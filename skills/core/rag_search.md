---
name: rag_search
version: 1.1
category: core
status: active
triggers:
  - find repo
  - find repos
  - related to
  - similar to
  - rag
  - knowledge
  - semantic
command: python3 /home/junaid-eko/cortex/scripts/rag_query.py "{query}"
ram_mb: 50
requires:
  - GEMINI_API_KEY
---

# RAG Search Skill
Semantic search across 83 archived GitHub repos using pgvector.
Returns top 5 repos with similarity scores and content chunks.
