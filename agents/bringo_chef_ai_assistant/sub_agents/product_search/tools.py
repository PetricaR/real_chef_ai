# product_search/tools.py
import logging
import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("product_search_tools")

# Configuration
MODEL = "gemini-2.0-flash"
PROJECT_ID = "formare-ai"
LOCATION = "europe-west4"
CONFIG = {
    'BRINGO_BASE_URL': "https://www.bringo.ro",
    'BRINGO_STORE': "carrefour_park_lake",
    'MAX_PRODUCTS_PER_SEARCH': 5,
    'REQUEST_TIMEOUT': 15,
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 1.0
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; BringoChef/1.0; +http://example.com/bot)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

# Shared AI client
try:
    from google import genai
    from google.genai import types
    
    gemini_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    logger.info("✅ Product search AI client initialized")
except Exception as e:
    logger.error(f"❌ AI client failed: {e}")
    gemini_client = None

def _call_ai(prompt: str) -> dict:
    """
    Robust AI call with intelligent error handling and response validation
    """
    if not gemini_client:
        logger.error("AI client unavailable")
        return {"error": "AI client unavailable", "fallback": True}
    
    try:
        response = gemini_client.models.generate_content(
            model=MODEL,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=0.3,  # Moderate creativity for search optimization
                max_output_tokens=1500,
                response_mime_type="application/json"
            )
        )
        
        # Robust JSON parsing - handle multiple response formats
        parsed_result = json.loads(response.text)
        
        # Handle array responses (sometimes AI returns [{}] instead of {})
        if isinstance(parsed_result, list):
            logger.warning(f"AI returned array instead of object, taking first element")
            if len(parsed_result) > 0 and isinstance(parsed_result[0], dict):
                return parsed_result[0]
            else:
                return {"error": "AI returned empty or invalid array", "fallback": True}
        
        # Handle object responses (expected format)
        if isinstance(parsed_result, dict):
            return parsed_result
        
        # Handle unexpected types
        logger.warning(f"AI returned unexpected type: {type(parsed_result)}")
        return {"error": f"Unexpected response type: {type(parsed_result)}", "fallback": True}
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        return {"error": f"Invalid JSON response: {str(e)}", "fallback": True}
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        return {"error": str(e), "fallback": True}

def _calculate_relevance(product_name: str, query: str) -> float:
    """Calculate intelligent relevance score between product and query"""
    product_lower = product_name.lower()
    query_lower = query.lower()
    
    # Exact match gets highest score
    if query_lower in product_lower:
        return 1.0
    
    # Word-based matching
    query_words = set(query_lower.split())
    product_words = set(product_lower.split())
    common_words = query_words.intersection(product_words)
    
    if not query_words:
        return 0.0
    
    # Calculate similarity ratio
    similarity = len(common_words) / len(query_words)
    
    # Boost for Romanian food terms
    romanian_food_terms = ['carne', 'paste', 'rosii', 'usturoi', 'ulei', 'branza']
    for term in romanian_food_terms:
        if term in product_lower and term in query_lower:
            similarity += 0.2
    
    return min(similarity, 1.0)

def _parse_products(html: str, query: str) -> list:
    """Parse Bringo search results with intelligent ranking"""
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    product_elements = soup.select('div.box-product')[:CONFIG['MAX_PRODUCTS_PER_SEARCH']]

    for elem in product_elements:
        try:
            name_link = elem.select_one('a.bringo-product-name')
            if not name_link or not name_link.get_text(strip=True):
                continue

            name = name_link.get_text(strip=True)
            url = urljoin(CONFIG['BRINGO_BASE_URL'], name_link['href'])
            
            price_elem = elem.select_one('div.bringo-product-price')
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price_match = re.search(r'(\d+[,.]\d+)', price_text.replace(' ', ''))
            price = float(price_match.group(1).replace(',', '.')) if price_match else 0.0
            
            if price == 0.0:
                continue

            available = 'out-of-stock' not in str(elem).lower()
            relevance = _calculate_relevance(name, query)

            products.append({
                "name": name,
                "price": price,
                "url": url,
                "available": available,
                "relevance_score": relevance
            })
            
        except Exception as e:
            logger.debug(f"Could not parse product element: {e}")
            continue
    
    # Sort by relevance first, then by price
    products.sort(key=lambda p: (-p['relevance_score'], p['price']))
    return products

