"""
RAG System for Nutritional Meal Planning with CrewAI
Implements the infrastructure schema for personalized meal planning considering type 2 diabetes
"""

import os
import json
import re
import math
import chromadb
from pathlib import Path
from collections import OrderedDict
from functools import lru_cache
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from .neo4j_client import Neo4jClient

# Load environment variables
load_dotenv()


def create_nutritional_rag_tool(vector_store, embedding_model, graph_client: Optional[Neo4jClient] = None):
    """
    Create a nutritional RAG tool that can be used with CrewAI agents.
    Returns a CrewAI BaseTool compatible tool.
    """
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field
    from typing import Type
    
    collection_name = "nutritional_data"
    initial_top_k = int(os.getenv("RAG_INITIAL_TOP_K", "20"))
    final_top_k = int(os.getenv("RAG_FINAL_TOP_K", "5"))
    cache_size = int(os.getenv("RAG_CACHE_SIZE", "128"))
    keyword_weight = float(os.getenv("RAG_KEYWORD_WEIGHT", "0.3"))
    embedding_weight = float(os.getenv("RAG_EMBEDDING_WEIGHT", "0.7"))

    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _tokenize(text: str) -> List[str]:
        if not text:
            return []
        return [
            token for token in re.split(r"[^a-zA-Z0-9áéíóúãõâêîôûç]+", text.lower())
            if token
        ]

    def _expand_query(query: str) -> str:
        tokens = set(_tokenize(query))
        expansions = []
        if not any(token.startswith("diabet") for token in tokens):
            expansions.append("diabetes tipo 2")
        if not any("glicem" in token for token in tokens):
            expansions.append("baixo indice glicemico")
        if not any("fibra" in token for token in tokens):
            expansions.append("rico em fibras")
        if not any("carb" in token for token in tokens):
            expansions.append("carboidratos complexos integral")
        if not expansions:
            return query
        return f"{query}. {'; '.join(expansions)}"

    def _keyword_score(query_tokens: List[str], text: str) -> float:
        if not query_tokens or not text:
            return 0.0
        text_tokens = set(_tokenize(text))
        overlap = len(set(query_tokens) & text_tokens)
        return overlap / max(len(set(query_tokens)), 1)

    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if a is None or b is None:
            return 0.0
        if len(a) == 0 or len(b) == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    @lru_cache(maxsize=256)
    def _cached_embed(text: str) -> List[float]:
        return embedding_model.encode(text).tolist()
    
    class NutritionalRAGSearchInput(BaseModel):
        """Input schema for nutritional RAG search"""
        query: str = Field(..., description="A query about foods, nutrients, or meal planning")
    
    class NutritionalRAGTool(BaseTool):
        name: str = "nutritional_rag_search"
        description: str = (
            "Retrieves relevant nutritional information from the knowledge base. "
            "Use this to find foods, their nutritional values, and meal recommendations "
            "for type 2 diabetes management. Input should be a query about foods, nutrients, "
            "or meal planning (e.g., 'alimentos ricos em fibras para diabeticos', "
            "'frutas com baixo índice glicêmico'). Returns JSON with ranked items."
        )
        args_schema: Type[BaseModel] = NutritionalRAGSearchInput

        def __init__(self, **data: Any):
            super().__init__(**data)
            self._cache: "OrderedDict[str, str]" = OrderedDict()

        def _get_cached(self, key: str) -> Optional[str]:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

        def _set_cached(self, key: str, value: str) -> None:
            self._cache[key] = value
            self._cache.move_to_end(key)
            while len(self._cache) > cache_size:
                self._cache.popitem(last=False)
        
        def _run(self, query: str) -> str:
            """Execute the retrieval"""
            try:
                normalized_query = _normalize_text(query)
                cached = self._get_cached(normalized_query)
                if cached is not None:
                    return cached

                # Get collection
                collection = vector_store.get_collection(collection_name)
                
                expanded_query = _expand_query(query)
                query_embedding = _cached_embed(expanded_query)
                query_tokens = _tokenize(expanded_query)
                
                # Search for similar items (retrieve more, then rerank)
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=initial_top_k,
                    include=["documents", "metadatas", "embeddings", "distances"]
                )

                graph_results = []
                if graph_client:
                    graph_results = graph_client.search_foods_by_name(query, limit=5)

                if results.get("documents") and len(results["documents"][0]) > 0:
                    scored_items = []
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = {}
                        if results.get("metadatas") and len(results["metadatas"][0]) > i:
                            metadata = results["metadatas"][0][i] or {}
                        doc_embedding = None
                        if results.get("embeddings") and len(results["embeddings"][0]) > i:
                            doc_embedding = results["embeddings"][0][i]
                            if hasattr(doc_embedding, "tolist"):
                                doc_embedding = doc_embedding.tolist()

                        name = metadata.get("name", "Unknown")
                        group = metadata.get("group", "")
                        keyword_text = f"{name} {group} {doc}"
                        keyword_score = _keyword_score(query_tokens, keyword_text)
                        embedding_score = _cosine_similarity(query_embedding, doc_embedding)
                        name_bonus = 0.1 if _normalize_text(name) in normalized_query else 0.0
                        final_score = (embedding_weight * embedding_score) + (keyword_weight * keyword_score) + name_bonus

                        scored_items.append({
                            "content": doc,
                            "metadata": metadata,
                            "scores": {
                                "embedding": round(embedding_score, 6),
                                "keyword": round(keyword_score, 6),
                                "final": round(final_score, 6)
                            }
                        })

                    scored_items.sort(key=lambda item: item["scores"]["final"], reverse=True)
                    top_items = scored_items[:final_top_k]

                    result_payload = {
                        "query": query,
                        "expanded_query": expanded_query,
                        "top_k": final_top_k,
                        "graph_results": graph_results,
                        "items": [
                            {
                                "name": item["metadata"].get("name", "Unknown"),
                                "metadata": item["metadata"],
                                "content": item["content"],
                                "scores": item["scores"]
                            }
                            for item in top_items
                        ]
                    }

                    formatted_results = json.dumps(result_payload, ensure_ascii=False, indent=2)
                    self._set_cached(normalized_query, formatted_results)
                    return formatted_results

                no_results = "No relevant nutritional information found for this query."
                self._set_cached(normalized_query, no_results)
                return no_results
                    
            except Exception as e:
                return f"Error retrieving information: {str(e)}"
    
    # Create and return the tool instance
    tool = NutritionalRAGTool()
    return tool


