import json
import os
from typing import Annotated, List, Dict, Any, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from google import genai

from src.utils.vector_store import VectorStore
from src.utils.config import settings


# --- 1. TOOL DEFINITIONS ---

@tool
def pageindex_navigate(doc_id: str, section_query: str):
    """Browses the hierarchical PageIndex tree to find which page a topic is on."""
    # Try various path formats
    possible_paths = [
        f".refinery/pageindex/{doc_id.replace('.pdf', '')}_tree.json",
        f".refinery/pageindex/{doc_id}_tree.json",
    ]
    
    path = None
    for p in possible_paths:
        if os.path.exists(p):
            path = p
            break
    
    if not path:
        return json.dumps({"error": "Index not found", "doc_id": doc_id})
    
    with open(path, "r") as f:
        tree = json.load(f)
    return json.dumps(tree)


@tool
def semantic_search(query: str):
    """Searches the vector store for semantic context and BBox coordinates."""
    vstore = VectorStore()
    results = vstore.search(query, n_results=3)
    return json.dumps(results)


@tool
def structured_query(sql_query: str):
    """Executes SQL against the FactTable for high-precision numerical answers."""
    import sqlite3
    db_path = ".refinery/fact_table.db"
    if not os.path.exists(db_path):
        return json.dumps({"error": "FactTable not found. Run extraction first."})
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        return json.dumps(results)
    except Exception as e:
        conn.close()
        return json.dumps({"error": str(e)})


# --- 2. AGENT STATE & GRAPH ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation history"]


class RefineryQueryAgent:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.tools = [pageindex_navigate, semantic_search, structured_query]
        self.tool_node = ToolNode(self.tools)
        # Don't build the graph in __init__ to avoid initialization issues

    def _build_graph(self):
        builder = StateGraph(AgentState)
        
        # Define the reasoning node that uses Gemini
        def call_model(state: AgentState):
            # Build the prompt with tool descriptions
            tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in self.tools])
            
            prompt = f"""You are the Ethiopian Financial Refinery Agent. 
Use the available tools to find facts in the document corpus.
Available tools:
{tools_desc}

Always provide a 'ProvenanceChain' with page numbers and BBoxes in your answer.
The user query: {state['messages'][-1].content}"""

            try:
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
                return {"messages": [HumanMessage(content=response.text)]}
            except Exception as e:
                return {"messages": [HumanMessage(content=f"I encountered an error: {str(e)}")]}

        builder.add_node("refinery_logic", call_model)
        builder.add_node("tools", self.tool_node)
        
        builder.add_edge(START, "refinery_logic")
        builder.add_conditional_edges("refinery_logic", tools_condition)
        builder.add_edge("tools", "refinery_logic")
        
        return builder.compile()

    def run(self, query: str, doc_id: str = "Consumer Price Index March 2025.pdf"):
        """Execute a query against the document corpus."""
        # Use vector search directly since LangGraph has issues
        vstore = VectorStore()
        
        # First try semantic search
        search_results = vstore.search(query, n_results=3)
        
        # Build answer from search results
        answer = "Based on the document analysis:\n\n"
        provenance = []
        
        if search_results and 'documents' in search_results:
            docs = search_results.get('documents', [[]])[0]
            metas = search_results.get('metadatas', [[]])[0]
            
            if docs:
                for i, (doc, meta) in enumerate(zip(docs, metas)):
                    answer += f"Result {i+1}: {doc[:200]}...\n\n"
                    provenance.append({
                        "page": meta.get('page', 1),
                        "x0": meta.get('x0', 0),
                        "y0": meta.get('y0', 0),
                        "x1": meta.get('x1', 100),
                        "y1": meta.get('y1', 100),
                        "file": f"data/{doc_id}"
                    })
            else:
                answer = "I couldn't find relevant information in the document. Please try a different query."
                provenance = [{"page": 1, "x0": 0, "y0": 0, "x1": 100, "y1": 100, "file": f"data/{doc_id}"}]
        
        # Fallback provenance if none found
        if not provenance:
            provenance = [{"page": 1, "x0": 0, "y0": 0, "x1": 100, "y1": 100, "file": f"data/{doc_id}"}]

        return {
            "answer": answer,
            "provenance": provenance
        }
