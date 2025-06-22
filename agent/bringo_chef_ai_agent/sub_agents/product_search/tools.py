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
    'REQUEST_TIMEOUT': 10
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
    """Simplified AI call"""
    if not gemini_client:
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
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        return {"error": str(e)}

def _calculate_relevance(product_name: str, query: str) -> float:
    """Calculate relevance score between product and query"""
    product_lower = product_name.lower()
    query_lower = query.lower()
    if query_lower in product_lower:
        return 1.0
    query_words = set(query_lower.split())
    product_words = set(product_lower.split())
    common_words = query_words.intersection(product_words)
    return len(common_words) / len(query_words) if query_words else 0.0

def _parse_products(html: str, query: str) -> list:
    """Parse Bringo search results"""
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

def _search_bringo_products(query: str) -> list:
    """Search Bringo.ro for products"""
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

def _validate_ingredient(ingredient: str) -> dict:
    """Validate ingredient and get search alternatives"""
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