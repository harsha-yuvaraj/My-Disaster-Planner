from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, START, END 
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os 
import json

# Configuration
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
PDF_PATH = r"C:\Users\Fares\Downloads\disaster_preparedness_9_16_2022.pdf"
JSON_PATH = r"C:\Users\Fares\Downloads\FLORIDA_CEMW.json"  # Add your JSON file path
PERSIST_DIRECTORY = r"C:\Users\Fares\Downloads\lang_embed"
COLLECTION_NAME = "disaster_preparedness"

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# Verify files exist
if not os.path.exists(PDF_PATH):
    raise FileNotFoundError(f"PDF file not found: {PDF_PATH}")

if not os.path.exists(JSON_PATH):
    raise FileNotFoundError(f"JSON file not found: {JSON_PATH}")

# Load and process PDF
try:
    print("Loading PDF...")
    pdf_loader = PyPDFLoader(PDF_PATH)
    pdf_pages = pdf_loader.load()
    print(f"Loaded PDF with {len(pdf_pages)} pages")
except Exception as e:
    print(f"Error processing PDF: {e}")
    raise

# Load and process JSON
def load_florida_counties_json(json_path: str) -> list[Document]:
    """Load Florida county emergency management data from JSON and convert to documents"""
    try:
        print("Loading Florida counties JSON...")
        with open(json_path, 'r', encoding='utf-8') as f:
            counties_data = json.load(f)
        
        documents = []
        for county, url in counties_data.items():
            # Create comprehensive content for each county
            content = f"""
County: {county} County, Florida
Emergency Management Website: {url}
Type: County Emergency Management Office
State: Florida
Purpose: Disaster preparedness, emergency response, and emergency management services for {county} County residents.
Contact Information: Visit {url} for emergency management resources, contact details, and local preparedness information.
Services: Emergency planning, disaster response coordination, public safety alerts, evacuation information, shelter locations, and community preparedness resources.
            """.strip()
            
            # Create document with metadata
            doc = Document(
                page_content=content,
                metadata={
                    "source": json_path,
                    "county": county,
                    "state": "Florida",
                    "url": url,
                    "type": "emergency_management",
                    "document_type": "county_directory"
                }
            )
            documents.append(doc)
        
        print(f"Created {len(documents)} county emergency management documents")
        return documents
        
    except Exception as e:
        print(f"Error processing JSON: {e}")
        raise

# Load JSON data
json_documents = load_florida_counties_json(JSON_PATH)

# Combine all documents
try:
    print("Combining all documents...")
    all_documents = pdf_pages + json_documents
    print(f"Total documents before splitting: {len(all_documents)} (PDF: {len(pdf_pages)}, Counties: {len(json_documents)})")
    
    # Split text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Split PDF pages
    pdf_chunks = text_splitter.split_documents(pdf_pages)
    
    # For county data, we'll use smaller chunks to keep county info together
    county_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    county_chunks = county_splitter.split_documents(json_documents)
    
    # Combine all chunks
    all_chunks = pdf_chunks + county_chunks
    print(f"Total document chunks: {len(all_chunks)} (PDF chunks: {len(pdf_chunks)}, County chunks: {len(county_chunks)})")
    
except Exception as e:
    print(f"Error splitting documents: {e}")
    raise

# Setup ChromaDB vector store
try:
    print("Creating vector store...")
    if not os.path.exists(PERSIST_DIRECTORY):
        os.makedirs(PERSIST_DIRECTORY)
    
    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY,
        collection_name=COLLECTION_NAME
    )
    print("Vector store created successfully!")
except Exception as e:
    print(f"Error creating vector store: {e}")
    raise

# Create retriever
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 7}  # Increased to get more diverse results
)

@tool
def retriever_tool(query: str) -> str:
    '''Search disaster preparedness guide and Florida county emergency management resources for dementia caregivers'''
    try:
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant information found."
        
        # Group results by source type
        pdf_results = []
        county_results = []
        
        for i, doc in enumerate(docs):
            doc_type = doc.metadata.get('document_type', 'pdf')
            content = f"Document {i+1}:\n{doc.page_content}"
            
            if doc_type == 'county_directory':
                county_results.append(content)
            else:
                pdf_results.append(content)
        
        # Combine results with clear sections
        result = ""
        if pdf_results:
            result += "=== DISASTER PREPAREDNESS GUIDE ===\n\n"
            result += "\n\n".join(pdf_results)
        
        if county_results:
            if result:
                result += "\n\n"
            result += "=== FLORIDA COUNTY EMERGENCY MANAGEMENT ===\n\n"
            result += "\n\n".join(county_results)
        
        return result
        
    except Exception as e:
        return f"Retrieval error: {str(e)}"

tools = [retriever_tool]

# Initialize LLM with fallbacks
llm = None
llm_name = "None"

# Option 1: Try Ollama first
try:
    from langchain_community.chat_models import ChatOllama
    llm = ChatOllama(model="llama3", temperature=0.1).bind_tools(tools)
    llm_name = "Ollama (llama3)"
    print("✅ Ollama LLM initialized successfully!")
except Exception as e:
    print(f"❌ Ollama failed: {e}")

# Option 2: Try HuggingFace
if llm is None:
    try:
        from langchain_huggingface import ChatHuggingFace
        from huggingface_hub import InferenceClient
        client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.1")
        llm = ChatHuggingFace(client=client).bind_tools(tools)
        llm_name = "HuggingFace (Mistral-7B)"
        print("✅ HuggingFace LLM initialized successfully!")
    except Exception as e:
        print(f"❌ HuggingFace failed: {e}")

