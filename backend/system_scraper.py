# symptom_scraper.py
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - SymptomScraper - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("symptom_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SymptomScraper")


def get_driver():
    """Initialize undetected Chrome driver"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    return driver


def scrape_symptom_page(symptom_url: str, model_number: str = None):
    """
    Scrapes troubleshooting information from a PartSelect symptom page
    
    Args:
        symptom_url: URL to the symptom page (e.g., ice-maker-not-working)
        model_number: Optional model number to filter results
    
    Returns:
        Dictionary with troubleshooting information
    """
    driver = None
    try:
        logger.info(f"Scraping symptom page: {symptom_url}")
        driver = get_driver()
        driver.get(symptom_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "symptom-header"))
        )
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        symptom_data = {}
        
        # Symptom title
        title_elem = soup.find('h1', class_='symptom-header')
        symptom_data['symptom'] = title_elem.text.strip() if title_elem else "Unknown Symptom"
        
        # Appliance type
        appliance_elem = soup.find('span', class_='appliance-type')
        symptom_data['appliance_type'] = appliance_elem.text.strip() if appliance_elem else "appliance"
        
        # Model number
        symptom_data['model_number'] = model_number
        
        # Common parts that fix this issue
        common_parts = []
        parts_section = soup.find('div', {'id': 'common-parts'})
        
        if parts_section:
            part_items = parts_section.find_all('div', class_='part-item')
            
            for item in part_items[:10]:  # Limit to top 10 parts
                part_info = {}
                
                # Part name
                name_elem = item.find('h3', class_='part-name')
                part_info['part_name'] = name_elem.text.strip() if name_elem else ""
                
                # Part number
                number_elem = item.find('span', class_='part-number')
                part_info['part_number'] = number_elem.text.strip() if number_elem else ""
                
                # Fix percentage
                fix_elem = item.find('span', class_='fix-percentage')
                if fix_elem:
                    fix_text = fix_elem.text.strip()
                    # Extract percentage number
                    import re
                    match = re.search(r'(\d+)%', fix_text)
                    part_info['fix_percentage'] = int(match.group(1)) if match else 0
                else:
                    part_info['fix_percentage'] = 0
                
                # Price
                price_elem = item.find('span', class_='part-price')
                part_info['price'] = price_elem.text.strip() if price_elem else "N/A"
                
                # Description
                desc_elem = item.find('p', class_='part-description')
                part_info['description'] = desc_elem.text.strip() if desc_elem else ""
                
                # User stories
                user_stories = []
                stories_section = item.find('div', class_='user-stories')
                if stories_section:
                    stories = stories_section.find_all('div', class_='story-item')
                    for story in stories[:3]:  # Limit to 3 stories per part
                        story_title = story.find('h4', class_='story-title')
                        story_content = story.find('p', class_='story-content')
                        
                        if story_title and story_content:
                            user_stories.append({
                                "title": story_title.text.strip(),
                                "instruction": story_content.text.strip()
                            })
                
                part_info['user_stories'] = user_stories
                common_parts.append(part_info)
        
        symptom_data['common_parts'] = common_parts
        
        # Diagnosis steps
        diagnosis_steps = []
        diagnosis_section = soup.find('div', {'id': 'diagnosis-steps'})
        if diagnosis_section:
            steps = diagnosis_section.find_all('li')
            for step in steps:
                diagnosis_steps.append(step.text.strip())
        
        symptom_data['diagnosis_steps'] = diagnosis_steps
        
        # Video tutorial
        video_elem = soup.find('iframe', class_='video-tutorial')
        symptom_data['video_url'] = video_elem.get('src') if video_elem else None
        
        logger.info(f"✅ Successfully scraped symptom data: {symptom_data.get('symptom')}")
        logger.info(f"   Found {len(common_parts)} common parts")
        
        return symptom_data
    
    except TimeoutException:
        logger.error(f"Timeout while scraping {symptom_url}")
        return None
    except Exception as e:
        logger.exception(f"Error scraping symptom page {symptom_url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def scrape_refrigerator_symptom(symptom: str):
    """
    Scrapes refrigerator-specific symptom information
    """
    # Construct PartSelect symptom URL
    symptom_slug = symptom.lower().replace(' ', '-')
    url = f"https://www.partselect.com/Refrigerator-Parts/Symptom/{symptom_slug}.htm"
    return scrape_symptom_page(url)


def scrape_dishwasher_symptom(symptom: str):
    """
    Scrapes dishwasher-specific symptom information
    """
    symptom_slug = symptom.lower().replace(' ', '-')
    url = f"https://www.partselect.com/Dishwasher-Parts/Symptom/{symptom_slug}.htm"
    return scrape_symptom_page(url)


# Example usage
if __name__ == "__main__":
    # Test scraping
    import json
    
    # Test refrigerator symptom
    data = scrape_refrigerator_symptom("ice maker not working")
    if data:
        print(json.dumps(data, indent=2))
    
    # Test dishwasher symptom
    data = scrape_dishwasher_symptom("not draining")
    if data:
        print(json.dumps(data, indent=2))