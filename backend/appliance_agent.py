# agent_manager.py

import json
import logging
import re
from langchain_community.chat_models import ChatOpenAI 
from google_search import google_partselect_search
from partselect_scraper import scrape_partselect
from symptom_scraper import scrape_symptom_page 
from vector_manager import live_store, index_scraped_data, semantic_search_with_intent
from langchain.schema import HumanMessage, SystemMessage

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - AgentManager - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AgentManager")


class ApplianceAgent:
    def __init__(self):
        """
        Initializes the Agent Manager with necessary components.
        """
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0)  

    def detect_intent(self, query: str) -> str:
        """
        Detects the user's intent using GPT-4.
        """
        try:
            messages = [
                SystemMessage(content=(
                    "You are an AI assistant specialized in classifying queries related to refrigerator and dishwasher parts."
                    " Classify the user's query into one of the following categories: 'troubleshoot', 'installation', "
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
                        return model

            # If regex fails, use GPT to extract model number
            messages = [
                SystemMessage(content=(
                    "Extract the appliance model number from the query. Common formats include:\n"
                    "- WRS588FIHZ00 (Whirlpool)\n"
                    "- GSS25GSHSS (GE)\n"
                    "- RF28HMEDBSR (Samsung)\n"
                    "Return only the model number or 'None' if not found. "
                    "Ignore part numbers which are usually shorter."
                )),
                HumanMessage(content=query)
            ]
            
            response = self.llm.invoke(messages)
            model_number = response.content.strip()
            
            if model_number.lower() != 'none':
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
                    "You are an AI assistant that extracts the main symptom from a user's query."
                    " Given a user's message, identify and return the primary symptom they are experiencing."
                    " Only return the symptom as a short phrase."
                )),
                HumanMessage(content=query)
            ]

            response = self.llm.invoke(messages)
            symptom = response.content.strip()
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
            search_results = google_partselect_search(search_query, num_results=1)
            if not search_results:
                logger.warning(f"No search results found for model number: {model_number}")
                return "❌ No search results found for the given model number."

            _, first_link = search_results[0]
            if first_link and first_link.startswith("https://www.partselect.com/"):
                logger.info(f"✅ Found PartSelect URL: {first_link}")
                return first_link
            else:
                logger.warning("⚠️ Unable to extract a valid URL from search results.")
                return "❌ Unable to extract a valid URL from search results."
        except Exception as e:
            logger.exception(f"🚨 Error during Google search for model number {model_number}: {e}")
            return f"❌ Error during Google search: {e}"

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
                if "partselect.com" in url and (part_number in url or "/parts/" in url):
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

    def process_query(self, query: str) -> dict:
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
                    return {"response": "❌ Could not identify a symptom in your query. Please describe the issue you're experiencing.", "status": "error"}

                # Search with model/brand included
                search_query = f"{symptom} {model_number if model_number else brand if brand else ''}"
                search_results = google_partselect_search(search_query, num_results=5)
                symptom_pages = [link for _, link in search_results if "Symptoms" in link]
                logger.info(f"🔍 Found {len(symptom_pages)} symptom pages")

                if not symptom_pages:
                    logger.warning(f"No symptom pages found for symptom: {symptom}")
                    return {"response": "❌ Could not find relevant symptom information on PartSelect.", "status": "error"}

                # Scrape first symptom page
                first_symptom_page = symptom_pages[0]
                logger.info(f"🌐 Scraping symptom page: {first_symptom_page}")
                scraped_data = scrape_symptom_page(first_symptom_page, headless=False)
                logger.info(f"📄 Raw scraped data received")

                # Index the scraped data
                if scraped_data:
                    index_status = index_scraped_data(json.dumps(scraped_data))
                    logger.info(f"Indexed new scraped data: {index_status}")

                    # Now perform semantic search
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
                        "user_stories": formatted_stories
                    }
                    
                    messages = [
                        SystemMessage(content=(
                            "You are a helpful appliance repair assistant. Create a concise but detailed response using the provided information. "
                            "Format your response using these guidelines:\n"
                            "1. Use '### ' for main sections\n"
                            "2. Use '#### ' for subsections\n"
                            "3. Use bullet points for lists\n"
                            "4. Keep sections compact but informative\n\n"
                            "Include these sections:\n"
                            "### Problem Analysis\n"
                            "- Brief description of the issue\n"
                            "- Potential causes\n\n"
                            "### Solution\n"
                            "#### Required Parts\n"
                            "- Part information\n"
                            "- Fix success rate\n\n"
                            "#### Repair Steps\n"
                            "1. Numbered steps\n"
                            "2. Clear instructions\n\n"
                            "Keep the formatting consistent and clean."
                        )),
                        HumanMessage(content=(
                            f"Query: {query}\n\n"
                            f"Troubleshooting Data: {json.dumps(formatted_data, indent=2)}"
                        ))
                    ]
                    
                    try:
                        logger.info("🤖 Generating response using LLM")
                        response = self.llm.invoke(messages)
                        logger.info("✅ LLM response generated successfully")
                        
                        response_content = response.content
                        if "🤔 Thought Process:" in response_content and "📝 Response:" in response_content:
                            final_response = response_content.split("📝 Response:")[1].strip()
                            return {
                                "response": final_response,
                                "status": "success"
                            }
                        else:
                            return {
                                "response": response_content,
                                "status": "success"
                            }
                    except Exception as e:
                        logger.exception(f"❌ Error generating response: {e}")
                        return {
                            "response": "❌ Error generating response from scraped data.",
                            "status": "error"
                        }
                else:
                    logger.warning("❌ No common parts found in scraped data")
                    return {"response": "❌ Could not find relevant troubleshooting information.", "status": "error"}

            elif intent == "installation":
                # Extract part number
                part_number = self.extract_part_number(query)
                logger.info(f"🔎 Part number detected: {part_number}")
                
                if not part_number:
                    return {
                        "response": "❌ Could not identify a part number in your query. Please provide the part number you want to install.",
                        "status": "error"
                    }

                # Find product URL
                product_url = self.find_product_url_by_part(part_number)
                logger.info(f"🌐 Product URL found: {product_url}")
                
                if not product_url:
                    return {
                        "response": f"❌ Could not find information for part number {part_number}.",
                        "status": "error"
                    }

                # Scrape installation data
                logger.info(f"🌐 Scraping product page: {product_url}")
                scraped_data = scrape_partselect(product_url, headless=False)
                logger.info(f"📄 Scraped data received: {bool(scraped_data)}")

                # Index the scraped data
                if scraped_data:
                    index_status = index_scraped_data(json.dumps(scraped_data))
                    logger.info(f"Indexed new scraped data: {index_status}")

                    # Now perform semantic search
                    vector_results = semantic_search_with_intent(query, intent, model_number)
                    logger.info(f"Vector search completed with {len(vector_results) if isinstance(vector_results, list) else 0} results")

                if not scraped_data:
                    return {
                        "response": "❌ Could not retrieve installation information.",
                        "status": "error"
                    }

                messages = [
                    SystemMessage(content=(
                        "You are a helpful appliance repair assistant. Create a concise but detailed response using the provided information. "
                        "Format your response using these guidelines:\n"
                        "1. Use '### ' for main sections (Part Info)\n"
                        "2. Use '#### ' for subsections (Tools Needed)\n"
                        "3. Use bullet points for lists\n"
                        "4. Keep sections compact but informative\n\n"
                        "Include these sections:\n"
                        "### Part Information\n"
                        "- Part details and compatibility\n"
                        "- Price and availability\n\n"
                        "### Installation Guide\n"
                        "#### Tools Needed\n"
                        "- List required tools\n"
                        "- Estimated time\n\n"
                        "#### Safety First\n"
                        "- Key safety precautions\n\n"
                        "#### Steps\n"
                        "1. Numbered steps\n"
                        "2. Clear instructions\n\n"
                        "Keep the formatting consistent and clean."
                    )),
                    HumanMessage(content=(
                        f"Query: {query}\n\n"
                        f"Installation Data: {json.dumps(scraped_data, indent=2)}"
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
                        "response": "❌ Could not identify a model number or brand in your query. Please provide your appliance's model number or brand.",
                        "status": "error"
                    }
                
                if not part_number:
                    return {
                        "response": "❌ Could not identify a part number in your query. Please provide the part number you want to check.",
                        "status": "error"
                    }

                # Find product URL for the model
                product_url = self.find_product_url_by_model(model_number)
                if not product_url:
                    return {
                        "response": f"❌ Could not find information for model number {model_number}.",
                        "status": "error"
                    }

                # Scrape compatibility data
                scraped_data = scrape_partselect(product_url, headless=False)

                # Index the scraped data
                if scraped_data:
                    index_status = index_scraped_data(json.dumps(scraped_data))
                    logger.info(f"Indexed new scraped data: {index_status}")

                    # Now perform semantic search
                    vector_results = semantic_search_with_intent(query, intent, model_number)
                    logger.info(f"Vector search completed with {len(vector_results) if isinstance(vector_results, list) else 0} results")

                messages = [
                    SystemMessage(content=(
                        "You are a helpful appliance repair assistant. Create a concise response about part compatibility. "
                        "Format your response using these guidelines:\n\n"
                        "#### Compatibility Summary\n"
                        "- Start with a clear yes/no statement\n"
                        "- Keep it brief and direct\n\n"
                        "#### Part Details\n"
                        "- Part name and number\n"
                        "- Basic specifications\n\n"
                        "#### Notes\n"
                        "- Important compatibility details\n"
                        "- Installation considerations\n\n"
                        "Use:\n"
                        "- '#### ' for section headers (smaller headers)\n"
                        "- Bullet points for lists\n"
                        "- Brief, clear sentences\n"
                        "- No large headers\n"
                        "Keep the entire response concise and well-organized."
                    )),
                    HumanMessage(content=(
                        f"Query: {query}\n"
                        f"Model Number: {model_number}\n"
                        f"Part Number: {part_number}\n"
                        f"Compatibility Data: {json.dumps(scraped_data, indent=2)}"
                    ))
                ]
                
                response = self.llm.invoke(messages)
                return {
                    "response": response.content,
                    "status": "success"
                }

            else:
                return {"response": "❌ I'm not sure how to help with that. Please try asking about troubleshooting an issue, installing a part, or checking compatibility.", "status": "error"}

        except Exception as e:
            logger.exception(f"❌ Error in process_query: {e}")
            return {
                "response": f"Error: {str(e)}",
                "status": "error"
            }

    def extract_part_number(self, query: str) -> str:
        """
        Extracts part number from the query using GPT.
        """
        messages = [
            SystemMessage(content="Extract the part number from the query. Return only the part number or 'None' if not found."),
            HumanMessage(content=query)
        ]
        try:
            response = self.llm.invoke(messages)
            part_number = response.content.strip()
            return None if part_number.lower() == 'none' else part_number
        except Exception as e:
            logger.exception(f"❌ Error extracting part number: {e}")
            return None

    def scrape_and_process(self, product_url: str) -> dict:
        """
        Scrapes the product page and indexes the data.
        """
        try:
            scraped_data = scrape_partselect(product_url, headless=False)
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
        messages = [
            SystemMessage(content="Extract the appliance brand name from the query. Return only the brand name or 'None' if not found."),
            HumanMessage(content=query)
        ]
        try:
            response = self.llm.invoke(messages)
            brand = response.content.strip()
            return None if brand.lower() == 'none' else brand
        except Exception as e:
            logger.exception(f"❌ Error extracting brand: {e}")
            return None


# Instantiate Agent Manager
appliance_agent = ApplianceAgent()