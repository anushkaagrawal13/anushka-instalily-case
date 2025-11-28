# partselect_scraper.py
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - PartSelectScraper - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PartSelectScraper")


def get_driver():
    """Initialize undetected Chrome driver"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = uc.Chrome(options=options)
    return driver


def scrape_part_details(part_url: str):
    """
    Scrapes detailed information from a PartSelect product page
    
    Args:
        part_url: Full URL to the part page (e.g., https://www.partselect.com/PS11752778.htm)
    
    Returns:
        Dictionary with part information or None if scraping fails
    """
    driver = None
    try:
        logger.info(f"Scraping part details from: {part_url}")
        driver = get_driver()
        driver.get(part_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pd__title"))
        )
        time.sleep(2)  # Additional wait for dynamic content
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract basic information
        part_data = {}
        
        # Part name
        title_elem = soup.find('h1', class_='pd__title')
        part_data['part_name'] = title_elem.text.strip() if title_elem else "Unknown Part"
        
        # Part number (from URL or page)
        part_number_elem = soup.find('span', class_='pd__part-number')
        if part_number_elem:
            part_data['part_number'] = part_number_elem.text.strip()
        else:
            # Extract from URL
            import re
            match = re.search(r'(PS|W10|WP|AP|W11)\d+', part_url)
            part_data['part_number'] = match.group(0) if match else "Unknown"
        
        # Price
        price_elem = soup.find('span', class_='pd__price-value')
        part_data['price'] = price_elem.text.strip() if price_elem else "N/A"
        
        # Availability
        stock_elem = soup.find('div', class_='pd__stock-status')
        part_data['in_stock'] = 'In Stock' in stock_elem.text if stock_elem else False
        
        # Description
        desc_elem = soup.find('div', class_='pd__description')
        part_data['full_description'] = desc_elem.text.strip() if desc_elem else ""
        
        # Installation information
        install_section = soup.find('div', {'id': 'installation-instructions'})
        if install_section:
            install_steps = []
            for step in install_section.find_all('li'):
                install_steps.append(step.text.strip())
            part_data['installation_info'] = "\n".join(install_steps) if install_steps else "See video tutorial"
        else:
            part_data['installation_info'] = "No installation information available."
        
        # Q&A Section
        qna_list = []
        qna_section = soup.find('div', {'id': 'questions-answers'})
        if qna_section:
            questions = qna_section.find_all('div', class_='qa-item')
            for qa in questions[:5]:  # Limit to 5 Q&As
                question_elem = qa.find('div', class_='qa-question')
                answer_elem = qa.find('div', class_='qa-answer')
                if question_elem and answer_elem:
                    qna_list.append({
                        "question": question_elem.text.strip(),
                        "answer": answer_elem.text.strip()
                    })
        part_data['qna'] = qna_list
        
        # Model Compatibility
        compat_list = []
        compat_section = soup.find('div', {'id': 'compatible-models'})
        if compat_section:
            models = compat_section.find_all('div', class_='model-item')
            for model in models[:10]:  # Limit to 10 models
                brand_elem = model.find('span', class_='model-brand')
                number_elem = model.find('span', class_='model-number')
                desc_elem = model.find('span', class_='model-desc')
                
                if brand_elem and number_elem:
                    compat_list.append({
                        "brand": brand_elem.text.strip(),
                        "model_number": number_elem.text.strip(),
                        "description": desc_elem.text.strip() if desc_elem else ""
                    })
        part_data['model_compatibility'] = compat_list
        
        # Troubleshooting info
        troubleshoot_data = {}
        troubleshoot_section = soup.find('div', {'id': 'troubleshooting'})
        if troubleshoot_section:
            symptoms = []
            symptom_elems = troubleshoot_section.find_all('a', class_='symptom-link')
            for sym in symptom_elems:
                symptoms.append(sym.text.strip())
            troubleshoot_data['symptoms'] = symptoms
        
        part_data['troubleshooting_info'] = troubleshoot_data
        
        logger.info(f"✅ Successfully scraped data for {part_data.get('part_number')}")
        return part_data
    
    except TimeoutException:
        logger.error(f"Timeout while scraping {part_url}")
        return None
    except Exception as e:
        logger.exception(f"Error scraping {part_url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def scrape_part_by_number(part_number: str):
    """
    Convenience function to scrape by part number
    Constructs the URL and calls scrape_part_details
    """
    # Remove any prefix and get just the number
    clean_number = part_number.replace('PS', '').replace('W10', '').replace('WP', '')
    
    # Try different URL formats
    urls_to_try = [
        f"https://www.partselect.com/PS{clean_number}.htm",
        f"https://www.partselect.com/W10{clean_number}.htm",
        f"https://www.partselect.com/{part_number}.htm"
    ]
    
    for url in urls_to_try:
        logger.info(f"Trying URL: {url}")
        result = scrape_part_details(url)
        if result:
            return result
    
    logger.warning(f"Could not scrape data for part {part_number}")
    return None


# Example usage
if __name__ == "__main__":
    # Test scraping
    test_url = "https://www.partselect.com/PS11752778.htm"
    data = scrape_part_details(test_url)
    
    if data:
        import json
        print(json.dumps(data, indent=2))