def _search_bringo_products_with_retry(query: str) -> list:
    """Search Bringo.ro with intelligent retry logic"""
    search_url = f"{CONFIG['BRINGO_BASE_URL']}/ro/search/{CONFIG['BRINGO_STORE']}"
    params = {'criteria[search][value]': query}
    
    for attempt in range(CONFIG['MAX_RETRIES']):
        try:
            logger.info(f"🔍 Searching Bringo for '{query}' (attempt {attempt + 1})")
            response = requests.get(
                search_url, 
                params=params, 
                headers=HEADERS, 
                timeout=CONFIG['REQUEST_TIMEOUT']
            )
            
            if response.status_code == 200:
                products = _parse_products(response.text, query)
                if products:
                    logger.info(f"✅ Found {len(products)} products for '{query}'")
                    return products
                else:
                    logger.info(f"⚪ No products found for '{query}' on attempt {attempt + 1}")
            else:
                logger.warning(f"⚠️ Search failed with status {response.status_code}")
            
        except requests.exceptions.Timeout:
            logger.warning(f"⏰ Timeout on attempt {attempt + 1} for '{query}'")
        except requests.exceptions.RequestException as e:
            logger.warning(f"🌐 Network error on attempt {attempt + 1}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
        
        # Exponential backoff between retries
        if attempt < CONFIG['MAX_RETRIES'] - 1:
            delay = CONFIG['RETRY_DELAY'] * (2 ** attempt)
            logger.info(f"⏱️ Waiting {delay}s before retry...")
            import time
            time.sleep(delay)
    
    logger.warning(f"❌ All {CONFIG['MAX_RETRIES']} attempts failed for '{query}'")
    return []

def _generate_intelligent_search_strategy(ingredient: str) -> dict:
    """
    Use AI to generate intelligent search strategy for Romanian e-commerce
    """
    prompt = f"""
    You are an expert in Romanian e-commerce and food shopping. Analyze this ingredient for optimal Bringo.ro search strategy: "{ingredient}"

    Use your knowledge of:
    - Romanian language and food terminology
    - Online grocery shopping patterns in Romania
    - Seasonal ingredient availability
    - Common Romanian ingredient substitutions
    - E-commerce search optimization

    Create intelligent search strategy:

    {{
        "ingredient_analysis": {{
            "is_valid_ingredient": true|false,
            "romanian_name": "best Romanian name for this ingredient",
            "ingredient_category": "meat|dairy|vegetables|spices|pantry|etc",
            "confidence": 0.95,
            "reasoning": "explain your analysis of this ingredient"
        }},
        "search_optimization": {{
            "primary_search_term": "most effective search term for Romanian e-commerce",
            "alternative_terms": ["backup term 1", "backup term 2", "backup term 3"],
            "generic_categories": ["broader category if specific fails"],
            "brand_considerations": ["specific brands if relevant"],
            "reasoning": "explain your search term strategy"
        }},
        "market_intelligence": {{
            "availability_expectation": "high|medium|low",
            "typical_price_range_ron": "budget|5-15|15-30|30+",
            "seasonal_factors": "seasonal availability considerations",
            "common_packaging": "how typically sold in Romania",
            "shopping_tips": "specific advice for finding this ingredient"
        }},
        "fallback_strategy": {{
            "if_not_found_search_for": ["alternative ingredients to search"],
            "substitution_options": ["cooking substitutes if unavailable"],
            "related_products": ["related items that might work"],
            "reasoning": "explain fallback logic"
        }}
    }}

    Think like a Romanian home cook who knows where to find ingredients and how they're typically named in stores.
    """
    
    result = _call_ai(prompt)
    
    # Robust fallback if AI fails
    if result.get("error") or result.get("fallback"):
        logger.warning(f"AI search strategy failed for '{ingredient}', using intelligent fallback")
        return {
            "ingredient_analysis": {
                "is_valid_ingredient": True,
                "romanian_name": ingredient,
                "ingredient_category": "unknown",
                "confidence": 0.5,
                "reasoning": f"AI analysis failed: {result.get('error', 'Unknown error')}"
            },
            "search_optimization": {
                "primary_search_term": ingredient,
                "alternative_terms": [ingredient.lower(), ingredient.title()],
                "generic_categories": ["alimente"],
                "brand_considerations": [],
                "reasoning": "Using fallback search strategy due to AI failure"
            },
            "market_intelligence": {
                "availability_expectation": "medium",
                "typical_price_range_ron": "15-30",
                "seasonal_factors": "Unknown seasonal factors",
                "common_packaging": "Various packaging",
                "shopping_tips": "Search with multiple terms"
            },
            "fallback_strategy": {
                "if_not_found_search_for": [ingredient],
                "substitution_options": [],
                "related_products": [],
                "reasoning": "Basic fallback due to AI analysis failure"
            }
        }
    
    return result

def search_products_with_fallback(ingredient: str) -> str:
    """
    Intelligent product search with AI-driven strategy and robust fallback handling.
    This is the main function called by the agent.
    """
    logger.info(f"🚀 Starting intelligent search for '{ingredient}'")
    search_execution_log = []
    start_time = datetime.now()
    
    try:
        # Step 1: Generate AI-driven search strategy
        logger.info("🧠 Generating AI search strategy...")
        search_strategy = _generate_intelligent_search_strategy(ingredient)
        search_execution_log.append({
            "step": "AI Strategy Generation",
            "success": True,
            "strategy": search_strategy.get("search_optimization", {}),
            "timestamp": datetime.now().isoformat()
        })
        
        # Extract search terms from AI strategy
        search_optimization = search_strategy.get("search_optimization", {})
        primary_term = search_optimization.get("primary_search_term", ingredient)
        alternative_terms = search_optimization.get("alternative_terms", [])
        generic_terms = search_optimization.get("generic_categories", [])
        
        # Create comprehensive search term list
        all_search_terms = [primary_term] + alternative_terms + generic_terms
        unique_search_terms = []
        for term in all_search_terms:
            if term and term not in unique_search_terms:
                unique_search_terms.append(term)
        
        if not unique_search_terms:
            unique_search_terms = [ingredient]  # Ultimate fallback
        
        logger.info(f"📋 Search plan: {len(unique_search_terms)} terms to try")
        
        # Step 2: Execute intelligent search with fallback
        products_found = []
        successful_search_term = None
        
        for i, search_term in enumerate(unique_search_terms):
            logger.info(f"🔍 [{i+1}/{len(unique_search_terms)}] Searching for: '{search_term}'")
            
            try:
                products = _search_bringo_products_with_retry(search_term)
                search_execution_log.append({
                    "step": f"Search Attempt {i+1}",
                    "search_term": search_term,
                    "products_found": len(products),
                    "success": len(products) > 0,
                    "timestamp": datetime.now().isoformat()
                })
                
                if products:
                    products_found = products
                    successful_search_term = search_term
                    logger.info(f"✅ Success! Found {len(products)} products with '{search_term}'")
                    break
                else:
                    logger.info(f"⚪ No products found for '{search_term}', trying next term...")
                    
            except Exception as search_error:
                logger.error(f"❌ Search failed for '{search_term}': {search_error}")
                search_execution_log.append({
                    "step": f"Search Error {i+1}",
                    "search_term": search_term,
                    "error": str(search_error),
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                })
                continue
        
        # Step 3: Compile comprehensive results
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if products_found:
            result_status = "success"
            result_message = f"Found {len(products_found)} products for '{ingredient}' using search term '{successful_search_term}'"
            logger.info(f"🎉 Search successful in {execution_time:.1f}s")
        else:
            result_status = "no_products_found"
            result_message = f"Could not find products for '{ingredient}' after trying {len(unique_search_terms)} search strategies"
            logger.warning(f"😔 Search unsuccessful after {execution_time:.1f}s")
        
        # Compile final result with comprehensive information
        final_result = {
            "status": result_status,
            "original_ingredient": ingredient,
            "message": result_message,
            "execution_summary": {
                "total_search_terms_tried": len(unique_search_terms),
                "successful_search_term": successful_search_term,
                "execution_time_seconds": round(execution_time, 2),
                "ai_strategy_used": True
            },
            "products": products_found,
            "search_strategy": search_strategy,
            "search_execution_log": search_execution_log,
            "searched_at": datetime.now().isoformat()
        }
        
        logger.info(f"📊 Search completed: {result_status} for '{ingredient}'")
        return json.dumps(final_result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"💥 CRITICAL ERROR in search for '{ingredient}': {e}")
        
        # Never crash - always return valid response
        error_result = {
            "status": "system_error",
            "original_ingredient": ingredient,
            "message": f"Search system encountered an error: {str(e)}",
            "execution_summary": {
                "total_search_terms_tried": 0,
                "successful_search_term": None,
                "execution_time_seconds": round(execution_time, 2),
                "ai_strategy_used": False
            },
            "products": [],
            "search_strategy": {"error": str(e)},
            "search_execution_log": search_execution_log + [{
                "step": "Critical Error",
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }],
            "searched_at": datetime.now().isoformat()
        }
        
        return json.dumps(error_result, indent=2, ensure_ascii=False)