"""Free-text / CVE-ID search over the rag_corpus ChromaDB collection.

Read-only: connects to the existing persistent collection built by
src/chroma_ingest.py. Never writes to it or re-embeds the corpus.
"""

import re

import chromadb
from chromadb.utils import embedding_functions

DB_PATH = "data/chroma_db"
COLLECTION_NAME = "rag_corpus"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SEARCH_TOP_K = 20

CVE_ID_RE = re.compile(r"^\s*CVE-\d{4}-\d+\s*$", re.IGNORECASE)


class SearchEngine:
    def __init__(self, corpus_store, db_path=DB_PATH):
        self.corpus_store = corpus_store
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection(COLLECTION_NAME)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )

    def search(self, query):
        query = (query or "").strip()
        if not query:
            return None

        if CVE_ID_RE.match(query):
            cve_id = query.strip().upper()
            record = self.corpus_store.get(cve_id)
            return [record] if record else []

        embedding = self.embedding_fn([query])
        res = self.collection.query(query_embeddings=embedding, n_results=SEARCH_TOP_K)
        results = []
        for cve_id in res["ids"][0]:
            record = self.corpus_store.get(cve_id)
            if record is not None:
                results.append(record)
        return results
