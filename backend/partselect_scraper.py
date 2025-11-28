# partselect_scraper.py

import undetected_chromedriver as uc
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PartSelectScraper:
    def __init__(self, headless=False):
        """
        Initializes the undetected ChromeDriver with specified options.
        """
        self.options = uc.ChromeOptions()
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent detection
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--start-maximized")  # Start maximized to ensure all elements are visible
        if headless:
            self.options.add_argument("--headless")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--window-size=1920,1080")

        # Initialize the ChromeDriver once and reuse it
        try:
            self.driver = uc.Chrome(options=self.options)
            logger.info("✅ ChromeDriver initialized successfully.")
        except Exception as e:
            logger.exception(f"❌ Failed to initialize ChromeDriver: {e}")
            raise e

    def close(self):
        """
        Closes the ChromeDriver instance.
        """
        try:
            self.driver.quit()
            logger.info("✅ ChromeDriver closed successfully.")
        except Exception as e:
            logger.exception(f"❌ Failed to close ChromeDriver: {e}")

    def scrape_partselect(self, url):
        """
        Scrapes product details from a PartSelect URL.
        Returns structured JSON data.
        """
        product_data = {}
        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 15)  # Explicit wait for dynamic content

            # Handle potential pop-ups or modals
            self.close_popup(wait)

            # Scroll to bottom to load dynamic content
            self.scroll_to_bottom()

            # Extract basic product info
            product_data.update(self.extract_basic_info(wait, url))

            # Extract full description
            product_data["full_description"] = self.extract_full_description(wait)

            # Extract troubleshooting info
            product_data["troubleshooting_info"] = self.extract_troubleshooting_info(wait)

            # Extract model compatibility
            product_data["model_compatibility"] = self.extract_model_compatibility(wait)

            # Extract Q&A
            product_data["qna"] = self.extract_qna(wait)

            product_data["product_page"] = url

        except Exception as e:
            logger.exception(f"❌ Scraping failed for URL {url}: {e}")
            product_data = {"error": "Scraping failed due to an unexpected error."}
        finally:
            # Optional: Keep the browser open for reuse
            pass  # Comment out or implement browser pooling as needed

        return product_data

    def close_popup(self, wait):
        """
        Attempts to close any pop-up modals.
        """
        try:
            decline_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@type='reset' and @data-click='close']")))
            decline_button.click()
            logger.info("✅ Popup closed successfully.")
            time.sleep(1)  # Brief pause to ensure the popup is closed
        except TimeoutException:
            logger.info("ℹ️ No popup detected.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to close popup: {e}")

    def scroll_to_bottom(self):
        """
        Scrolls to the bottom of the page to load all dynamic content.
        """
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Brief pause to allow content to load
            logger.info("✅ Scrolled to bottom of the page.")
        except Exception as e:
            logger.warning(f"⚠️ Scrolling failed: {e}")

    def extract_basic_info(self, wait, url):
        """
        Extracts basic product information.
        """
        product_data = {}
        try:
            main_div = self.driver.find_element(By.ID, "main")
            product_data.update({
                "inventory_id": main_div.get_attribute("data-inventory-id"),
                "description": main_div.get_attribute("data-description"),
                "price": main_div.get_attribute("data-price"),
                "brand": main_div.get_attribute("data-brand"),
                "model_type": main_div.get_attribute("data-modeltype"),
                "category": main_div.get_attribute("data-category"),
            })
            logger.info("✅ Extracted basic product information.")
        except NoSuchElementException as e:
            logger.warning(f"⚠️ Basic product info extraction failed: {e}")
            product_data = {"error": "No product details found."}
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error during basic info extraction: {e}")
            product_data = {"error": "Error extracting basic product details."}
        return product_data

    def extract_full_description(self, wait):
        """
        Extracts the full product description.
        """
        product_description = "No description available."
        try:
            # Ensure the Product Description section is expanded
            description_header = self.driver.find_element(By.ID, "ProductDescription")
            self.driver.execute_script("arguments[0].scrollIntoView();", description_header)
            if description_header.get_attribute("aria-expanded") == "false":
                description_header.click()
                wait.until(EC.attribute_to_be((By.ID, "ProductDescription"), "aria-expanded", "true"))
                logger.info("✅ Product Description section expanded.")

            description_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@itemprop='description']")))
            product_description = description_element.text.strip()
            logger.info("✅ Extracted full product description.")
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f"⚠️ Product Description extraction failed: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error during description extraction: {e}")
        return product_description

    def extract_troubleshooting_info(self, wait):
        """
        Extracts troubleshooting information.
        """
        troubleshooting_info = {}
        try:
            troubleshooting_header = self.driver.find_element(By.ID, "Troubleshooting")
            self.driver.execute_script("arguments[0].scrollIntoView();", troubleshooting_header)
            if troubleshooting_header.get_attribute("aria-expanded") == "false":
                troubleshooting_header.click()
                wait.until(EC.attribute_to_be((By.ID, "Troubleshooting"), "aria-expanded", "true"))
                logger.info("✅ Troubleshooting section expanded.")

            troubleshooting_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@id='Troubleshooting']/following-sibling::div")))
            raw_text = troubleshooting_element.text.strip()

            lines = raw_text.split('\n')

            symptoms = []
            products = []
            replacements = []

            # Parse each line
            for i in range(len(lines)):
                line = lines[i].strip()
                if line.startswith("This part fixes the following symptoms:"):
                    if i + 1 < len(lines):
                        symptoms = lines[i + 1].split(" | ")  # Extract symptoms
                elif line.startswith("This part works with the following products:"):
                    if i + 1 < len(lines):
                        products = lines[i + 1].split(" | ")  # Extract products
                elif line.startswith("Part#"):
                    if i + 1 < len(lines):
                        replacements = lines[i + 1].split(", ")  # Extract replacements

            # Remove empty entries
            troubleshooting_info = {
                "symptoms": [s.strip() for s in symptoms if s.strip()],
                "products": [p.strip() for p in products if p.strip()],
                "replacements": [r.strip() for r in replacements if r.strip()]
            }

            logger.info("✅ Extracted troubleshooting information.")
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f"⚠️ Troubleshooting Info extraction failed: {e}")
            troubleshooting_info = {}
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error during troubleshooting extraction: {e}")
            troubleshooting_info = {}
        return troubleshooting_info

    def extract_model_compatibility(self, wait):
        """
        Extracts model compatibility information.
        """
        model_compatibility = []
        try:
            model_compatibility_header = self.driver.find_element(By.ID, "ModelCrossReference")
            self.driver.execute_script("arguments[0].scrollIntoView();", model_compatibility_header)
            if model_compatibility_header.get_attribute("aria-expanded") == "false":
                model_compatibility_header.click()
                wait.until(EC.attribute_to_be((By.ID, "ModelCrossReference"), "aria-expanded", "true"))
                logger.info("✅ Model Compatibility section expanded.")

            model_compatibility_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@id='ModelCrossReference']/following-sibling::div")))
            model_compatibility_text = model_compatibility_element.text.strip()

            # Parse Model Compatibility into a list of dictionaries
            lines = model_compatibility_text.split('\n')

            # Identify the start of model data by finding the line after headers
            try:
                headers_index = lines.index("Description")
                data_lines = lines[headers_index + 1:]
            except ValueError:
                # If "Description" is not found, assume data starts after first 3 lines
                data_lines = lines[3:] if len(lines) > 3 else []

            # Iterate through the data in chunks of 3 lines (Brand, Model Number, Description)
            for i in range(0, len(data_lines), 3):
                try:
                    brand = data_lines[i].strip()
                    model_number = data_lines[i + 1].strip()
                    description = data_lines[i + 2].strip()

                    # Skip if any field is missing
                    if not brand or not model_number or not description:
                        continue

                    # Clean up description
                    description = description.replace("- REFRIGERATOR", "").strip()

                    model_compatibility.append({
                        "brand": brand,
                        "model_number": model_number,
                        "description": description
                    })
                except IndexError:
                    # Incomplete data; skip
                    continue

            logger.info("✅ Extracted model compatibility information.")
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f"⚠️ Model Compatibility extraction failed: {e}")
            model_compatibility = []
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error during model compatibility extraction: {e}")
            model_compatibility = []
        return model_compatibility

    def extract_qna(self, wait):
        """
        Extracts Q&A pairs from the product page.
        """
        qna = []
        try:
            # Ensure the Q&A section is expanded
            qna_header = self.driver.find_element(By.ID, "QuestionsAndAnswers")
            self.driver.execute_script("arguments[0].scrollIntoView();", qna_header)
            if qna_header.get_attribute("aria-expanded") == "false":
                qna_header.click()
                wait.until(EC.attribute_to_be((By.ID, "QuestionsAndAnswers"), "aria-expanded", "true"))
                logger.info("✅ Q&A section expanded.")

            # Wait for Q&A content to load
            qna_container = wait.until(EC.presence_of_element_located(
                (By.ID, "QuestionsAndAnswersContent")))
            
            # Function to extract Q&A from the current page
            def extract_qna_from_page():
                qna_elements = qna_container.find_elements(By.CLASS_NAME, "qna__question")
                for qna_element in qna_elements:
                    try:
                        # Extract question
                        question_text_element = qna_element.find_element(By.CLASS_NAME, "js-searchKeys")
                        question_text = question_text_element.text.strip()

                        # Extract answer
                        answer_element = qna_element.find_element(By.CSS_SELECTOR, "div.qna__ps-answer__msg > div.js-searchKeys")
                        answer_text = answer_element.text.strip()

                        qna.append({
                            "question": question_text,
                            "answer": answer_text
                        })
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to extract a Q&A pair: {e}")
                        continue

            # Extract Q&A from the first page
            extract_qna_from_page()

            # Handle pagination (if multiple pages exist)
            page_number = 1
            max_pages = 2  # Prevent infinite loops

            while page_number < max_pages:
                try:
                    # Get the first question's text to detect page change
                    first_qna_element = qna_container.find_element(By.CLASS_NAME, "qna__question")
                    first_question_text = first_qna_element.find_element(By.CLASS_NAME, "js-searchKeys").text.strip()

                    # Find the 'Next' button within the current Q&A container using flexible XPath
                    next_button = qna_container.find_element(By.XPATH, ".//ul[contains(@class, 'pagination') and contains(@class, 'js-pagination')]//li[contains(@class, 'next')]")
                    
                    # Check if 'Next' button is disabled
                    if "disabled" in next_button.get_attribute("class"):
                        logger.info("✅ No more Q&A pages to navigate.")
                        break
                    else:
                        # Click the 'Next' button
                        next_button.click()
                        logger.info(f"➡️ Navigated to Q&A page {page_number + 1}.")
                        
                        # Wait for the first question's text to change, indicating a new page
                        wait.until(lambda d: qna_container.find_element(By.CLASS_NAME, "qna__question").find_element(By.CLASS_NAME, "js-searchKeys").text.strip() != first_question_text)
                        
                        # Small delay to ensure content has loaded
                        time.sleep(1)

                        # Extract Q&A from the new page
                        extract_qna_from_page()
                        page_number += 1
                except (NoSuchElementException, TimeoutException) as e:
                    logger.info(f"✅ No further Q&A pages found: {e}")
                    break
                except Exception as e:
                    logger.warning(f"⚠️ Pagination handling failed: {e}")
                    break

            logger.info(f"✅ Extracted {len(qna)} Q&A pairs.")

        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f"⚠️ Q&A extraction failed: {e}")
            qna = []
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error during Q&A extraction: {e}")
            qna = []
        return qna

def scrape_partselect(url: str, headless: bool = False) -> dict:
    """
    Standalone function to scrape PartSelect product details.
    
    Args:
        url (str): The PartSelect product URL.
        headless (bool): Whether to run Chrome in headless mode. Default is False.
    
    Returns:
        dict: Scraped product data in JSON-like dictionary format.
    """
    scraper = PartSelectScraper(headless=headless)
    try:
        extracted_data = scraper.scrape_partselect(url)
    finally:
        scraper.close()
    
    return extracted_data

if __name__ == "__main__":
    test_url = "https://www.partselect.com/PS11752778-Whirlpool-WPW10321304-Refrigerator-Door-Shelf-Bin.htm"
    extracted_data = scrape_partselect(test_url, headless=False)  # Set headless=False to match original behavior

    print(json.dumps(extracted_data, indent=4))