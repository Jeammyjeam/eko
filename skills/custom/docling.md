---
name: docling
version: '0.1'
category: experimental
status: active
triggers:
- process document with docling
- extract data from document
- understand document content
- generate structured data from document
- parse document with docling
command: python3 /home/junaid-eko/cortex/scripts/synthesized/docling.py {query}
ram_mb: 500
requires:
- python3
install_command: pip install docling
source_repo: docling
source_url: https://github.com/docling-project/docling
synthesized_at: '2026-06-28T17:30:35.016915'
---
# Docling Skill

This skill uses Docling to intelligently process documents, extracting data and generating structured JSON output. It can handle various document formats, making it useful for automating information extraction and building document processing pipelines. The skill expects a document file path as input and returns the extracted content as JSON.

**Source repo:** [docling](https://github.com/docling-project/docling)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/docling.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.
