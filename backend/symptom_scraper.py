# symptom_scraper.py

import undetected_chromedriver as uc
import time
import json
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - symptom_scraper - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("symptom_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SymptomScraper:
    def __init__(self, headless=True):
        """
        Initializes undetected ChromeDriver with specified options.
        """
        self.options = uc.ChromeOptions()
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--start-maximized")
        if headless:
            self.options.add_argument("--headless")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--window-size=1920,1080")

        try:
            self.driver = uc.Chrome(options=self.options)
            logger.info("✅ SymptomScraper: ChromeDriver initialized successfully.")
        except Exception as e:
            logger.exception(f"❌ Failed to initialize ChromeDriver: {e}")
            raise e

    def close(self):
        """
        Closes the ChromeDriver instance.
        """
        try:
            self.driver.quit()
            logger.info("✅ SymptomScraper: ChromeDriver closed successfully.")
        except Exception as e:
            logger.exception(f"❌ Failed to close ChromeDriver: {e}")

    def scrape_symptom_page(self, url: str):
        """
        Scrapes a PartSelect Symptom Page for structured data.
        Returns a dictionary with symptom info, common parts, user stories, etc.
        """
        data = {}
        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 15)

            # Attempt to close any pop-up if it exists
            self.close_popup(wait)

            # Wait for main content to load (adjust sleep as needed)
            time.sleep(2)

            data["product_url"] = url

            # Extract high-level info (model num, symptom title, etc.)
            data.update(self.extract_symptom_info(wait))

            # Extract each "symptoms__redesign" row for parts and user stories
            # Since we only want the first symptom section (highest fix_percentage),
            # we'll modify the method to return only the first one.
            data["common_parts"] = self.extract_common_parts(wait, limit=1)

        except Exception as e:
            logger.exception(f"❌ Scraping failed for Symptom Page {url}: {e}")
            data["error"] = f"Scraping failed: {e}"


        return data

    def close_popup(self, wait):
        """
        Closes any pop-up modals if present.
        """
        try:

            decline_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='reset' and @data-click='close']"))
            )
            decline_btn.click()
            logger.info("✅ Popup closed successfully.")
            time.sleep(1)
        except TimeoutException:
            logger.info("ℹ️ No popup detected on this symptom page.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to close popup: {e}")

    def extract_symptom_info(self, wait):
        """
        Extracts top-level info such as the symptom title, etc.
        """
        result = {}
        try:
            main_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#main")))
            result["model_number"] = main_el.get_attribute("data-model-num") or ""

            try:
                title_el = main_el.find_element(By.CSS_SELECTOR, "h1.title-main")
                result["symptom_title"] = title_el.text.strip()
            except NoSuchElementException:
                result["symptom_title"] = ""

            logger.info("✅ Extracted base symptom info.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract symptom info: {e}")
        return result

    def extract_common_parts(self, wait, limit=1):
        """
        Extracts part listings and associated user repair stories from the "symptoms__redesign" containers.
        Returns a list of part objects, each with user stories.
        Only processes up to 'limit' number of symptom_rows.
        """
        parts = []
        try:
            # Each "div.mb-5.symptoms" typically holds one part listing + user stories
            symptom_rows = self.driver.find_elements(By.CSS_SELECTOR, "div.mb-5.symptoms.d-flex")
            if not symptom_rows:
                logger.info("ℹ️ No 'symptoms__redesign' sections found with the .mb-5.symptoms selector.")
                return parts

            # Process only up to 'limit' number of symptom_rows
            for idx, row in enumerate(symptom_rows):
                if idx >= limit:
                    break
                try:
                    # PART NAME + LINK
                    part_header = row.find_element(By.CSS_SELECTOR, "div.symptoms__header a")
                    part_name = part_header.text.strip()
                    part_url = part_header.get_attribute("href")

                    # FIX PERCENTAGE
                    fix_percent_el = row.find_element(By.CSS_SELECTOR, "div.symptoms__percent span.bold")
                    fix_percent = fix_percent_el.text.strip().replace("%", "")

                    # PART PRICE, PART NUMBER, DESCRIPTION
                    price, ps_number, manufacturer_pn, description = self.extract_part_details(row)

                    # EXTRACT USER STORIES
                    user_stories = self.extract_user_stories(row)

                    # Skip parts with no user stories
                    if not user_stories:
                        logger.info(f"ℹ️ Skipping part '{part_name}' due to no user stories.")
                        continue

                    parts.append({
                        "part_name": part_name,
                        "part_url": part_url,
                        "fix_percentage": fix_percent,
                        "price": price,
                        "part_number": ps_number,
                        "manufacturer_part_number": manufacturer_pn,
                        "description": description,
                        "user_stories": user_stories
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting part data for row: {e}")

            logger.info(f"✅ Extracted {len(parts)} common parts from symptom page.")
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error extracting common parts: {e}")
        return parts

    def extract_part_details(self, row_el):
        """
        Extracts part details: price, PartSelect #, manufacturer #, short description from row element.
        """
        price = ""
        ps_number = ""
        manufacturer_pn = ""
        description = ""
        try:
            # Price
            try:
                price_el = row_el.find_element(By.CSS_SELECTOR, "span.price.pd__price span.js-partPrice")
                price = price_el.text.strip()  # e.g. "75.92"
            except NoSuchElementException:
                pass

            # PartSelect Number
            try:
                ps_el = row_el.find_element(By.CSS_SELECTOR, "div.mt-3.mb-2.bold span.bold.text-teal")
                ps_number = ps_el.text.strip()  # e.g. "PS11738120"
            except NoSuchElementException:
                pass

            # Manufacturer PN
            try:
                mpn_el = row_el.find_element(By.CSS_SELECTOR, "div.mb-2.bold span.bold.text-teal")
                manufacturer_pn = mpn_el.text.strip()  # e.g. "W10873791"
            except NoSuchElementException:
                pass

            # Description
            try:
                desc_el = row_el.find_element(By.CSS_SELECTOR, "p.mb-4")
                description = desc_el.text.strip()
            except NoSuchElementException:
                pass

        except Exception as e:
            logger.warning(f"⚠️ Error extracting part details: {e}")

        return price, ps_number, manufacturer_pn, description

    def extract_user_stories(self, row_el):
        """
        Extracts user repair stories from the row element:
         .repair-story =>  .repair-story__title, .repair-story__instruction__content, .repair-story__details
        """
        stories = []
        try:
            story_elements = row_el.find_elements(By.CSS_SELECTOR, "div.repair-story")
            for s_el in story_elements:
                try:
                    # Click "Read More" if exists to expand full instruction
                    self.expand_read_more(s_el)

                    # Title
                    story_title = s_el.find_element(By.CSS_SELECTOR, "div.repair-story__title").text.strip()

                    # Instruction Content
                    instruction_el = s_el.find_element(By.CSS_SELECTOR, "div.repair-story__instruction__content")
                    instruction_text = instruction_el.text.strip()

                    # Additional details (author, difficulty, time, tools)
                    # These are stored in a ul.repair-story__details with <li>
                    user_details = self.parse_details_li(s_el.find_elements(By.CSS_SELECTOR, "ul.repair-story__details li"))

                    # Skip empty user stories
                    if not any([story_title, instruction_text, user_details.get("author"), user_details.get("difficulty"),
                                user_details.get("time"), user_details.get("tools")]):
                        logger.info("ℹ️ Skipping an empty user story.")
                        continue

                    stories.append({
                        "title": story_title,
                        "instruction": instruction_text,
                        "author": user_details.get("author", ""),
                        "difficulty": user_details.get("difficulty", ""),
                        "time": user_details.get("time", ""),
                        "tools": user_details.get("tools", [])
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting a user story: {e}")
        except NoSuchElementException:
            pass
        return stories

    def expand_read_more(self, story_element):
        """
        Clicks the "Read more" button/span within a user story to reveal full instructions.
        """
        try:
            # Locate the span with data-collapse-trigger="show-more"
            read_more_trigger = story_element.find_element(By.CSS_SELECTOR, "span[data-collapse-trigger='show-more']")
            # Within this span, locate the inner span with text "Read more"
            read_more_text = read_more_trigger.find_element(By.CSS_SELECTOR, "span.bold.text-link.underline")
            if read_more_text.is_displayed():
                read_more_text.click()
                logger.info("✅ Clicked 'Read more' to expand instruction.")
                time.sleep(1)  # Wait for content to load
        except NoSuchElementException:
            logger.info("ℹ️ No 'Read more' button found for this user story.")
        except ElementClickInterceptedException:
            logger.warning("⚠️ 'Read more' button could not be clicked due to overlay or other issue.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to click 'Read more' button: {e}")

    def parse_details_li(self, li_els):
        """
        Maps each LI to a key like { "author": ..., "difficulty": ..., "time": ..., "tools": [...] }
        """
        details = {}
        for li in li_els:
            try:
                svg_use = li.find_element(By.CSS_SELECTOR, "svg use")
                svg_href = svg_use.get_attribute("href")
                value_text = li.find_element(By.CSS_SELECTOR, "div").text.strip()
                # Check the svg href to determine which field it references
                if "#profile" in svg_href:
                    # Possibly author
                    details["author"] = value_text.split("\n")[-1]  # e.g., "James from NEW LONDON, NH"
                elif "#difficulty" in svg_href:
                    details["difficulty"] = value_text.replace("Difficulty Level:", "").strip()
                elif "#duration" in svg_href:
                    details["time"] = value_text.replace("Total Repair Time:", "").strip()
                elif "#tools" in svg_href:
                    # Something like "Tools:\nNutdriver, Screw drivers"
                    lines = value_text.split("\n")
                    if len(lines) > 1:
                        tool_line = lines[-1]  # "Nutdriver, Screw drivers"
                        tools_list = [t.strip() for t in tool_line.split(",")]
                        details["tools"] = tools_list
            except Exception:
                continue
        return details


def scrape_symptom_page(url: str, headless: bool = False) -> dict:
    """
    Standalone function to scrape PartSelect symptom pages.
    """
    scraper = SymptomScraper(headless=headless)
    try:
        data = scraper.scrape_symptom_page(url)
    finally:
        scraper.close()
    return data


if __name__ == "__main__":
    test_url = "https://www.partselect.com/Models/WRS588FIHZ00/Symptoms/Ice-maker-not-making-ice/"
    result_data = scrape_symptom_page(test_url, headless=False)
    print(json.dumps(result_data, indent=2))