# agent_manager.py - Using Google Gemini Free Tier
import os
import re
import json
import logging
import google.generativeai as genai
from vector_manager import live_store, index_scraped_data
from partselect_scraper import scrape_part_details
from symptom_scraper import scrape_symptom_page
from google_search import google_partselect_search

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

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')


class AgentManager:
    """
    Manages the agent workflow using Google Gemini Free Tier:
    1. Detects query intent
    2. Extracts entities (part numbers, model numbers)
    3. Routes to appropriate handler
    4. Generates structured response
    """
    
    def __init__(self):
        self.conversation_history = []
        # Define appliance scope
        self.ALLOWED_APPLIANCES = ['refrigerator', 'fridge', 'dishwasher', 'ice maker']
        
    def is_in_scope(self, query: str) -> bool:
        """Check if query is about refrigerators or dishwashers"""
        query_lower = query.lower()
        
        # Check for appliance keywords
        appliance_mentioned = any(appliance in query_lower for appliance in self.ALLOWED_APPLIANCES)
        
        # Check for part/model numbers (usually in scope)
        has_part_number = bool(re.search(r'(PS|W10|WP|AP|W11)\d+', query, re.IGNORECASE))
        has_model_number = bool(re.search(r'[A-Z]{2,}\d{3,}', query))
        
        return appliance_mentioned or has_part_number or has_model_number
    
    def detect_intent(self, query: str) -> dict:
        """
        Uses Gemini to detect user intent and extract entities
        Returns: {
            'intent': str,
            'part_number': str,
            'model_number': str,
            'symptom': str,
            'appliance_type': str
        }
        """
        logger.info(f"Detecting intent for query: {query}")
        
        prompt = f"""You are an intent classifier for a PartSelect chatbot specializing in Refrigerator and Dishwasher parts.

Analyze this user query and return a JSON response with:
1. intent: one of [installation, compatibility, troubleshooting, product_search, part_info, general, out_of_scope]
2. part_number: extract any part number (format: PS####, W10####, etc.) or null
3. model_number: extract any model number or null
4. symptom: extract the problem description for troubleshooting or null
5. appliance_type: refrigerator or dishwasher or null

Query: "{query}"

Return ONLY valid JSON, no markdown or explanation.

Example output:
{{"intent": "installation", "part_number": "PS11752778", "model_number": null, "symptom": null, "appliance_type": "dishwasher"}}"""

        try:
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            logger.info(f"Intent detected: {result}")
            return result
            
        except Exception as e:
            logger.exception(f"Intent detection failed: {e}")
            return {
                "intent": "general",
                "part_number": None,
                "model_number": None,
                "symptom": None,
                "appliance_type": None
            }
    
    def handle_installation_query(self, part_number: str, query: str) -> dict:
        """Handle installation-related queries"""
        logger.info(f"Handling installation query for part: {part_number}")
        
        try:
            # Try to scrape installation info
            part_url = f"https://www.partselect.com/PS{part_number.replace('PS', '')}.htm"
            scraped_data = scrape_part_details(part_url)
            
            if scraped_data:
                # Index the data
                index_scraped_data(json.dumps(scraped_data))
                
                # Search for installation instructions
                installation_results = live_store.semantic_search_with_intent(
                    query=f"how to install {part_number}",
                    intent="installation",
                    top_k=3
                )
                
                # Generate response
                response = self._generate_installation_response(
                    part_number, 
                    scraped_data, 
                    installation_results
                )
                
                return {
                    "response": response,
                    "part_info": {
                        "part_number": part_number,
                        "name": scraped_data.get("part_name", ""),
                        "price": scraped_data.get("price", ""),
                        "url": part_url
                    }
                }
        except Exception as e:
            logger.exception(f"Installation query failed: {e}")
        
        return {
            "response": f"I'll help you install part {part_number}. Let me search for instructions...",
            "part_info": {"part_number": part_number}
        }
    
    def handle_compatibility_query(self, part_number: str, model_number: str, query: str) -> dict:
        """Handle compatibility checks"""
        logger.info(f"Checking compatibility: Part {part_number} with Model {model_number}")
        
        try:
            # Search PartSelect for compatibility
            search_query = f"part {part_number} compatible {model_number}"
            search_results = google_partselect_search(search_query, num_results=5)
            
            # Index search results
            if search_results:
                live_store.live_search_and_index(search_query, k=5)
            
            # Semantic search for compatibility info
            compat_results = live_store.semantic_search_with_intent(
                query=f"{part_number} compatible with {model_number}",
                intent="compatibility",
                model_number=model_number,
                top_k=5
            )
            
            response = self._generate_compatibility_response(
                part_number,
                model_number,
                compat_results
            )
            
            return {"response": response}
            
        except Exception as e:
            logger.exception(f"Compatibility check failed: {e}")
            return {
                "response": f"Let me check if part {part_number} is compatible with model {model_number}..."
            }
    
    def handle_troubleshooting_query(self, symptom: str, appliance_type: str, model_number: str = None) -> dict:
        """Handle troubleshooting queries"""
        logger.info(f"Troubleshooting: {symptom} for {appliance_type}")
        
        try:
            # Search for symptom page
            search_query = f"{appliance_type} {symptom} parts fix"
            search_results = google_partselect_search(search_query, num_results=3)
            
            # Try to find and scrape symptom page
            symptom_url = None
            for snippet, url in search_results:
                if "symptom" in url.lower() or "repair" in url.lower():
                    symptom_url = url
                    break
            
            if symptom_url:
                symptom_data = scrape_symptom_page(symptom_url, model_number)
                if symptom_data:
                    index_scraped_data(json.dumps(symptom_data))
            
            # Semantic search for solutions
            troubleshoot_results = live_store.semantic_search_with_intent(
                query=symptom,
                intent="troubleshoot",
                model_number=model_number,
                top_k=5
            )
            
            response = self._generate_troubleshooting_response(
                symptom,
                appliance_type,
                troubleshoot_results
            )
            
            return {"response": response}
            
        except Exception as e:
            logger.exception(f"Troubleshooting failed: {e}")
            return {
                "response": f"I'll help you troubleshoot the {symptom} issue with your {appliance_type}."
            }
    
    def _generate_installation_response(self, part_number: str, scraped_data: dict, search_results: list) -> str:
        """Generate installation guide using Gemini"""
        
        context = f"""
Part Number: {part_number}
Part Name: {scraped_data.get('part_name', 'Unknown')}
Price: {scraped_data.get('price', 'N/A')}

Installation Information:
{scraped_data.get('installation_info', 'No specific instructions available')}

Related Information:
{json.dumps(search_results[:3], indent=2)}
"""
        
        prompt = f"""Generate a clear, step-by-step installation guide for this part.

{context}

Format as:
**Installation Guide for [Part Name] - Part #{part_number}**

**Tools Needed:**
• List tools

**Step-by-Step Instructions:**
1. Step one
2. Step two
...

**Estimated Time:** X minutes
**Difficulty:** Easy/Medium/Hard

Include safety warnings if relevant. Keep it concise and practical."""

        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.exception(f"Response generation failed: {e}")
            return f"Installation guide for part {part_number} will be available shortly."
    
    def _generate_compatibility_response(self, part_number: str, model_number: str, results: list) -> str:
        """Generate compatibility check response"""
        
        prompt = f"""Based on this compatibility data, provide a clear answer about whether part {part_number} 
is compatible with model {model_number}.

Data: {json.dumps(results, indent=2)}

Format as:
**Compatibility Check for Model {model_number}**

[Clear yes/no answer with explanation]

**Compatible Parts:**
• Part details with fix percentage
• Part details with fix percentage

Be concise but informative."""

        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.exception(f"Response generation failed: {e}")
            return f"Checking compatibility for part {part_number} with model {model_number}..."
    
    def _generate_troubleshooting_response(self, symptom: str, appliance_type: str, results: list) -> str:
        """Generate troubleshooting guide"""
        
        prompt = f"""Create a troubleshooting guide for this issue:

Appliance: {appliance_type}
Symptom: {symptom}

Data: {json.dumps(results, indent=2)}

Format as:
**Troubleshooting: {symptom} - {appliance_type}**

**Common Causes & Solutions:**
• Cause 1: Solution (likelihood: High/Medium/Low - X%)
• Cause 2: Solution
...

**Recommended Replacement Parts:**
• Part name (Part #) - $price - Fix rate: X%

Be specific and actionable."""

        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.exception(f"Response generation failed: {e}")
            return f"Troubleshooting guide for {symptom} issue..."
    
    def handle_query(self, query: str, session: dict) -> dict:
        """Main query handler"""
        logger.info(f"Handling query: {query}")
        
        # Check if query is in scope
        if not self.is_in_scope(query):
            return {
                "response": """I specialize in helping with **Refrigerator and Dishwasher parts only**. 

I can assist you with:
• Installation instructions for refrigerator/dishwasher parts
• Compatibility checks for your specific models
• Troubleshooting common issues
• Finding the right replacement parts

Please ask me about refrigerator or dishwasher parts!"""
            }
        
        # Detect intent
        intent_data = self.detect_intent(query)
        intent = intent_data.get("intent")
        
        # Route to appropriate handler
        if intent == "installation" and intent_data.get("part_number"):
            return self.handle_installation_query(intent_data["part_number"], query)
        
        elif intent == "compatibility":
            part_num = intent_data.get("part_number")
            model_num = intent_data.get("model_number")
            if part_num and model_num:
                return self.handle_compatibility_query(part_num, model_num, query)
        
        elif intent == "troubleshooting" and intent_data.get("symptom"):
            return self.handle_troubleshooting_query(
                intent_data["symptom"],
                intent_data.get("appliance_type", "appliance"),
                intent_data.get("model_number")
            )
        
        # Default general response
        return {
            "response": """I can help you with:

• **Installation**: "How do I install part PS11752778?"
• **Compatibility**: "Is part X compatible with model Y?"
• **Troubleshooting**: "My ice maker isn't working"
• **Product Search**: "Find dishwasher spray arm parts"

What would you like help with?"""
        }


# Singleton instance
agent_manager = AgentManager()