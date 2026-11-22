from typing import Dict, Any, List
from app.data_ingestion.vector_store import vector_store

class SemanticKnowledgeAgent:
    def __init__(self, name: str = "Semantic Knowledge & Document Retrieval Agent"):
        self.name = name
        self.role = "Unstructured Intelligence & Semantic Retrieval Specialist"
        self.goal = "Retrieve high-confidence document chunks across contracts, Confluence wikis, PDFs, spreadsheets, and emails from the Pinecone vector index."

    def search_knowledge(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        results = vector_store.search(query=query, top_k=top_k)

        citations = []
        for r in results:
            citations.append({
                "chunk_id": r.chunk_id,
                "relevance_score": r.score,
                "title": r.title,
                "source_type": r.source_type,
                "excerpt": r.content[:350] + ("..." if len(r.content) > 350 else ""),
                "full_content": r.content,
                "metadata": r.metadata
            })

        return {
            "agent": self.name,
            "status": "COMPLETED",
            "query": query,
            "top_k": top_k,
            "citations_found": len(citations),
            "citations": citations,
            "highest_similarity": citations[0]["relevance_score"] if citations else 0.0
        }

vector_agent = SemanticKnowledgeAgent()

