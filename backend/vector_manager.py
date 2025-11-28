# vector_manager.py - Using Google Gemini Embeddings

import os
import json
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from google_search import google_partselect_search
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - VectorManager - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("vector_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VectorManager")


class LivePartSelectMemory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LivePartSelectMemory, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        """
        Initializes the embedding model and vector store using Google's free embeddings
        """
        # Use Google's free embedding model
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )

        # Initialize Chroma without persistence
        self.vector_store = Chroma(
            embedding_function=self.embedding_model,
            collection_name="partselect_data"
        )

        logger.info("✅ LivePartSelectMemory initialized with Google Gemini embeddings.")

    def live_search_and_index(self, query: str, k=3):
        """
        1) Perform a live Google search for the query (restricted to PartSelect).
        2) Extract snippets & links.
        3) Convert them into Document objects and store them in the vector store.
        4) Returns a confirmation message.
        """
        results = google_partselect_search(query, num_results=k)
        if not results:
            logger.warning(f"No search results found for: {query}")
            return "No results found on PartSelect for that query."

        documents = []
        for snippet, link in results:
            combined_text = f"Snippet: {snippet}\nURL: {link}"

            if combined_text.strip():
                doc = Document(page_content=combined_text, metadata={"source": link})
                documents.append(doc)

        if not documents:
            logger.warning("No valid documents found to index.")
            return "No valid data found to index."

        try:
            self.vector_store.add_documents(documents)
            logger.info(f"✅ Live indexed {len(documents)} new items from PartSelect.")
            return f"Live indexed {len(documents)} new items from PartSelect."
        except Exception as e:
            logger.exception(f"Error during indexing: {e}")
            return "Error: Unable to index data."

    def semantic_search_with_intent(self, query: str, intent: str, model_number: str = None, top_k: int = 3):
        """
        Performs semantic search based on the query and intent.
        """
        filter_metadata = {}
        if intent == 'troubleshoot':
            filter_metadata = {"type": {"$eq": "user_story"}}
            if model_number:
                filter_metadata["model"] = {"$eq": model_number}
        elif intent == 'installation':
            filter_metadata = {"type": {"$eq": "installation_guides"}}
            if model_number:
                filter_metadata["model"] = {"$eq": model_number}
        elif intent == 'compatibility':
            filter_metadata = {"type": {"$eq": "model_compatibility"}}
        elif intent == 'qna':
            filter_metadata = {"type": {"$eq": "qna"}}
        else:
            filter_metadata = {}

        logger.debug(f"Performing semantic search with query: '{query}', intent: '{intent}', model: '{model_number}'")

        try:
            results = self.vector_store.similarity_search(query, k=top_k, filter=filter_metadata)
            logger.debug(f"Semantic search results: {results}")

            if not results:
                logger.warning(f"No relevant results found for query: '{query}'")
                return ["No relevant results found for this intent."]

            formatted_results = []
            for doc in results:
                metadata = doc.metadata
                if "title" in metadata and "instruction" in metadata:
                    formatted_results.append({
                        "title": metadata['title'],
                        "instruction": metadata['instruction'],
                        "source": metadata.get('source')
                    })
                elif "part_name" in metadata:
                    formatted_results.append({
                        "part_name": metadata['part_name'],
                        "source": metadata.get('source')
                    })
                else:
                    formatted_results.append({
                        "title": metadata.get('title', 'No Title'),
                        "instruction": metadata.get('instruction', ''),
                        "source": metadata.get('source')
                    })

            logger.info(f"✅ Semantic search returned {len(formatted_results)} results for intent '{intent}'.")
            return formatted_results

        except Exception as e:
            logger.exception(f"❌ Semantic search failed: {e}")
            return ["Error occurred during semantic search."]


# Instantiate live_store with Singleton pattern
live_store = LivePartSelectMemory()