class NutritionalRAGTool:
    """
    Wrapper class for the nutritional RAG tool.
    Provides the tool instance for use with CrewAI agents.
    """
    
    def __init__(self, vector_store, embedding_model, graph_client: Optional[Neo4jClient] = None):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.collection_name = "nutritional_data"
        self.tool = create_nutritional_rag_tool(vector_store, embedding_model, graph_client=graph_client)
    
    def _run(self, query: str) -> str:
        """Execute the retrieval"""
        return self.tool.run(query)
    
    def __call__(self, query: str) -> str:
        """Make the tool callable"""
        return self._run(query)


class DataLoader:
    """Loads and processes nutritional data into vector database"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        embedding_device = os.getenv("EMBEDDING_DEVICE", "cpu")
        self.embedding_model = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2',
            device=embedding_device,
        )
        self.vector_store = None
        self.neo4j_client = Neo4jClient.from_env()
        self.enable_neo4j_load = os.getenv("NEO4J_ENABLE_LOAD", "false").lower() == "true"
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store"""
        persist_directory = "./chroma_db"
        self.vector_store = chromadb.PersistentClient(path=persist_directory)
    
    def load_nutritional_data(self):
        """Load nutritional data from JSONL files and index them"""
        collection_name = "nutritional_data"
        
        # Delete existing collection if it exists (for re-indexing)
        try:
            self.vector_store.delete_collection(collection_name)
        except:
            pass
        
        # Create new collection
        collection = self.vector_store.create_collection(
            name=collection_name,
            metadata={"description": "Nutritional information database"}
        )
        
        # Load data files
        data_files = [
            self.data_dir / "tbca_unified.jsonl",
            self.data_dir / "taco_unified.jsonl",
            self.data_dir / "taco.jsonl"
        ]
        
        all_documents = []
        all_metadatas = []
        all_ids = []
        
        for data_file in data_files:
            if not data_file.exists():
                print(f"Warning: {data_file} not found, skipping...")
                continue
            
            print(f"Loading {data_file.name}...")
            with open(data_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        item = json.loads(line.strip())
                        # Format document text
                        doc_text = self._format_nutritional_item(item)
                        metadata = self._extract_metadata(item)
                        
                        all_documents.append(doc_text)
                        all_metadatas.append(metadata)
                        all_ids.append(f"{data_file.stem}_{line_num}")
                        if self.neo4j_client and self.enable_neo4j_load:
                            name = metadata.get("name", "")
                            group = metadata.get("group", "")
                            source = metadata.get("source", "unknown")
                            nutrients = item.get("nutrients", {})
                            if name:
                                self.neo4j_client.upsert_food(name, group, nutrients, source)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line {line_num} in {data_file}: {e}")
                        continue
        
        if not all_documents:
            print("No documents loaded. Please check your data files.")
            return
        
        # Generate embeddings in batches
        print(f"Generating embeddings for {len(all_documents)} documents...")
        embedding_batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(all_documents), embedding_batch_size):
            batch = all_documents[i:i+embedding_batch_size]
            embeddings = self.embedding_model.encode(batch, show_progress_bar=True)
            all_embeddings.extend(embeddings.tolist())
            print(f"Processed {min(i+embedding_batch_size, len(all_documents))}/{len(all_documents)} documents")
        
        # Add to collection in batches (ChromaDB has a max batch size limit)
        print("Adding documents to vector store...")
        chromadb_batch_size = 5000  # Safe batch size for ChromaDB (max is around 5461)
        
        for i in range(0, len(all_documents), chromadb_batch_size):
            end_idx = min(i + chromadb_batch_size, len(all_documents))
            batch_docs = all_documents[i:end_idx]
            batch_embeddings = all_embeddings[i:end_idx]
            batch_metadatas = all_metadatas[i:end_idx]
            batch_ids = all_ids[i:end_idx]
            
            print(f"Adding batch {i//chromadb_batch_size + 1} ({len(batch_docs)} documents)...")
            collection.add(
                embeddings=batch_embeddings,
                documents=batch_docs,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
        
        print(f"Successfully indexed {len(all_documents)} nutritional items!")
        return collection
    
    def _format_nutritional_item(self, item: Dict) -> str:
        """Format a nutritional item as searchable text"""
        # Extract key information
        name = item.get('name_full') or item.get('descricao') or item.get('name', 'Unknown')
        
        # Get nutrients
        nutrients = item.get('nutrients', {})
        
        # Build description
        parts = [f"Alimento: {name}"]
        
        if nutrients:
            if 'energy_kcal' in nutrients:
                parts.append(f"Energia: {nutrients['energy_kcal']} kcal")
            if 'protein_total_g' in nutrients:
                parts.append(f"Proteína: {nutrients['protein_total_g']} g")
            if 'carbohydrate_available_g' in nutrients or 'carbo_idrato_g' in nutrients:
                carbs = nutrients.get('carbohydrate_available_g') or nutrients.get('carbo_idrato_g')
                parts.append(f"Carboidratos: {carbs} g")
            if 'lipids_total_g' in nutrients or 'lip_deos_g' in nutrients:
                fats = nutrients.get('lipids_total_g') or nutrients.get('lip_deos_g')
                parts.append(f"Gorduras: {fats} g")
            if 'fiber_g' in nutrients or 'fibra_alimentar_g' in nutrients:
                fiber = nutrients.get('fiber_g') or nutrients.get('fibra_alimentar_g')
                parts.append(f"Fibras: {fiber} g")
            if 'sodium_mg' in nutrients or 's_dio_mg' in nutrients:
                sodium = nutrients.get('sodium_mg') or nutrients.get('s_dio_mg')
                parts.append(f"Sódio: {sodium} mg")
        
        group = item.get('group', '')
        if group:
            parts.append(f"Grupo: {group}")
        
        return ". ".join(parts)
    
    def _extract_metadata(self, item: Dict) -> Dict:
        """Extract metadata from nutritional item"""
        # ChromaDB doesn't accept None values - filter them out
        metadata = {}
        
        # Add name (required, should always have a value)
        name = item.get('name_full') or item.get('descricao') or item.get('name', '')
        if name:
            metadata['name'] = name
        
        # Add group if available
        group = item.get('group', '')
        if group:
            metadata['group'] = group
        
        # Add source (default to 'unknown' if not present)
        source = item.get('source', 'unknown')
        metadata['source'] = source if source else 'unknown'
        
        # Add code if available (only if not None)
        if 'code_tbca' in item and item['code_tbca'] is not None:
            metadata['code_tbca'] = str(item['code_tbca'])
        
        code_taco = item.get('code_taco') or item.get('code')
        if code_taco is not None:
            metadata['code'] = str(code_taco)
        
        # Ensure all values are strings (ChromaDB requirement)
        return {k: str(v) if v is not None else '' for k, v in metadata.items()}
    
    def get_collection(self):
        """Get the nutritional data collection"""
        try:
            return self.vector_store.get_collection("nutritional_data")
        except:
            return None
    
    def get_embedding_model(self):
        """Get the embedding model"""
        return self.embedding_model


def initialize_rag_system(data_dir: str = "data", force_reload: bool = False):
    """
    Initialize the RAG system by loading data into the vector database
    
    Args:
        data_dir: Directory containing data files
        force_reload: If True, reload data even if collection exists
    
    Returns:
        tuple: (DataLoader instance, NutritionalRAGTool instance)
    """
    loader = DataLoader(data_dir)
    
    # Check if collection exists
    collection = loader.get_collection()
    
    if not collection or force_reload:
        print("Loading nutritional data into vector database...")
        loader.load_nutritional_data()
    else:
        print("Using existing vector database. Set force_reload=True to re-index.")
    
    # Create RAG tool
    rag_tool = NutritionalRAGTool(
        vector_store=loader.vector_store,
        embedding_model=loader.embedding_model,
        graph_client=loader.neo4j_client
    )
    
    return loader, rag_tool


if __name__ == "__main__":
    # Initialize RAG system
    print("Initializing RAG system...")
    loader, rag_tool = initialize_rag_system(force_reload=False)
    
    # Test the RAG tool
    print("\nTesting RAG tool with query: 'alimentos ricos em fibras para diabéticos'")
    result = rag_tool._run("alimentos ricos em fibras para diabéticos")
    print("\n" + "="*50)
    print("RETRIEVAL RESULT:")
    print("="*50)
    print(result[:1000])  # Print first 1000 chars
    print("...")

