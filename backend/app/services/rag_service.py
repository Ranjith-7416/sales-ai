"""RAG Service - Vector database and knowledge base retrieval"""
from typing import List, Dict, Any, Optional
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.telemetry.product import ProductTelemetryClient
    from overrides import override
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    ProductTelemetryClient = object
    override = lambda f: f

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class NoOpTelemetry(ProductTelemetryClient):
    """Disable Chroma product telemetry for local, offline application use."""

    @override
    def capture(self, event) -> None:
        return None


class LocalSentenceTransformerEmbeddings:
    """Minimal local embedding adapter that never downloads a model at runtime."""

    def __init__(self, model_name: str):
        if not HAS_SENTENCE_TRANSFORMERS:
            raise RuntimeError("sentence_transformers is not installed")
        self.model = SentenceTransformer(
            model_name,
            device="cpu",
            local_files_only=True,
        )

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()


class RAGService:
    """Vector database and RAG for knowledge base with an offline lexical fallback."""

    def __init__(self):
        self.embedding_model_name = settings.EMBEDDING_MODEL
        self.kb_path = settings.KNOWLEDGE_BASE_PATH
        self.vector_path = f"{self.kb_path}/.chroma"
        self.embeddings = None
        self.client = None
        self.product_collection = None
        self.service_collection = None
        self.case_study_collection = None
        self._fallback_products: List[Dict[str, Any]] = []
        self._fallback_services: List[Dict[str, Any]] = []

        if HAS_CHROMADB and HAS_SENTENCE_TRANSFORMERS:
            try:
                # Offline-first prevents an unavailable model cache from turning a
                # deterministic local workflow into a Hugging Face network request.
                self.embeddings = LocalSentenceTransformerEmbeddings(self.embedding_model_name)
                self.client = chromadb.PersistentClient(
                    path=self.vector_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        chroma_product_telemetry_impl="app.services.rag_service.NoOpTelemetry",
                    ),
                )
                self.product_collection = self.client.get_or_create_collection(
                    name="products",
                    metadata={"hnsw:space": "cosine"},
                )
                self.service_collection = self.client.get_or_create_collection(
                    name="services",
                    metadata={"hnsw:space": "cosine"},
                )
                self.case_study_collection = self.client.get_or_create_collection(
                    name="case_studies",
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as exc:
                logger.warning("Vector RAG unavailable; using bundled lexical retrieval: %s", exc)
        else:
            logger.info("ChromaDB or SentenceTransformers not available; using bundled lexical retrieval")
        self._load_bundled_knowledge_base()

    @staticmethod
    def _safe_metadata(value: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: json.dumps(item) if isinstance(item, (list, dict)) else str(item)
            for key, item in value.items()
            if item is not None
        }

    def _load_bundled_knowledge_base(self):
        for filename, loader in (("products.json", self.add_products), ("services.json", self.add_services)):
            path = f"{self.kb_path}/{filename}"
            try:
                with open(path, "r", encoding="utf-8") as file:
                    entries = json.load(file)
                if entries:
                    loader(entries)
            except FileNotFoundError:
                logger.info(f"Bundled knowledge base file not found: {path}")
            except Exception as exc:
                logger.warning(f"Unable to load bundled knowledge base {path}: {exc}")

    def add_products(self, products: List[Dict[str, Any]]):
        """Add products to knowledge base"""
        try:
            self._fallback_products = self._merge_fallback_entries(self._fallback_products, products)
            if not self.embeddings or not self.product_collection:
                return
            for product in products:
                product_id = product.get("id", product.get("name", "")).lower().replace(" ", "_")
                
                # Create text representation for embedding
                product_text = self._create_product_text(product)
                
                # Generate embedding
                embedding = self.embeddings.embed_query(product_text)
                
                # Add to collection
                self.product_collection.upsert(
                    ids=[product_id],
                    embeddings=[embedding],
                    documents=[product_text],
                    metadatas=[self._safe_metadata(product)],
                )
            logger.info(f"Added {len(products)} products to knowledge base")
        except Exception as e:
            logger.error(f"Error adding products: {str(e)}")
            raise

    def add_services(self, services: List[Dict[str, Any]]):
        """Add services to knowledge base"""
        try:
            self._fallback_services = self._merge_fallback_entries(self._fallback_services, services)
            if not self.embeddings or not self.service_collection:
                return
            for service in services:
                service_id = service.get("id", service.get("name", "")).lower().replace(" ", "_")
                
                service_text = self._create_service_text(service)
                embedding = self.embeddings.embed_query(service_text)
                
                self.service_collection.upsert(
                    ids=[service_id],
                    embeddings=[embedding],
                    documents=[service_text],
                    metadatas=[self._safe_metadata(service)],
                )
            logger.info(f"Added {len(services)} services to knowledge base")
        except Exception as e:
            logger.error(f"Error adding services: {str(e)}")
            raise

    def search_products(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search products by requirement"""
        if not self.embeddings or not self.product_collection:
            return self._lexical_search(query, self._fallback_products, "product", top_k)
        try:
            query_embedding = self.embeddings.embed_query(query)
            results = self.product_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
            
            # Format results
            formatted_results = []
            if results and results.get("metadatas"):
                for i, metadata in enumerate(results["metadatas"][0]):
                    result = {
                        "product": self._decode_metadata(metadata),
                        "score": results["distances"][0][i] if results.get("distances") else 0,
                    }
                    formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []

    def search_services(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search services by requirement"""
        if not self.embeddings or not self.service_collection:
            return self._lexical_search(query, self._fallback_services, "service", top_k)
        try:
            query_embedding = self.embeddings.embed_query(query)
            results = self.service_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
            
            formatted_results = []
            if results and results.get("metadatas"):
                for i, metadata in enumerate(results["metadatas"][0]):
                    result = {
                        "service": self._decode_metadata(metadata),
                        "score": results["distances"][0][i] if results.get("distances") else 0,
                    }
                    formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching services: {str(e)}")
            return []

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products from knowledge base"""
        if not self.product_collection:
            return list(self._fallback_products)
        try:
            results = self.product_collection.get()
            return [self._decode_metadata(item) for item in results.get("metadatas", [])] if results else []
        except Exception as e:
            logger.error(f"Error retrieving all products: {str(e)}")
            return []

    def get_all_services(self) -> List[Dict[str, Any]]:
        """Get all services from knowledge base"""
        if not self.service_collection:
            return list(self._fallback_services)
        try:
            results = self.service_collection.get()
            return [self._decode_metadata(item) for item in results.get("metadatas", [])] if results else []
        except Exception as e:
            logger.error(f"Error retrieving all services: {str(e)}")
            return []

    @staticmethod
    def _create_product_text(product: Dict[str, Any]) -> str:
        """Create searchable text from product data"""
        parts = [
            f"Product: {product.get('name', '')}",
            f"Description: {product.get('description', '')}",
            f"Features: {', '.join(product.get('features', []))}",
            f"Pricing: {product.get('pricing', '')}",
            f"Certifications: {', '.join(product.get('certifications', []))}",
            f"Delivery: {product.get('delivery_timeline', '')}",
            f"Use cases: {', '.join(product.get('use_cases', []))}",
        ]
        return " ".join([p for p in parts if p])

    @staticmethod
    def _decode_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        decoded = {}
        for key, value in metadata.items():
            if isinstance(value, str) and value[:1] in "[{":
                try:
                    decoded[key] = json.loads(value)
                    continue
                except json.JSONDecodeError:
                    pass
            decoded[key] = value
        return decoded

    @staticmethod
    def _create_service_text(service: Dict[str, Any]) -> str:
        """Create searchable text from service data"""
        parts = [
            f"Service: {service.get('name', '')}",
            f"Description: {service.get('description', '')}",
            f"Type: {service.get('type', '')}",
            f"SLA: {service.get('sla', '')}",
            f"Support: {service.get('support_hours', '')}",
            f"Price: {service.get('pricing', '')}",
        ]
        return " ".join([p for p in parts if p])

    @staticmethod
    def _merge_fallback_entries(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Upsert local catalog records by stable ID without mutating caller data."""
        merged = {str(item.get("id") or item.get("name")): dict(item) for item in existing}
        for item in incoming:
            if isinstance(item, dict):
                merged[str(item.get("id") or item.get("name"))] = dict(item)
        return list(merged.values())

    @staticmethod
    def _lexical_search(query: str, entries: List[Dict[str, Any]], kind: str, top_k: int) -> List[Dict[str, Any]]:
        """Return bounded, deterministic bundled-KB matches when vectors are unavailable."""
        query_terms = {term.lower() for term in str(query).replace("/", " ").split() if len(term) > 2}
        ranked = []
        for entry in entries:
            document = json.dumps(entry, ensure_ascii=False).lower()
            score = sum(term in document for term in query_terms)
            ranked.append((score, str(entry.get("name", "")), entry))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [
            {kind: dict(entry), "score": score}
            for score, _, entry in ranked[:top_k]
        ]


# Singleton instance
_rag_service = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