# State definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Enhanced system prompt
system_prompt = """You are an expert AI assistant for disaster preparedness for dementia caregivers in Florida. 
You have access to:
1. A comprehensive disaster preparedness guide for dementia caregivers
2. Florida county emergency management contact information and websites

Provide specific advice on:
- Emergency planning for dementia patients
- Communication strategies during emergencies
- Safety measures and protocols
- Emergency supply checklists
- Local emergency management resources by county
- Evacuation procedures for vulnerable populations

When providing county-specific information, always include the emergency management website URL for direct contact.
Use the retriever_tool when you need information from either the guide or county emergency resources."""

def should_continue(state: AgentState):
    """Determine if we should call tools or end"""
    last_msg = state['messages'][-1]
    return hasattr(last_msg, 'tool_calls') and bool(last_msg.tool_calls)

def call_llm(state: AgentState) -> AgentState:
    """Generate response or tool calls"""
    try:
        messages = [SystemMessage(content=system_prompt)] + list(state['messages'])
        
        if llm is None:
            # Direct retrieval fallback
            query = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")
            docs = retriever.invoke(query)
            context = "\n".join(doc.page_content[:500] for doc in docs[:3])
            return {'messages': [AIMessage(content=f"From the resources:\n\n{context}")]}
        
        response = llm.invoke(messages)
        return {'messages': [response]}
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return {'messages': [AIMessage(content="I'm having technical difficulties. Please try again.")]}

def take_action(state: AgentState) -> AgentState:
    """Execute tool calls"""
    try:
        tool_calls = state['messages'][-1].tool_calls
        results = []
        
        for t in tool_calls:
            if t['name'] == "retriever_tool":
                result = retriever_tool.invoke(t['args']['query'])
                results.append(ToolMessage(
                    tool_call_id=t['id'],
                    name=t['name'],
                    content=str(result)
                ))
        
        return {'messages': results}
    except Exception as e:
        print(f"Tool Error: {e}")
        return {'messages': [AIMessage(content="Tool execution failed.")]}

# Build the graph
graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("action", take_action)

graph.add_conditional_edges(
    "llm",
    should_continue,
    {True: "action", False: END}
)
graph.add_edge("action", "llm")
graph.set_entry_point("llm")

rag_agent = graph.compile()

# Enhanced test functions
def test_retriever():
    print("\nTesting retriever...")
    queries = [
        "hurricane preparation dementia",
        "emergency kit supplies",
        "evacuation planning vulnerable adults",
        "Hillsborough County emergency management",
        "Miami-Dade emergency contacts",
        "Pinellas County disaster preparedness"
    ]
    for q in queries:
        print(f"\n--- Query: '{q}' ---")
        docs = retriever.invoke(q)
        print(f"Found {len(docs)} documents")
        for i, doc in enumerate(docs[:2]):
            doc_type = doc.metadata.get('document_type', 'guide')
            county = doc.metadata.get('county', 'N/A')
            print(f"[Doc {i+1} - {doc_type}] County: {county}")
            print(f"Content: {doc.page_content[:150]}...")

def test_county_search():
    print("\nTesting county-specific searches...")
    test_counties = ["Hillsborough", "Miami-Dade", "Orange", "Pinellas", "Duval"]
    
    for county in test_counties:
        docs = retriever.invoke(f"{county} county emergency management")
        county_docs = [d for d in docs if d.metadata.get('county') == county]
        print(f"\n{county} County: Found {len(county_docs)} specific documents")
        if county_docs:
            doc = county_docs[0]
            print(f"URL: {doc.metadata.get('url', 'N/A')}")

def test_llm():
    if llm is None:
        print("\nNo LLM available for testing")
        return
        
    print("\nTesting LLM...")
    tests = [
        ("What should be in an emergency kit for dementia patients?", "general preparedness"),
        ("How do I contact emergency management in Tampa?", "location-specific"),
        ("What's the emergency website for Broward County?", "county lookup")
    ]
    
    for question, test_type in tests:
        print(f"\nTest '{test_type}': {question}")
        try:
            response = llm.invoke([HumanMessage(content=question)])
            print("Response:", response.content[:200] + "...")
            if hasattr(response, 'tool_calls'):
                print("Tool calls:", [t['name'] for t in response.tool_calls])
        except Exception as e:
            print(f"Error: {e}")

def run_agent():
    print(f"\n=== FLORIDA DISASTER PREPAREDNESS AGENT (using {llm_name}) ===")
    print("Ask about disaster preparedness for dementia caregivers or Florida county emergency management!")
    print("Example questions:")
    print("- 'What should I include in an emergency kit for my loved one with dementia?'")
    print("- 'How do I contact emergency management in Orange County?'")
    print("- 'What's the evacuation process for dementia patients?'")
    print("\nType 'exit' to quit\n")
    
    while True:
        try:
            query = input("Your question: ").strip()
            if query.lower() in ['exit', 'quit']:
                break
            if not query:
                continue
                
            result = rag_agent.invoke({"messages": [HumanMessage(content=query)]})
            print("\nResponse:", result['messages'][-1].content, "\n")
            print("-" * 80)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_retriever()
    test_county_search()
    test_llm()
    run_agent()
