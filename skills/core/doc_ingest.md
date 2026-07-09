---
name: doc_ingest
version: 1.0
category: core
status: active
triggers:
  - ingest
  - document
  - pdf
  - upload
  - read file
command: python3 /home/junaid-eko/cortex/scripts/doc_ingestor.py
ram_mb: 50
requires:
  - GEMINI_API_KEY
---

# Document Ingestor Skill
Ingest PDF, DOCX, TXT, MD, or code files into CORTEX pgvector RAG.
Drop file into ~/cortex/docs_inbox/ then run this skill.
Processed files move to ~/cortex/docs_processed/.
Shows as doc:filename in RAG search results.