def index_scraped_data(json_str: str) -> str:
    """
    Parses JSON data from the scraper and indexes relevant sections into the vector store.
    """
    logger.info(f"Indexing data: {json_str[:200]}...")
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON input.")
        return "❌ Invalid JSON input."

    documents = []

    # Q&A Document Tagging
    qna_list = data.get("qna", [])
    if isinstance(qna_list, list):
        for pair in qna_list:
            if isinstance(pair, dict):
                question = pair.get("question", "").strip()
                answer = pair.get("answer", "").strip()
                if question and answer:
                    content = f"Q: {question}\nA: {answer}"
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={
                                "type": "qna",
                                "source": "scraped_json"
                            }
                        )
                    )

    # Troubleshooting Document Tagging
    troubleshooting_info = data.get("troubleshooting_info", {})
    if isinstance(troubleshooting_info, dict):
        symptoms = troubleshooting_info.get("symptoms", [])
        if symptoms:
            content = f"Symptoms: {', '.join(symptoms)}"
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "type": "troubleshooting_symptoms",
                        "source": "scraped_json"
                    }
                )
            )

        products = troubleshooting_info.get("products", [])
        if products:
            content = f"Products: {', '.join(products)}"
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "type": "troubleshooting_products",
                        "source": "scraped_json"
                    }
                )
            )

        replacements = troubleshooting_info.get("replacements", [])
        if replacements:
            content = f"Replacements: {', '.join(replacements)}"
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "type": "troubleshooting_replacements",
                        "source": "scraped_json"
                    }
                )
            )

    # Model Compatibility Document Tagging
    model_compatibility = data.get("model_compatibility", [])
    if isinstance(model_compatibility, list):
        for model in model_compatibility:
            if isinstance(model, dict):
                brand = model.get("brand", "").strip()
                model_number = model.get("model_number", "").strip()
                description = model.get("description", "").strip()
                if brand and model_number and description:
                    content = f"Brand: {brand}\nModel Number: {model_number}\nDescription: {description}"
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={
                                "type": "model_compatibility",
                                "source": "scraped_json"
                            }
                        )
                    )

    # Installation Document Tagging
    installation_info = data.get("installation_info", "").strip()
    if installation_info and installation_info != "No installation information available.":
        documents.append(
            Document(
                page_content=installation_info,
                metadata={
                    "type": "installation_guides",
                    "source": "scraped_json"
                }
            )
        )

    # Data Segmentation (Chunking)
    def split_into_chunks(text, chunk_size=500):
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    if 'full_description' in data:
        desc_chunks = split_into_chunks(data['full_description'], chunk_size=500)
        for chunk in desc_chunks:
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "type": "full_description",
                        "source": "scraped_json"
                    }
                )
            )

    # Symptom Information Tagging
    for part in data.get("common_parts", []):
        content = f"Part: {part['part_name']}\nFix Percentage: {part['fix_percentage']}%\nPrice: ${part['price']}\nDescription: {part['description']}"
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "type": "part_info",
                    "model": data.get("model_number", ""),
                    "source": "scraped_json"
                }
            )
        )

        for story in part.get("user_stories", []):
            content = f"Title: {story['title']}\nInstruction: {story['instruction']}"
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "type": "user_story",
                        "model": data.get("model_number", ""),
                        "source": "scraped_json"
                    }
                )
            )

    if not documents:
        logger.error("❌ No valid documents found to index.")
        return "❌ No valid documents found to index."

    try:
        live_store.vector_store.add_documents(documents)
        logger.info(f"✅ Indexed {len(documents)} documents from scraped data.")
        return f"✅ Indexed {len(documents)} documents from scraped data."
    except Exception as e:
        logger.exception(f"❌ Error during indexing: {e}")
        return "❌ Failed to index scraped data."


def semantic_search_with_intent(query: str, intent: str, model_number: str = None, top_k: int = 3):
    """
    Performs semantic search based on the query and intent.
    """
    return live_store.semantic_search_with_intent(query, intent, model_number, top_k)