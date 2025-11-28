# agent_manager.py

import json
import logging
import re
from langchain_community.chat_models import ChatOpenAI
from google_search import google_partselect_search
from partselect_scraper import scrape_partselect
from symptom_scraper import scrape_symptom_page
from vector_manager import index_scraped_data, semantic_search_with_intent
from langchain.schema import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - AgentManager - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AgentManager")


class AgentManager:
    def __init__(self):
        """
        Initializes the Agent Manager with necessary components.
        """
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)  # Slightly higher temp for better responses

    def detect_intent(self, query: str) -> str:
        """
        Detects the user's intent using GPT-4.
        """
        try:
            messages = [
                SystemMessage(content=(
                    "You are an AI assistant specialized in classifying queries related to refrigerator and dishwasher parts. "
                    "Classify the user's query into one of the following categories: 'troubleshoot', 'installation', "
                    "'compatibility', 'qna', or 'general'. Only return the category name as the response."
                )),
                HumanMessage(content=query)
            ]

            response = self.llm.invoke(messages)
            intent = response.content.strip().lower()

            valid_intents = {'troubleshoot', 'installation', 'compatibility', 'qna', 'general'}
            if intent in valid_intents:
                logger.info(f"🎯 Detected intent: {intent}")
                return intent
            else:
                logger.warning(f"⚠️ Unexpected intent response: {intent}. Defaulting to 'general'.")
                return "general"
        except Exception as e:
            logger.exception(f"🚨 Error during GPT-based intent detection: {e}")
            return "general"

    def extract_model_number(self, query: str) -> str:
        """
        Extracts the model number from the query using a combination of regex patterns
        and GPT-based extraction.
        """
        
        try:
            # First try common patterns for model numbers
            patterns = [
                r'\b[A-Z]{2,}\d{2,}[A-Z0-9]+\b',  # Matches WRS588FIHZ00
                r'\b[A-Z]+\d{4,}[A-Z]*\d*\b',     # Matches patterns like WRS588
                r'\b\d{1,2}-?[A-Z]{1,2}\d{3,}\b'  # Matches number-letter-number patterns
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, query.upper())
                for match in matches:
                    model = match.group(0)
                    # Skip if it looks like a part number (usually shorter)
                    if len(model) >= 8:  # Most model numbers are 8+ characters
                        logger.info(f"🔎 Model number detected via regex: {model}")
                        return model

            # If regex fails, use GPT to extract model number
            messages = [
                SystemMessage(content=(
                    "Extract the appliance model number from the query. Common formats include:\n"
                    "- WRS588FIHZ00 (Whirlpool)\n"
                    "- GSS25GSHSS (GE)\n"
                    "- RF28HMEDBSR (Samsung)\n"
                    "- WDT780SAEM1 (Whirlpool dishwasher)\n"
                    "Return only the model number or 'None' if not found. "
                    "Ignore part numbers which are usually shorter and start with PS, W10, etc."
                )),
                HumanMessage(content=query)
            ]
            
            response = self.llm.invoke(messages)
            model_number = response.content.strip()
            
            if model_number.lower() != 'none':
                logger.info(f"🔎 Model number detected via GPT: {model_number}")
                return model_number
            
            logger.warning("❌ No model number found in query")
            return None

        except Exception as e:
            logger.exception(f"❌ Error extracting model number: {e}")
            return None

    def extract_symptom(self, query: str) -> str:
        """
        Extracts the symptom from the user's query using GPT-4.
        """
        try:
            messages = [
                SystemMessage(content=(
                    "You are an AI assistant that extracts the main symptom from a user's query. "
                    "Given a user's message, identify and return the primary symptom they are experiencing. "
                    "Only return the symptom as a short phrase (e.g., 'ice maker not working', 'dishwasher not draining')."
                )),
                HumanMessage(content=query)
            ]

            response = self.llm.invoke(messages)
            symptom = response.content.strip()
            logger.info(f"🔍 Extracted symptom: {symptom}")
            return symptom
        except Exception as e:
            logger.exception(f"🚨 Error during symptom extraction: {e}")
            return ""

    def find_product_url_by_model(self, model_number: str) -> str:
        """
        Uses Google Custom Search to find the PartSelect URL based on the model number.
        """
        try:
            search_query = f"{model_number} site:partselect.com"
            search_results = google_partselect_search(search_query, num_results=5)
            if not search_results:
                logger.warning(f"No search results found for model number: {model_number}")
                return None

            # Look for the best matching URL
            for _, link in search_results:
                if link and "partselect.com" in link and model_number.lower() in link.lower():
                    logger.info(f"✅ Found PartSelect URL: {link}")
                    return link
            
            # If no exact match, use first result
            first_link = search_results[0][1]
            if first_link and "partselect.com" in first_link:
                logger.info(f"✅ Using first available URL: {first_link}")
                return first_link
            
            logger.warning("⚠️ Unable to extract a valid URL from search results.")
            return None
        except Exception as e:
            logger.exception(f"🚨 Error during Google search for model number {model_number}: {e}")
            return None

    def find_product_url_by_part(self, part_number: str) -> str:
        """
        Find product URL using part number through Google search
        """
        
        try:
            # Direct search for the part number
            search_query = f"{part_number} site:partselect.com"
            search_results = google_partselect_search(search_query, num_results=5)
            
            if not search_results:
                logger.warning(f"No results found for part number: {part_number}")
                return None
            
            # Log all found URLs for debugging
            for _, url in search_results:
                logger.debug(f"Found URL: {url}")
            
            # Get the first valid product URL
            for _, url in search_results:
                # Look for URLs containing the part number or /parts/ path
                if "partselect.com" in url and (part_number.upper() in url.upper() or "/parts/" in url):
                    logger.info(f"✅ Found matching product URL: {url}")
                    return url
            
            # If no specific match found, return the first PartSelect URL
            first_url = search_results[0][1] if search_results else None
            if first_url and "partselect.com" in first_url:
                logger.info(f"✅ Using first available URL: {first_url}")
                return first_url
            
            logger.warning("No valid product URLs found in search results")
            return None
            
        except Exception as e:
            logger.exception(f"❌ Error finding product URL: {e}")
            return None

    def handle_query(self, query: str, session: dict) -> dict:
        """
        Handles user queries and returns appropriate responses based on intent.
        """
        logger.info(f"🧐 Processing query: {query}")

        try:
            intent = self.detect_intent(query)
            logger.info(f"🎯 Detected intent: {intent}")

            # Extract model number and brand for all intents
            model_number = self.extract_model_number(query)
            brand = None
            if not model_number:
                brand = self.extract_brand(query)
            logger.info(f"🔎 Model number detected: {model_number}")
            logger.info(f"🏢 Brand detected: {brand}")

            if intent == "troubleshoot":
                # Extract symptom
                symptom = self.extract_symptom(query)
                logger.info(f"🔍 Extracted symptom: {symptom}")
                
                if not symptom:
                    logger.warning("❌ No symptom extracted from query")
                    return {
                        "response": "I couldn't identify a specific issue in your query. Could you please describe the problem you're experiencing with your refrigerator or dishwasher?",
                        "status": "error"
                    }

                # Search with model/brand included
                search_query = f"{symptom} {model_number if model_number else brand if brand else 'refrigerator dishwasher'}"
                search_results = google_partselect_search(search_query, num_results=5)
                symptom_pages = [link for _, link in search_results if "Symptoms" in link or "symptom" in link.lower()]
                logger.info(f"🔍 Found {len(symptom_pages)} symptom pages")

                if not symptom_pages:
                    logger.warning(f"No symptom pages found for symptom: {symptom}")
                    return {
                        "response": f"I couldn't find specific troubleshooting information for '{symptom}'. Please try rephrasing your issue or contact PartSelect support for assistance.",
                        "status": "error"
                    }

                # Scrape first symptom page
                first_symptom_page = symptom_pages[0]
                logger.info(f"🌐 Scraping symptom page: {first_symptom_page}")
                scraped_data = scrape_symptom_page(first_symptom_page, headless=True)

                # Index the scraped data
                if scraped_data:
                    index_status = index_scraped_data(json.dumps(scraped_data))
                    logger.info(f"Indexed new scraped data: {index_status}")

                    # Perform semantic search
                    vector_results = semantic_search_with_intent(query, intent, model_number)
                    logger.info(f"Vector search completed with {len(vector_results) if isinstance(vector_results, list) else 0} results")

                # Format the scraped data for the LLM
                if scraped_data and 'common_parts' in scraped_data and scraped_data['common_parts']:
                    common_parts = scraped_data['common_parts'][0]
                    user_stories = common_parts.get('user_stories', [])[:3]
                    formatted_stories = []
                    for story in user_stories:
                        formatted_stories.append({
                            "title": story.get('title', ''),
                            "instruction": story.get('instruction', '')
                        })
                    
                    formatted_data = {
                        "symptom": symptom,
                        "description": common_parts.get('description', ''),
                        "fix_percentage": common_parts.get('fix_percentage', ''),
                        "part_name": common_parts.get('part_name', ''),
                        "price": common_parts.get('price', ''),
                        "user_stories": formatted_stories
                    }
                    
                    messages = [
                        SystemMessage(content=(
                            "You are an expert appliance repair assistant. Create a clear, well-formatted troubleshooting guide.\n\n"
                            "**FORMATTING RULES:**\n"
                            "- Use '##' for main sections\n"
                            "- Use '###' for subsections\n"
                            "- Use bullet points (•) for lists\n"
                            "- Use numbered lists (1., 2., 3.) for steps\n"
                            "- Use **bold** for emphasis\n"
                            "- Keep it concise but comprehensive\n\n"
                            "**REQUIRED SECTIONS:**\n\n"
                            "## Problem Analysis\n"
                            "Brief description of the issue and common causes\n\n"
                            "## Most Likely Solution\n\n"
                            "### Required Part\n"
                            "• Part name and number\n"
                            "• Price\n"
                            "• Success rate\n\n"
                            "### Repair Steps\n"
                            "1. First step\n"
                            "2. Second step\n"
                            "(Include safety warnings if needed)\n\n"
                            "## What Others Did\n"
                            "Brief summary of 1-2 user repair stories\n\n"
                            "Keep the entire response under 300 words."
                        )),
                        HumanMessage(content=(
                            f"User Query: {query}\n\n"
                            f"Troubleshooting Data:\n{json.dumps(formatted_data, indent=2)}"
                        ))
                    ]
                    
                    try:
                        logger.info("🤖 Generating response using LLM")
                        response = self.llm.invoke(messages)
                        logger.info("✅ LLM response generated successfully")
                        
                        return {
                            "response": response.content,
                            "status": "success"
                        }
                    except Exception as e:
                        logger.exception(f"❌ Error generating response: {e}")
                        return {
                            "response": "I encountered an error while generating the troubleshooting guide. Please try again.",
                            "status": "error"
                        }
                else:
                    logger.warning("❌ No common parts found in scraped data")
                    return {
                        "response": "I couldn't find detailed troubleshooting information for this issue. Please check PartSelect.com directly or contact their support.",
                        "status": "error"
                    }

            elif intent == "installation":
                # Extract part number
                part_number = self.extract_part_number(query)
                logger.info(f"🔎 Part number detected: {part_number}")
                
                if not part_number:
                    return {
                        "response": "I couldn't identify a part number in your query. Please provide the part number you want to install (e.g., PS11752778).",
                        "status": "error"
                    }

                # Find product URL
                product_url = self.find_product_url_by_part(part_number)
                logger.info(f"🌐 Product URL found: {product_url}")
                
                if not product_url:
                    return {
                        "response": f"I couldn't find information for part number {part_number} on PartSelect. Please verify the part number is correct.",
                        "status": "error"
                    }

                # Scrape installation data
                logger.info(f"🌐 Scraping product page: {product_url}")
                scraped_data = scrape_partselect(product_url, headless=True)

                # Index the scraped data
                if scraped_data:
                    index_status = index_scraped_data(json.dumps(scraped_data))
                    logger.info(f"Indexed new scraped data: {index_status}")

                    # Perform semantic search
                    vector_results = semantic_search_with_intent(query, intent, model_number)
                    logger.info(f"Vector search completed")

                if not scraped_data:
                    return {
                        "response": "I couldn't retrieve installation information for this part. Please visit PartSelect.com directly.",
                        "status": "error"
                    }

                messages = [
                    SystemMessage(content=(
                        "You are an expert appliance repair assistant. Create a clear, step-by-step installation guide.\n\n"
                        "**FORMATTING RULES:**\n"
                        "- Use '##' for main sections\n"
                        "- Use '###' for subsections\n"
                        "- Use bullet points (•) for lists\n"
                        "- Use numbered lists (1., 2., 3.) for sequential steps\n"
                        "- Use **bold** for important warnings\n"
                        "- Keep it clear and concise\n\n"
                        "**REQUIRED SECTIONS:**\n\n"
                        "## Part Information\n"
                        "Brief description, price, and what it fixes\n\n"
                        "## Installation Guide\n\n"
                        "### Tools Needed\n"
                        "• List required tools\n"
                        "• Estimated time: X minutes\n\n"
                        "### Safety First\n"
                        "• **Disconnect power** before starting\n"
                        "• Other safety precautions\n\n"
                        "### Installation Steps\n"
                        "1. First step with clear instructions\n"
                        "2. Second step\n"
                        "3. Continue with detailed steps\n\n"
                        "### Final Checks\n"
                        "• Test the appliance\n"
                        "• Verify proper operation\n\n"
                        "Keep the entire response under 400 words."
                    )),
                    HumanMessage(content=(
                        f"User Query: {query}\n"
                        f"Part Number: {part_number}\n\n"
                        f"Installation Data:\n{json.dumps(scraped_data, indent=2)}"
                    ))
                ]
                
                logger.info("🤖 Generating installation instructions")
                response = self.llm.invoke(messages)
                logger.info("✅ Generated installation instructions")
                
                return {
                    "response": response.content,
                    "status": "success"
                }

            elif intent == "compatibility":
                # Extract part number (model number already extracted)
                part_number = self.extract_part_number(query)
                logger.info(f"🔎 Part number detected: {part_number}")
                
                if not model_number and not brand:
                    return {
                        "response": "I couldn't identify a model number or brand in your query. Please provide your appliance's model number (e.g., WDT780SAEM1) to check compatibility.",
                        "status": "error"
                    }
                
                if not part_number:
                    return {
                        "response": "I couldn't identify a part number in your query. Please provide the part number you want to check for compatibility.",
                        "status": "error"
                    }

                # Find product URL for the model
                product_url = self.find_product_url_by_model(model_number) if model_number else None
                if not product_url:
                    return {
                        "response": f"I couldn't find information for model number {model_number}. Please verify the model number is correct.",
                        "status": "error"
                    }

                # Scrape compatibility data
                scraped_data = scrape_partselect(product_url, headless=True)

                # Index the scraped data
                if scraped_data:
                    index_status = index_scraped_data(json.dumps(scraped_data))
                    logger.info(f"Indexed new scraped data: {index_status}")

                    # Perform semantic search
                    vector_results = semantic_search_with_intent(query, intent, model_number)
                    logger.info(f"Vector search completed")

                messages = [
                    SystemMessage(content=(
                        "You are an expert appliance parts assistant. Provide a clear compatibility answer.\n\n"
                        "**FORMATTING RULES:**\n"
                        "- Use '##' for the main answer\n"
                        "- Use '###' for subsections\n"
                        "- Use bullet points for details\n"
                        "- Keep it concise and direct\n\n"
                        "**REQUIRED FORMAT:**\n\n"
                        "## Compatibility: YES/NO\n\n"
                        "### Part Details\n"
                        "• Part name and number\n"
                        "• Price and availability\n\n"
                        "### Compatibility Notes\n"
                        "• Key compatibility information\n"
                        "• Installation notes if relevant\n\n"
                        "Keep response under 200 words."
                    )),
                    HumanMessage(content=(
                        f"User Query: {query}\n"
                        f"Model Number: {model_number}\n"
                        f"Part Number: {part_number}\n\n"
                        f"Compatibility Data:\n{json.dumps(scraped_data, indent=2)}"
                    ))
                ]
                
                response = self.llm.invoke(messages)
                return {
                    "response": response.content,
                    "status": "success"
                }

            else:
                return {
                    "response": "I can help you with:\n\n• **Troubleshooting** - Diagnose and fix appliance issues\n• **Installation** - Step-by-step part installation guides\n• **Compatibility** - Check if parts fit your model\n\nWhat would you like help with?",
                    "status": "error"
                }

        except Exception as e:
            logger.exception(f"❌ Error in handle_query: {e}")
            return {
                "response": f"I encountered an error processing your request. Please try again or rephrase your question.",
                "status": "error"
            }

    def extract_part_number(self, query: str) -> str:
        """
        Extracts part number from the query using regex and GPT.
        """
        try:
            # Try regex first for common part number patterns
            patterns = [
                r'\bPS\d{5,}\b',           # PS11752778
                r'\bW10\d{5,}\b',          # W10195416
                r'\bWP\d{5,}\b',           # WP12345678
                r'\b[A-Z]{2}\d{6,}\b'      # Generic pattern
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query.upper())
                if match:
                    part_num = match.group(0)
                    logger.info(f"🔎 Part number detected via regex: {part_num}")
                    return part_num
            
            # Fall back to GPT
            messages = [
                SystemMessage(content=(
                    "Extract the part number from the query. Common formats:\n"
                    "- PS11752778\n"
                    "- W10195416\n"
                    "- WP12345678\n"
                    "Return only the part number or 'None' if not found."
                )),
                HumanMessage(content=query)
            ]
            
            response = self.llm.invoke(messages)
            part_number = response.content.strip()
            
            if part_number.lower() != 'none':
                logger.info(f"🔎 Part number detected via GPT: {part_number}")
                return part_number
            
            return None
            
        except Exception as e:
            logger.exception(f"❌ Error extracting part number: {e}")
            return None

    def scrape_and_process(self, product_url: str) -> dict:
        """
        Scrapes the product page and indexes the data.
        """
        try:
            scraped_data = scrape_partselect(product_url, headless=True)
            json_data = json.dumps(scraped_data, indent=2)
            indexing_result = index_scraped_data(json_data)
            if "✅" in indexing_result:
                logger.info("✅ Scraped data indexed successfully.")
                return scraped_data
            else:
                logger.error("❌ Failed to index scraped data.")
                return {}
        except Exception as e:
            logger.exception(f"🚨 Error during scraping and processing: {e}")
            return {}

    def extract_brand(self, query: str) -> str:
        """
        Extracts brand name from the query using GPT.
        """
        try:
            messages = [
                SystemMessage(content=(
                    "Extract the appliance brand name from the query. Common brands:\n"
                    "- Whirlpool\n"
                    "- GE\n"
                    "- Samsung\n"
                    "- LG\n"
                    "- Frigidaire\n"
                    "- KitchenAid\n"
                    "- Maytag\n"
                    "Return only the brand name or 'None' if not found."
                )),
                HumanMessage(content=query)
            ]
            
            response = self.llm.invoke(messages)
            brand = response.content.strip()
            
            if brand.lower() != 'none':
                logger.info(f"🏢 Brand detected: {brand}")
                return brand
            
            return None
            
        except Exception as e:
            logger.exception(f"❌ Error extracting brand: {e}")
            return None


# Instantiate Agent Manager
agent_manager = AgentManager()