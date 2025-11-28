# gpt_handler.py
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_with_gpt(messages, model="gpt-4", temperature=0.7):
    """
    Send a conversation to GPT-4. 
    messages: list of {"role": "system"/"user"/"assistant", "content": "..."}
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"GPT error: {str(e)}"