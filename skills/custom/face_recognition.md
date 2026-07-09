---
name: face_recognition
version: '0.1'
category: experimental
status: active
triggers:
- recognize
- identify
- detect
command: python3 /home/junaid-eko/cortex/scripts/synthesized/face_recognition.py {query}
ram_mb: 50
requires: []
install_command: pip install face_recognition
source_repo: face_recognition
source_url: https://github.com/ageitgey/face_recognition
synthesized_at: '2026-06-28T17:45:12.108642'
---
# Face Recognition Skill

Recognize and manipulate faces from Python or from the command line with the world's simplest face recognition library.

**Source repo:** [face_recognition](https://github.com/ageitgey/face_recognition)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/face_recognition.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.
