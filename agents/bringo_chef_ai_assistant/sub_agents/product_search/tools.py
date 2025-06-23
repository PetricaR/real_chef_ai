# product_search/tools.py
import logging
import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("product_search_tools")

# Configuration
MODEL = "gemini-2.0-flash"
PROJECT_ID = "formare-ai"
LOCATION = "europe-west4"
GCP_CREDENTIALS_SECRET_NAME = "gcp-credentials"

CONFIG = {
    'BRINGO_BASE_URL': "https://www.bringo.ro",
    'BRINGO_STORE': "carrefour_park_lake",
    'MAX_PRODUCTS_PER_SEARCH': 5,
    'REQUEST_TIMEOUT': 10
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; BringoChef/1.0; +http://example.com/bot)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

def get_secret_from_manager(secret_name: str, project_id: str = PROJECT_ID) -> Optional[str]:
    """
    Retrieve a secret from Google Cloud Secret Manager.
    
    Args:
        secret_name (str): Name of the secret to retrieve
        project_id (str): GCP project ID
        
    Returns:
        Optional[str]: Secret value if successful, None if failed
        
    Raises:
        Exception: If secret manager client initialization or secret retrieval fails
    """
    try:
        from google.cloud import secretmanager
        
        # Initialize the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()
        
        # Build the secret version name
        secret_version_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        # Access the secret version
        response = client.access_secret_version(name=secret_version_name)
        secret_value = response.payload.data.decode('UTF-8')
        
        logger.info(f"✅ Successfully retrieved secret: {secret_name}")
        return secret_value
        
    except ImportError as e:
        logger.error(f"❌ Google Cloud Secret Manager library not available: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to retrieve secret '{secret_name}': {e}")
        return None

def initialize_gcp_credentials() -> Optional[Dict[str, Any]]:
    """
    Initialize GCP credentials from Secret Manager.
    
    Returns:
        Optional[Dict[str, Any]]: Parsed credentials JSON if successful, None if failed
    """
    try:
        # Retrieve GCP credentials from Secret Manager
        credentials_json = get_secret_from_manager(GCP_CREDENTIALS_SECRET_NAME)
        
        if not credentials_json:
            logger.error("❌ Failed to retrieve GCP credentials from Secret Manager")
            return None
            
        # Parse the JSON credentials
        credentials = json.loads(credentials_json)
        logger.info("✅ GCP credentials initialized successfully from Secret Manager")
        return credentials
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in GCP credentials secret: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ GCP credentials initialization failed: {e}")
        return None

def setup_gemini_client(credentials: Optional[Dict[str, Any]] = None):
    """
    Initialize the Gemini AI client with proper credentials.
    
    Args:
        credentials (Optional[Dict[str, Any]]): GCP credentials dict, 
                                               if None will attempt to load from Secret Manager
                                               
    Returns:
        genai.Client or None: Initialized client or None if failed
    """
    try:
        from google import genai
        from google.genai import types
        
        # Get credentials if not provided
        if credentials is None:
            credentials = initialize_gcp_credentials()
            
        if credentials is None:
            logger.warning("⚠️ No credentials available, attempting default authentication")
        
        # Initialize the Gemini client
        # If using service account key from Secret Manager, you might need to set up authentication
        # For now, using the existing vertex AI authentication method
        gemini_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION
        )
        
        logger.info("✅ Product search AI client initialized successfully")
        return gemini_client
        
    except ImportError as e:
        logger.error(f"❌ Google GenAI library not available: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Gemini client initialization failed: {e}")
        return None

# Initialize credentials and AI client
gcp_credentials = initialize_gcp_credentials()
gemini_client = setup_gemini_client(gcp_credentials)

