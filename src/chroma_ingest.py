import json

import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm

CORPUS_PATH = "data/rag_corpus_final.jsonl"
DB_PATH = "data/chroma_db"
COLLECTION_NAME = "rag_corpus"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 256


def load_corpus(path):
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return records


def build_metadata(record):
    # ChromaDB metadata can't store None; -1.0 marks the one CVE with no EPSS score yet.
    epss_score = record["epss_score"]
    epss_percentile = record["epss_percentile"]
    return {
        "cvss_score": record["cvss_score"],
        "cvss_severity": record["cvss_severity"],
        "attack_vector": record["attack_vector"],
        "kev_listed": record["kev_listed"],
        "epss_score": epss_score if epss_score is not None else -1.0,
        "epss_percentile": epss_percentile if epss_percentile is not None else -1.0,
        "year": int(record["published"][:4]),
    }


def ingest():
    print(f"Loading corpus from {CORPUS_PATH}...")
    records = load_corpus(CORPUS_PATH)
    print(f"Loaded {len(records)} records.")

    client = chromadb.PersistentClient(path=DB_PATH)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    print(f"Embedding and ingesting into ChromaDB collection '{COLLECTION_NAME}'...")
    for i in tqdm(range(0, len(records), BATCH_SIZE)):
        batch = records[i:i + BATCH_SIZE]
        collection.add(
            ids=[r["id"] for r in batch],
            documents=[r["description"] for r in batch],
            metadatas=[build_metadata(r) for r in batch],
        )

    print(f"Done. Collection now has {collection.count()} records.")


if __name__ == "__main__":
    ingest()
