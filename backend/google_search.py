# google_search.py
import os
import logging
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - GoogleSearch - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("google_search.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GoogleSearch")

# Google Custom Search API credentials
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")


def google_partselect_search(query: str, num_results: int = 5):
    """
    Performs a Google Custom Search restricted to PartSelect.com
    
    Args:
        query: Search query string
        num_results: Number of results to return (default: 5, max: 10)
    
    Returns:
        List of tuples: [(snippet, link), (snippet, link), ...]
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        logger.error("Missing Google API credentials")
        return []
    
    try:
        # Build the service
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        
        # Execute search
        logger.info(f"Searching PartSelect for: {query}")
        result = service.cse().list(
            q=query,
            cx=GOOGLE_CSE_ID,
            num=min(num_results, 10)  # Max 10 results per request
        ).execute()
        
        # Extract snippets and links
        search_results = []
        if "items" in result:
            for item in result["items"]:
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                search_results.append((snippet, link))
                logger.debug(f"Found: {link}")
        
        logger.info(f"Found {len(search_results)} results for: {query}")
        return search_results
    
    except Exception as e:
        logger.exception(f"Google search failed for query '{query}': {e}")
        return []


def search_part_number(part_number: str):
    """
    Searches for a specific part number on PartSelect
    """
    query = f"part {part_number}"
    return google_partselect_search(query, num_results=3)


def search_model_compatibility(part_number: str, model_number: str):
    """
    Searches for compatibility information between a part and model
    """
    query = f"{part_number} compatible with {model_number}"
    return google_partselect_search(query, num_results=5)


def search_symptom(appliance_type: str, symptom: str):
    """
    Searches for troubleshooting information for a specific symptom
    """
    query = f"{appliance_type} {symptom} repair parts fix"
    return google_partselect_search(query, num_results=5)


def search_installation_guide(part_number: str):
    """
    Searches for installation instructions for a part
    """
    query = f"{part_number} installation instructions how to install"
    return google_partselect_search(query, num_results=3)