FROM python:3.13-slim

WORKDIR /app

# System deps for chromadb/sentence-transformers wheels that need a compiler
# fallback on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch first (sentence-transformers' dependency) -- pip's default
# resolution on Linux otherwise pulls the CUDA build (~1.5GB of unused
# nvidia-* wheels), which bloats the image for no benefit on HF Spaces'
# CPU-only free tier.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements-space.txt .
RUN pip install --no-cache-dir -r requirements-space.txt

# Code
COPY app.py .
COPY src/ src/
COPY assets/ assets/
COPY v2_bullet/prompts/prompt-persona_v2.txt v2_bullet/prompts/prompt-persona_v2.txt

# Data the dashboard reads at startup/runtime -- see src/dashboard_data.py
# (CORPUS_PATH), src/dashboard_search.py (DB_PATH), src/dashboard_generate.py
# (CACHE_PATH). Nothing else under data/ (raw NVD pulls, eval sample, etc.)
# is needed to serve the dashboard.
COPY data/rag_corpus_final.jsonl data/rag_corpus_final.jsonl
COPY data/chroma_db/ data/chroma_db/
COPY data/dashboard_summary_cache.json data/dashboard_summary_cache.json

# Pre-download the sentence-transformers embedding model at build time so
# the first search/Explain request on a cold container doesn't pay for it.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Cloud Run injects its own PORT env var at container start (default 8080)
# and requires the app to bind 0.0.0.0 -- these ENV values are just the
# build-time default so the image also runs standalone (docker run -p) with
# no extra flags.
ENV HOST=0.0.0.0
ENV PORT=8080
ENV DASH_DEBUG=0
EXPOSE 8080

CMD ["python", "app.py"]
