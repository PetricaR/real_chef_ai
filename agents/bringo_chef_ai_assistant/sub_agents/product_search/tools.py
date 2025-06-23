# agents/bringo_chef_ai_assistant/sub_agents/product_search/tools.py
# Professional async product search tools for Bringo.ro with AI-driven search optimization
# Concurrent product search with intelligent Romanian term generation and fallback strategies

import asyncio
import aiohttp
import logging
import time
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from ...shared.client import get_ai_client
from ...shared.models import ProductInfo, ProductSearchResult, ProductSearchResponse
from ...shared.responses import create_success_response, create_error_response
from ...shared.config import settings

logger = logging.getLogger("product_search_tools")


class BringoSearchClient:
    """
    Professional async client for Bringo.ro product searches with intelligent optimization
    """
    
    def __init__(self):
        self.base_url = settings.bringo_base_url
        self.store = settings.bringo_store
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = asyncio.Semaphore(settings.max_concurrent_requests)
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=settings.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        
        self.session = aiohttp.ClientSession(
            headers=settings.request_headers,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_product(self, search_term: str, max_results: int = None) -> List[ProductInfo]:
        """
        Search for products on Bringo.ro with professional error handling
        
        Args:
            search_term: Romanian search term
            max_results: Maximum products to return
            
        Returns:
            List of ProductInfo objects
        """
        if not self.session:
            raise RuntimeError("Session not initialized - use async context manager")
        
        max_results = max_results or settings.max_products_per_search
        
        async with self.rate_limiter:
            try:
                search_url = f"{self.base_url}/ro/search/{self.store}"
                params = {'criteria[search][value]': search_term}
                
                logger.info(f"🔍 Searching Bringo.ro for: '{search_term}'")
                
                async with self.session.get(search_url, params=params) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ Search failed with status {response.status} for '{search_term}'")
                        return []
                    
                    html_content = await response.text()
                    products = await self._parse_products(html_content, search_term, max_results)
                    
                    logger.info(f"✅ Found {len(products)} products for '{search_term}'")
                    return products
                    
            except asyncio.TimeoutError:
                logger.error(f"❌ Search timeout for '{search_term}'")
                return []
            except Exception as e:
                logger.error(f"❌ Search error for '{search_term}': {e}")
                return []
    
    async def _parse_products(self, html: str, search_term: str, max_results: int) -> List[ProductInfo]:
        """Parse Bringo product results from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            products = []
            product_elements = soup.select('div.box-product')[:max_results]
            
            for elem in product_elements:
                try:
                    product = await self._extract_product_info(elem, search_term)
                    if product and product.price > 0:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Could not parse product element: {e}")
                    continue
            
            # Sort by relevance and price
            products.sort(key=lambda p: (-p.relevance_score, p.price))
            return products
            
        except Exception as e:
            logger.error(f"❌ HTML parsing failed for '{search_term}': {e}")
            return []
    
    async def _extract_product_info(self, elem, search_term: str) -> Optional[ProductInfo]:
        """Extract product information from HTML element"""
        try:
            # Extract product name and URL
            name_link = elem.select_one('a.bringo-product-name')
            if not name_link or not name_link.get_text(strip=True):
                return None
            
            name = name_link.get_text(strip=True)
            url = urljoin(self.base_url, name_link['href'])
            
            # Extract price
            price_elem = elem.select_one('div.bringo-product-price')
            if not price_elem:
                return None
            
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r'(\d+[,.]\d+)', price_text.replace(' ', ''))
            
            if not price_match:
                return None
            
            price = float(price_match.group(1).replace(',', '.'))
            
            # Check availability
            available = 'out-of-stock' not in str(elem).lower()
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance(name, search_term)
            
            # Extract package size if available
            package_size = self._extract_package_size(name)
            
            return ProductInfo(
                name=name,
                price=price,
                url=url,
                available=available,
                relevance_score=relevance_score,
                package_size=package_size
            )
            
        except Exception as e:
            logger.debug(f"Product extraction failed: {e}")
            return None
    
    def _calculate_relevance(self, product_name: str, search_term: str) -> float:
        """Calculate relevance score between product and search term"""
        product_lower = product_name.lower()
        search_lower = search_term.lower()
        
        # Exact match gets highest score
        if search_lower in product_lower:
            return 1.0
        
        # Word overlap scoring
        search_words = set(search_lower.split())
        product_words = set(product_lower.split())
        common_words = search_words.intersection(product_words)
        
        if not search_words:
            return 0.0
        
        base_score = len(common_words) / len(search_words)
        
        # Bonus for product name starting with search term
        if product_lower.startswith(search_lower):
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _extract_package_size(self, product_name: str) -> Optional[str]:
        """Extract package size information from product name"""
        size_patterns = [
            r'(\d+(?:[,.]\d+)?\s*(?:kg|g|l|ml|buc|bucăți))',
            r'(\d+\s*x\s*\d+(?:[,.]\d+)?\s*(?:g|ml))'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None


async def search_products_for_ingredients(ingredient_validation_json: str) -> str:
    """
    Search for products for all validated ingredients using concurrent processing.
    
    Args:
        ingredient_validation_json: JSON string containing ingredient validation results
        
    Returns:
        JSON string containing comprehensive product search results
    """
    start_time = time.time()
    logger.info("🛒 Starting comprehensive product search for all ingredients...")
    
    try:
        # Parse ingredient validation data
        validation_data = json.loads(ingredient_validation_json)
        
        if validation_data.get("status") not in ["success", "warning"]:
            raise Exception("Invalid ingredient validation data")
        
        # Extract ingredients from validation results
        ingredients_to_search = await _extract_search_ingredients(validation_data)
        
        if not ingredients_to_search:
            raise Exception("No valid ingredients found for product search")
        
        logger.info(f"🔍 Searching for {len(ingredients_to_search)} ingredients")
        
        # Execute concurrent product searches
        search_results = await _execute_concurrent_searches(ingredients_to_search)
        
        # Analyze and optimize results
        analysis = await _analyze_search_results(search_results, validation_data)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Product search completed in {processing_time}ms")
        logger.info(f"📊 Found products for {analysis['successful_searches']}/{len(ingredients_to_search)} ingredients")
        logger.info(f"💰 Total estimated cost: {analysis['total_estimated_cost_ron']} RON")
        
        # Create successful response
        response = ProductSearchResponse(
            status="success",
            message=f"Found products for {analysis['successful_searches']} ingredients",
            agent_name="product_search_agent",
            processing_time_ms=processing_time,
            confidence_score=analysis['success_rate'],
            data=search_results,
            total_searches=len(ingredients_to_search),
            successful_searches=analysis['successful_searches'],
            total_products_found=analysis['total_products_found']
        )
        
        # Add analysis data
        response_dict = response.dict()
        response_dict["shopping_analysis"] = analysis
        
        return json.dumps(response_dict, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Product search failed: {e}")
        
        error_response = ProductSearchResponse(
            status="error",
            message=f"Product search failed: {str(e)}",
            agent_name="product_search_agent",
            processing_time_ms=processing_time,
            total_searches=0,
            successful_searches=0,
            total_products_found=0
        )
        
        return error_response.model_dump_json(indent=2)


async def optimize_product_selection(search_results_json: str, budget_ron: float = 100.0) -> str:
    """
    Optimize product selection for best value within budget constraints.
    
    Args:
        search_results_json: Product search results
        budget_ron: Budget constraint in Romanian Lei
        
    Returns:
        JSON string containing optimized product recommendations
    """
    start_time = time.time()
    logger.info(f"💡 Optimizing product selection for {budget_ron} RON budget...")
    
    try:
        search_data = json.loads(search_results_json)
        
        if search_data.get("status") != "success":
            raise Exception("Invalid search results for optimization")
        
        search_results = search_data.get("data", [])
        
        # Generate optimization prompt for AI
        optimization_prompt = f"""
        Optimize product selection for best value within {budget_ron} RON budget:
        
        Search Results: {json.dumps(search_results[:10], indent=2)}  # Truncate for prompt size
        
        As a shopping optimization specialist, provide recommendations for:
        
        1. **Budget Optimization**:
           - Select best value products within budget
           - Identify cost-saving opportunities
           - Suggest quantity adjustments if needed
           - Prioritize essential vs. optional ingredients
        
        2. **Quality Assessment**:
           - Evaluate price-to-quality ratio for each product
           - Identify premium vs. budget options
           - Recommend brand preferences for Romanian market
           - Assess packaging efficiency
        
        3. **Shopping Strategy**:
           - Suggest optimal shopping sequence
           - Identify bulk buying opportunities
           - Recommend seasonal timing for purchases
           - Provide Romanian market shopping tips
        
        Return optimization recommendations:
        {{
            "optimized_selections": [
                {{
                    "ingredient": "ingredient_name",
                    "recommended_product": "best_value_product",
                    "reasoning": "why_this_product_chosen",
                    "cost_savings": "potential_savings_vs_alternatives",
                    "quality_assessment": "quality_rating_explanation"
                }}
            ],
            "budget_analysis": {{
                "optimized_total_cost_ron": optimized_total,
                "savings_achieved_ron": amount_saved,
                "budget_utilization_percentage": percentage_used,
                "remaining_budget_ron": remaining_amount
            }},
            "shopping_strategy": {{
                "recommended_shopping_order": ["ingredient_purchase_sequence"],
                "bulk_buying_opportunities": ["bulk_purchase_recommendations"],
                "timing_recommendations": "best_time_to_shop",
                "store_recommendations": "best_romanian_stores_or_sections"
            }}
        }}
        """
        
        # Use AI for optimization analysis
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=optimization_prompt,
            temperature=settings.conservative_temperature,
            agent_name="product_search_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        optimization_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Product optimization completed in {processing_time}ms")
        
        # Create optimization response
        response_obj = {
            "status": "success",
            "message": "Product selection optimized successfully",
            "agent_name": "product_search_agent",
            "processing_time_ms": processing_time,
            "optimization_data": optimization_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response_obj, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Product optimization failed: {e}")
        
        error_response = {
            "status": "error",
            "message": f"Product optimization failed: {str(e)}",
            "agent_name": "product_search_agent",
            "processing_time_ms": processing_time
        }
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)


async def generate_shopping_strategy(optimized_products_json: str) -> str:
    """
    Generate comprehensive shopping strategy for Romanian market.
    
    Args:
        optimized_products_json: Optimized product selection results
        
    Returns:
        JSON string containing shopping strategy recommendations
    """
    start_time = time.time()
    logger.info("📋 Generating comprehensive shopping strategy...")
    
    try:
        products_data = json.loads(optimized_products_json)
        
        if products_data.get("status") != "success":
            raise Exception("Invalid optimized products data")
        
        # Generate shopping strategy using AI
        strategy_prompt = f"""
        Generate comprehensive shopping strategy for Romanian consumers:
        
        Optimized Products: {json.dumps(products_data.get('optimization_data', {}), indent=2)}
        
        As a Romanian market shopping specialist, provide detailed guidance covering:
        
        1. **Shopping Route Optimization**:
           - Optimal shopping sequence within Romanian supermarkets
           - Best sections/aisles to visit for efficiency
           - Peak vs. off-peak shopping timing recommendations
           - Multi-store shopping strategy if beneficial
        
        2. **Romanian Market Intelligence**:
           - Best Romanian supermarket chains for these ingredients
           - Local brand recommendations vs. international brands
           - Seasonal pricing patterns and optimal purchase timing
           - Regional availability considerations
        
        3. **Cost-Saving Strategies**:
           - Discount and promotion timing for common ingredients
           - Bulk buying recommendations with storage considerations
           - Generic vs. brand name value assessments
           - Membership and loyalty program benefits
        
        4. **Practical Shopping Tips**:
           - Ingredient freshness indicators and selection tips
           - Storage and preservation recommendations
           - Substitution strategies for unavailable items
           - Quantity adjustment guidelines for different serving sizes
        
        Return comprehensive shopping strategy:
        {{
            "shopping_route": {{
                "recommended_stores": ["best_romanian_supermarket_chains"],
                "shopping_sequence": ["optimal_ingredient_collection_order"],
                "timing_recommendations": "best_days_and_times_to_shop",
                "estimated_shopping_time": "total_time_needed"
            }},
            "romanian_market_tips": {{
                "local_brand_preferences": ["recommended_romanian_brands"],
                "seasonal_considerations": "seasonal_pricing_and_availability",
                "regional_variations": "geographic_availability_differences",
                "cultural_shopping_patterns": "romanian_consumer_preferences"
            }},
            "cost_optimization": {{
                "discount_strategies": ["how_to_find_best_deals"],
                "bulk_buying_guide": ["what_to_buy_in_bulk_and_storage"],
                "price_comparison_tips": ["how_to_compare_prices_effectively"],
                "loyalty_program_benefits": ["best_programs_for_food_shopping"]
            }},
            "practical_guidance": {{
                "freshness_selection": ["how_to_choose_quality_ingredients"],
                "storage_recommendations": ["proper_storage_for_each_ingredient"],
                "substitution_strategies": ["alternatives_if_items_unavailable"],
                "quantity_scaling": ["how_to_adjust_for_different_serving_sizes"]
            }}
        }}
        """
        
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=strategy_prompt,
            temperature=settings.balanced_temperature,
            agent_name="product_search_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        strategy_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Shopping strategy generated in {processing_time}ms")
        
        # Create strategy response
        response_obj = {
            "status": "success",
            "message": "Shopping strategy generated successfully",
            "agent_name": "product_search_agent",
            "processing_time_ms": processing_time,
            "shopping_strategy": strategy_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response_obj, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Shopping strategy generation failed: {e}")
        
        error_response = {
            "status": "error",
            "message": f"Shopping strategy generation failed: {str(e)}",
            "agent_name": "product_search_agent",
            "processing_time_ms": processing_time
        }
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)


async def _extract_search_ingredients(validation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract ingredients for search from validation data"""
    ingredients = []
    
    # Check for automatic selection data
    if "automatic_selection_data" in validation_data:
        selection_data = validation_data["automatic_selection_data"]
        auto_ingredients = selection_data.get("automatic_ingredient_selection", {}).get("selected_ingredients", [])
        
        for ingredient in auto_ingredients:
            ingredients.append({
                "name": ingredient.get("name", ""),
                "romanian_name": ingredient.get("romanian_name", ""),
                "importance": ingredient.get("importance", "important"),
                "estimated_cost": ingredient.get("estimated_cost_ron", 0)
            })
    
    # Also check for validation data
    if "data" in validation_data:
        validation_list = validation_data["data"]
        if isinstance(validation_list, list):
            for validation in validation_list:
                ingredients.append({
                    "name": validation.get("ingredient", ""),
                    "romanian_name": validation.get("romanian_name", ""),
                    "importance": "important",
                    "estimated_cost": validation.get("estimated_cost_ron", 0)
                })
    
    return ingredients


async def _execute_concurrent_searches(ingredients: List[Dict[str, Any]]) -> List[ProductSearchResult]:
    """Execute concurrent product searches for all ingredients"""
    search_results = []
    
    async with BringoSearchClient() as client:
        # Create search tasks
        search_tasks = []
        for ingredient in ingredients:
            task = _search_single_ingredient(client, ingredient)
            search_tasks.append(task)
        
        # Execute searches concurrently
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Search failed for {ingredients[i]['name']}: {result}")
                # Create empty result for failed search
                search_results.append(ProductSearchResult(
                    ingredient=ingredients[i]['name'],
                    search_terms_used=[ingredients[i]['romanian_name']],
                    products_found=[],
                    best_recommendation=None,
                    total_found=0,
                    search_success=False
                ))
            else:
                search_results.append(result)
    
    return search_results


async def _search_single_ingredient(client: BringoSearchClient, ingredient: Dict[str, Any]) -> ProductSearchResult:
    """Search for a single ingredient with fallback strategies"""
    ingredient_name = ingredient["name"]
    romanian_name = ingredient["romanian_name"]
    
    # Generate search terms with AI assistance
    search_terms = await _generate_search_terms(ingredient_name, romanian_name)
    
    all_products = []
    successful_terms = []
    
    # Try each search term until we find products
    for term in search_terms:
        try:
            products = await client.search_product(term)
            if products:
                all_products.extend(products)
                successful_terms.append(term)
                
                # If we found enough products, break
                if len(all_products) >= settings.max_products_per_search:
                    break
                    
        except Exception as e:
            logger.warning(f"⚠️ Search term '{term}' failed for {ingredient_name}: {e}")
            continue
    
    # Remove duplicates and sort by relevance
    unique_products = _deduplicate_products(all_products)
    unique_products.sort(key=lambda p: (-p.relevance_score, p.price))
    
    # Select best recommendation
    best_product = unique_products[0] if unique_products else None
    
    return ProductSearchResult(
        ingredient=ingredient_name,
        search_terms_used=successful_terms,
        products_found=unique_products[:settings.max_products_per_search],
        best_recommendation=best_product,
        total_found=len(unique_products),
        search_success=len(unique_products) > 0
    )


async def _generate_search_terms(english_name: str, romanian_name: str) -> List[str]:
    """Generate optimized Romanian search terms using AI"""
    search_terms = [romanian_name] if romanian_name else []
    
    # Add the English name as fallback
    if english_name and english_name.lower() != romanian_name.lower():
        search_terms.append(english_name)
    
    # Generate additional terms using AI
    try:
        client = await get_ai_client()
        
        prompt = f"""
        Generate optimized Romanian search terms for finding "{english_name}" (Romanian: "{romanian_name}") on Romanian e-commerce sites.
        
        Return 3-5 alternative Romanian search terms that would help find this ingredient:
        {{
            "additional_terms": ["term1", "term2", "term3"]
        }}
        
        Consider:
        - Regional Romanian variations
        - Common misspellings or alternate spellings
        - Category terms (e.g., "condimente" for spices)
        - Brand names if relevant
        """
        
        response = await client.generate_text(
            prompt=prompt,
            temperature=settings.conservative_temperature,
            agent_name="product_search_agent"
        )
        
        if not response.get("error"):
            ai_terms = json.loads(response.get("content", "{}"))
            additional_terms = ai_terms.get("additional_terms", [])
            search_terms.extend(additional_terms)
            
    except Exception as e:
        logger.warning(f"⚠️ AI search term generation failed: {e}")
    
    # Remove duplicates while preserving order
    unique_terms = []
    seen = set()
    for term in search_terms:
        if term and term.lower() not in seen:
            unique_terms.append(term)
            seen.add(term.lower())
    
    return unique_terms[:5]  # Limit to 5 terms max


def _deduplicate_products(products: List[ProductInfo]) -> List[ProductInfo]:
    """Remove duplicate products based on name and price"""
    unique_products = []
    seen = set()
    
    for product in products:
        # Create a key based on name and price
        key = (product.name.lower().strip(), round(product.price, 2))
        
        if key not in seen:
            unique_products.append(product)
            seen.add(key)
    
    return unique_products


async def _analyze_search_results(search_results: List[ProductSearchResult], validation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze search results and provide insights"""
    successful_searches = sum(1 for result in search_results if result.search_success)
    total_products_found = sum(result.total_found for result in search_results)
    
    # Calculate total estimated cost
    total_cost = 0.0
    for result in search_results:
        if result.best_recommendation:
            total_cost += result.best_recommendation.price
    
    success_rate = successful_searches / len(search_results) if search_results else 0
    
    # Determine budget compliance
    budget_info = validation_data.get("automatic_selection_data", {}).get("budget_analysis", {})
    expected_budget = budget_info.get("total_estimated_cost", 100.0)
    
    if total_cost <= expected_budget:
        budget_compliance = "within_budget"
    elif total_cost <= expected_budget * 1.2:
        budget_compliance = "slightly_over"
    else:
        budget_compliance = "significantly_over"
    
    return {
        "successful_searches": successful_searches,
        "total_products_found": total_products_found,
        "total_estimated_cost_ron": round(total_cost, 2),
        "success_rate": round(success_rate, 2),
        "budget_compliance": budget_compliance,
        "average_products_per_ingredient": total_products_found / len(search_results) if search_results else 0
    }