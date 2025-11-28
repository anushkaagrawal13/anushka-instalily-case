# agents.py
#playground code for testing
import json
import logging
from langchain.schema import HumanMessage, SystemMessage
from agent_manager import AgentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - Agent - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agents.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Agent")

# Initialize the Agent Manager
agent_manager = AgentManager()

# ============================
# 1. Define Tools
# ============================

def gpt_tool(query: str) -> str:
    """
    Utilizes GPT to generate responses when necessary.
    """
    messages = [
        SystemMessage(content=(
            "You are a helpful chatbot specialized in PartSelect queries for "
            "refrigerator and dishwasher parts. Use the provided data or your training knowledge, "
            "but remain within that domain. If not relevant to parts, politely decline."
        )),
        HumanMessage(content=query)
    ]
    try:
        response = agent_manager.llm.invoke(messages)  # Use invoke instead of __call__
        return response.content.strip()  # Access content directly
    except Exception as e:
        logger.exception(f"❌ GPT tool encountered an error: {e}")
        return "❌ Failed to generate response using GPT."

# ============================
# 2. Formatting Functions
# ============================

def format_response(data: dict, intent: str, original_query: str, session: dict) -> str:
    """
    Summarizes `scraped_data` for GPT: includes instructions, user stories, and overall context.
    """
    if "scraped_data" in data:
        scraped_data = data["scraped_data"]

        #build a single dict for GPT containing:
        # - The original user query
        # - The relevant instructions from user stories
        # - Possibly the part's official description
        # - The highest fix_percentage part name
        # - The product link if available
        final_context = {
            "user_query": original_query,
            "intent": intent,
            "model_number": scraped_data.get("model_number", ""),
            "symptom_title": scraped_data.get("symptom_title", ""),
            "troubleshoot_instructions": scraped_data.get("troubleshoot_instructions", []),
            "highest_fix_part_description": "",
            "product_link": scraped_data.get("product_url", ""),
            "highest_fix_part_name": "",
            "fix_percentage": ""
        }

        # If common_parts exist, show the top part's description:
        parts = scraped_data.get("common_parts", [])
        if parts:
            top_part = parts[0]
            final_context["highest_fix_part_description"] = top_part.get("description", "")
            final_context["highest_fix_part_name"] = top_part.get("part_name", "")
            final_context["fix_percentage"] = top_part.get("fix_percentage", "")

        # Prepare the system prompt with conversation history for multi-turn
        history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in session.get('history', [])])

        gpt_prompt = (
            "You are a specialized assistant for refrigerator and dishwasher part issues. "
            "Use the data below to answer the user's question accurately.\n\n"
            f"Conversation history:\n{history}\n\n"
            "Structured Data:\n"
            + json.dumps(final_context, indent=2)
            + "\n\nPlease compose a helpful, concise, markdown-formatted answer focusing on the user's question and the relevant instructions."
        )

        formatted_response = gpt_tool(gpt_prompt)

        # Append product URL at the end of the response
        if final_context["product_link"]:
            formatted_response += f"\n\n🔗 **[View Product on PartSelect]({final_context['product_link']})**"

        return formatted_response

    elif "search_results" in data:
        # Summarize search results if needed
        return gpt_tool("Summarize these search results:\n" + json.dumps(data["search_results"]))
    elif "clarifying_question" in data:
        # Return the clarifying question directly
        return data["clarifying_question"]
    else:
        return "❌ No relevant information found to generate a response."

# ============================
# 3. Main Agent Function
# ============================

def plan_and_execute_agent(query: str, session: dict) -> dict:
    """
    Main agent function handling user queries.
    Delegates tasks to the Agent Manager and processes responses.
    Maintains session context for multi-turn conversations.
    """
    try:
        logger.info(f"🧐 Processing query: {query}")
        processed_data = agent_manager.handle_query(query, session)

        if "clarifying_question" in processed_data:
            return {"clarifying_question": processed_data["clarifying_question"]}

        # Detect intent using GPT
        intent = agent_manager.detect_intent(query)

        # Format the response based on processed data and intent
        formatted_response = format_response(processed_data, intent, query, session)

        return {"response": formatted_response}

    except Exception as e:
        logger.exception(f"🚨 Agent encountered an error: {e}")
        return {"response": f"❌ Agent error: {str(e)}"}

# ============================
# 4. Execution (For Testing)
# ============================

if __name__ == "__main__":
    # Example query with a mock session
    test_query = "My Whirlpool fridge model WRS588FIHZ00 is not making ice. What's wrong?"
    mock_session = {
        "history": [
            {"role": "user", "content": test_query}
        ]
    }
    response = plan_and_execute_agent(test_query, mock_session)
    print("\n🔍 **Agent Response:**")
    print(response)