def _call_ai(prompt: str) -> Dict[str, Any]:
    """
    Simplified AI call with proper error handling.
    
    Args:
        prompt (str): The prompt to send to the AI model
        
    Returns:
        Dict[str, Any]: AI response as dictionary or error information
    """
    if not gemini_client:
        logger.error("❌ AI client unavailable")
        return {"error": "AI client unavailable"}
    
    try:
        response = gemini_client.models.generate_content(
            model=MODEL,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1000,
                response_mime_type="application/json"
            )
        )
        
        # Parse and return the response
        result = json.loads(response.text)
        logger.info("✅ AI call completed successfully")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse AI response as JSON: {e}")
        return {"error": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        logger.error(f"❌ AI call failed: {e}")
        return {"error": str(e)}

def _calculate_relevance(product_name: str, query: str) -> float:
    """
    Calculate relevance score between product and query.
    
    Args:
        product_name (str): Name of the product
        query (str): Search query
        
    Returns:
        float: Relevance score between 0.0 and 1.0
    """
    product_lower = product_name.lower()
    query_lower = query.lower()
    if query_lower in product_lower:
        return 1.0
    query_words = set(query_lower.split())
    product_words = set(product_lower.split())
    common_words = query_words.intersection(product_words)
    return len(common_words) / len(query_words) if query_words else 0.0

def _parse_products(html: str, query: str) -> List[Dict[str, Any]]:
    """
    Parse Bringo search results from HTML.
    
    Args:
        html (str): HTML content from Bringo search page
        query (str): Original search query for relevance scoring
        
    Returns:
        List[Dict[str, Any]]: List of parsed product dictionaries
    """
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
            
    products.sort(key=lambda p: (-p['relevance_score'], p['price']))
    return products

def _search_bringo_products(query: str) -> List[Dict[str, Any]]:
    """
    Search Bringo.ro for products.
    
    Args:
        query (str): Search query
        
    Returns:
        List[Dict[str, Any]]: List of found products
    """
    search_url = f"{CONFIG['BRINGO_BASE_URL']}/ro/search/{CONFIG['BRINGO_STORE']}"
    params = {'criteria[search][value]': query}
    try:
        response = requests.get(search_url, params=params, headers=HEADERS, timeout=CONFIG['REQUEST_TIMEOUT'])
        if response.status_code == 200:
            return _parse_products(response.text, query)
        else:
            logger.warning(f"Search failed with status: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Search error for '{query}': {e}")
        return []

def _validate_ingredient(ingredient: str) -> Dict[str, Any]:
    """
    Validate ingredient and get search alternatives using AI.
    
    Args:
        ingredient (str): Ingredient name to validate
        
    Returns:
        Dict[str, Any]: Validation results with alternatives and substitutes
    """
    prompt = f"""
    Validate if "{ingredient}" is a real, edible ingredient available in Romanian supermarkets.
    
    Return JSON:
    {{
        "is_valid": true|false,
        "corrected_name": "best Romanian name for this ingredient",
        "search_terms": ["alternative search term 1", "alternative search term 2"],
        "substitutes": ["substitute 1", "substitute 2"],
        "validation_notes": "brief explanation"
    }}
    """
    
    result = _call_ai(prompt)
    if "error" in result:
        return {
            "is_valid": True,  # Assume valid if AI fails
            "corrected_name": ingredient,
            "search_terms": [ingredient],
            "substitutes": [],
            "validation_notes": f"AI validation failed: {result['error']}"
        }
    return result

def search_products_with_fallback(ingredient: str) -> str:
    """
    Search for products with intelligent validation and automatic fallback.
    
    Args:
        ingredient (str): Ingredient name to search for
        
    Returns:
        str: JSON string containing search results with fallback history
    """
    logger.info(f"🚀 Starting enhanced search for '{ingredient}'")
    search_history = []
    
    # Step 1: Validate ingredient
    validation_result = _validate_ingredient(ingredient)
    search_history.append({"step": "Validation", "details": validation_result})

    if not validation_result.get("is_valid"):
        logger.warning(f"Ingredient '{ingredient}' is not valid. Using substitutes.")
        search_terms_to_try = validation_result.get("substitutes", [ingredient])
    else:
        search_terms_to_try = [validation_result.get("corrected_name", ingredient)]
        search_terms_to_try.extend(validation_result.get("search_terms", []))
        search_terms_to_try.extend(validation_result.get("substitutes", []))

    # Remove duplicates while preserving order
    unique_search_terms = list(dict.fromkeys(search_terms_to_try))
    
    # Step 2: Search with fallback
    products_found = []
    for term in unique_search_terms:
        if not term:
            continue
        logger.info(f"-> Trying search term: '{term}'")
        products = _search_bringo_products(term)
        search_history.append({"step": "Search", "term": term, "products_found": len(products)})
        if products:
            logger.info(f"✅ Found {len(products)} products for '{term}'")
            products_found = products
            break
        else:
            logger.info(f"-> No products found for '{term}'. Trying next term.")
            
    # Step 3: Compile results
    if products_found:
        final_status = "success"
        message = f"Successfully found products for '{ingredient}'"
    else:
        final_status = "no_products_found"
        message = f"Could not find any products for '{ingredient}' after trying all alternatives"
        
    final_result = {
        "status": final_status,
        "original_ingredient": ingredient,
        "message": message,
        "search_history": search_history,
        "products": products_found,
        "validation": validation_result,
        "searched_at": datetime.now().isoformat()
    }
    
    return json.dumps(final_result, indent=2, ensure_ascii=False)

def batch_search_ingredients(ingredients_list: List[str]) -> str:
    """
    Search for multiple ingredients in batch with optimized performance.
    
    Args:
        ingredients_list (List[str]): List of ingredient names to search for
        
    Returns:
        str: JSON string containing batch search results
    """
    logger.info(f"🔍 Starting batch search for {len(ingredients_list)} ingredients")
    
    batch_results = {
        "status": "success",
        "total_ingredients": len(ingredients_list),
        "results": {},
        "summary": {
            "successful_searches": 0,
            "failed_searches": 0,
            "total_products_found": 0
        },
        "searched_at": datetime.now().isoformat()
    }
    
    for ingredient in ingredients_list:
        if not ingredient or not ingredient.strip():
            continue
            
        ingredient = ingredient.strip()
        logger.info(f"🔎 Searching for ingredient: {ingredient}")
        
        try:
            search_result_json = search_products_with_fallback(ingredient)
            search_result = json.loads(search_result_json)
            
            batch_results["results"][ingredient] = search_result
            
            if search_result.get("status") == "success":
                batch_results["summary"]["successful_searches"] += 1
                batch_results["summary"]["total_products_found"] += len(search_result.get("products", []))
            else:
                batch_results["summary"]["failed_searches"] += 1
                
        except Exception as e:
            logger.error(f"❌ Batch search failed for '{ingredient}': {e}")
            batch_results["results"][ingredient] = {
                "status": "error",
                "message": str(e),
                "original_ingredient": ingredient
            }
            batch_results["summary"]["failed_searches"] += 1
    
    logger.info(f"✅ Batch search completed: {batch_results['summary']['successful_searches']}/{len(ingredients_list)} successful")
    return json.dumps(batch_results, indent=2, ensure_ascii=False)

def analyze_price_trends(ingredient: str, historical_searches: str = "") -> str:
    """
    Analyze price trends for an ingredient using AI analysis.
    
    Args:
        ingredient (str): Ingredient name to analyze
        historical_searches (str): JSON string of previous search results
        
    Returns:
        str: JSON string containing price trend analysis
    """
    logger.info(f"📊 Analyzing price trends for '{ingredient}'")
    
    # Get current prices
    current_search = search_products_with_fallback(ingredient)
    
    try:
        current_data = json.loads(current_search)
        historical_data = json.loads(historical_searches) if historical_searches else {}
    except json.JSONDecodeError:
        logger.warning("⚠️ Invalid historical data JSON")
        historical_data = {}
    
    # Extract current prices
    current_products = current_data.get("products", [])
    current_prices = [p["price"] for p in current_products if p.get("available", True)]
    
    prompt = f"""
    Analyze price trends for ingredient "{ingredient}":
    
    Current search results: {json.dumps(current_products[:3], indent=2)}
    Historical data: {json.dumps(historical_data, indent=2)}
    
    Return JSON:
    {{
        "price_analysis": {{
            "current_avg_price": average_current_price,
            "current_min_price": minimum_current_price,
            "current_max_price": maximum_current_price,
            "price_range_ron": "X.XX - Y.YY RON"
        }},
        "market_insights": {{
            "availability": "excellent|good|limited|poor",
            "price_competitiveness": "very_competitive|competitive|moderate|expensive",
            "value_recommendation": "best value product recommendation",
            "shopping_strategy": "when and how to buy for best price"
        }},
        "trend_predictions": {{
            "seasonal_factors": "factors affecting price seasonally",
            "buying_recommendation": "buy_now|wait|stock_up",
            "price_forecast": "expected price direction"
        }}
    }}
    """
    
    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])
            
        logger.info("✅ Price trend analysis successful")
        return json.dumps({
            "status": "success",
            "ingredient": ingredient,
            "current_search": current_data,
            "price_trends": result,
            "analyzed_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Price trend analysis failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "current_search": current_data
        })

