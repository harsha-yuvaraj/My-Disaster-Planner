import os
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
# === NEW IMPORTS for the modern chat engine approach ===
from llama_index.core.prompts import ChatPromptTemplate
from llama_index.core.llms import ChatMessage, MessageRole

def initialize_ai_services(app):
    """
    Initializes all AI-related services, including the LlamaIndex query engine.
    This function is called once when the Flask app is created.
    """
    print("Initializing AI services...")
    
    # --- Configuration ---
    api_key = app.config.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not configured. AI services will be disabled.")
        return None

    # --- Build dynamic and absolute paths ---
    app_root = app.root_path 
    data_dir = os.path.join(app_root, 'data')
    index_dir = os.path.join(app_root, 'index_store')

    # --- Setup LLM and LlamaIndex Settings ---
    model_name = app.config.get('LLM_MODEL', 'gpt-4o')
    Settings.llm = OpenAI(model=model_name, api_key=api_key, temperature=0.1, max_tokens=300)
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
    Settings.embed_model = "local:BAAI/bge-small-en-v1.5"

    # --- Build or Load the Vector Index ---
    if not os.path.exists(index_dir):
        print(f"Index not found. Building index from documents in {data_dir}...")
        try:
            reader = SimpleDirectoryReader(data_dir, recursive=True)
            docs = reader.load_data()
            index = VectorStoreIndex.from_documents(docs)
            index.storage_context.persist(persist_dir=index_dir)
            print("Index built and persisted successfully.")
        except Exception as e:
            print(f"Error building the index: {e}")
            return None
    else:
        print(f"Loading existing index from {index_dir}...")
        try:
            storage_context = StorageContext.from_defaults(persist_dir=index_dir)
            index = load_index_from_storage(storage_context)
            print("Index loaded successfully.")
        except Exception as e:
            print(f"Error loading the index: {e}")
            return None

    # --- System Prompt ---
    system_prompt = (
        "You are the AI Disaster Prep Assistant for My Disaster Planner, a web application that helps anyone "
        "(but is especially tailored for older adults and their caregivers in Florida) create a comprehensive, "
        "personalized emergency or disaster preparedness plan. "
        "Your role is to provide clear, actionable tips and information about disaster preparedness, guide users "
        "through creating robust preparedness plans, and deliver your responses in a reassuring, friendly, and calm tone. "
        "If a user asks about anything outside disaster preparedness, politely decline and steer them back to emergency or disaster planning. "
        "Keep your response concise - under 250 tokens and return response in markdown if needed."
    )
    
    # The modern way to create a chat engine with a system prompt and conversation history
    chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context",
        system_prompt=system_prompt,
        similarity_top_k=3
    )
    # ================================

    # The function now returns the chat_engine
    return chat_engine