# Health check function to verify all components are working
def health_check() -> Dict[str, Any]:
    """
    Perform a health check on all product search components.
    
    Returns:
        Dict[str, Any]: Health status of all components
    """
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "service": "product_search",
        "components": {}
    }
    
    # Check Secret Manager connectivity
    try:
        test_credentials = initialize_gcp_credentials()
        health_status["components"]["secret_manager"] = {
            "status": "healthy" if test_credentials else "degraded",
            "credentials_loaded": test_credentials is not None
        }
    except Exception as e:
        health_status["components"]["secret_manager"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Gemini client
    health_status["components"]["gemini_client"] = {
        "status": "healthy" if gemini_client else "unhealthy",
        "initialized": gemini_client is not None
    }
    
    # Test Bringo connectivity
    try:
        test_response = requests.get(CONFIG['BRINGO_BASE_URL'], headers=HEADERS, timeout=5)
        bringo_status = "healthy" if test_response.status_code == 200 else "degraded"
    except Exception:
        bringo_status = "unhealthy"
    
    health_status["components"]["bringo_connectivity"] = {
        "status": bringo_status,
        "base_url": CONFIG['BRINGO_BASE_URL']
    }
    
    # Test a simple product search
    try:
        test_search = _search_bringo_products("oua")  # Search for eggs
        search_test_status = "healthy" if len(test_search) > 0 else "degraded"
    except Exception:
        search_test_status = "unhealthy"
    
    health_status["components"]["product_search"] = {
        "status": search_test_status
    }
    
    # Test AI ingredient validation
    try:
        test_validation = _validate_ingredient("rosii")  # Validate tomatoes
        ai_test_status = "healthy" if "error" not in test_validation else "degraded"
    except Exception:
        ai_test_status = "unhealthy"
    
    health_status["components"]["ai_validation"] = {
        "status": ai_test_status
    }
    
    # Overall system health
    component_statuses = [comp["status"] for comp in health_status["components"].values()]
    if all(status == "healthy" for status in component_statuses):
        health_status["overall_status"] = "healthy"
    elif any(status == "healthy" for status in component_statuses):
        health_status["overall_status"] = "degraded"
    else:
        health_status["overall_status"] = "unhealthy"
    
    logger.info(f"🏥 Product search health check completed: {health_status['overall_status']}")
    return health_status

def get_product_search_summary(ingredients_list: List[str]) -> str:
    """
    Get comprehensive product search summary for multiple ingredients.
    
    Args:
        ingredients_list (List[str]): List of ingredients to search for
        
    Returns:
        str: JSON string containing comprehensive search analysis
    """
    logger.info(f"📋 Generating product search summary for {len(ingredients_list)} ingredients...")
    
    try:
        # Run batch search
        batch_result = batch_search_ingredients(ingredients_list)
        batch_data = json.loads(batch_result)
        
        # Analyze the results
        prompt = f"""
        Analyze this batch product search results: {json.dumps(batch_data['summary'], indent=2)}
        
        Create a summary with recommendations:
        
        Return JSON:
        {{
            "search_summary": {{
                "total_ingredients_searched": {len(ingredients_list)},
                "successful_searches": number,
                "total_products_found": number,
                "average_products_per_ingredient": number
            }},
            "cost_analysis": {{
                "estimated_total_cost": "estimated total for all ingredients",
                "budget_breakdown": "cost analysis",
                "value_recommendations": ["how to optimize costs"]
            }},
            "shopping_strategy": {{
                "recommended_store": "best store option",
                "shopping_tips": ["practical shopping advice"],
                "availability_concerns": ["any availability issues"]
            }},
            "alternatives_needed": [
                {{
                    "ingredient": "ingredient name",
                    "issue": "why alternative needed",
                    "recommendation": "suggested alternative"
                }}
            ]
        }}
        """
        
        analysis_result = _call_ai(prompt)
        
        # Combine results
        combined_summary = {
            "status": "success",
            "ingredients_analyzed": ingredients_list,
            "detailed_search_results": batch_data,
            "intelligent_analysis": analysis_result if "error" not in analysis_result else {},
            "summary_generated_at": datetime.now().isoformat()
        }
        
        logger.info("✅ Product search summary generated successfully")
        return json.dumps(combined_summary, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Product search summary failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "partial_results": "Individual search functions may still work"
        })