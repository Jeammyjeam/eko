---
name: visual_studio_code
version: '0.1'
category: experimental
status: active
triggers:
- open vscode
- vscode
command: python3 /home/junaid-eko/cortex/scripts/synthesized/visual_studio_code.py
  {query}
ram_mb: 50
requires: []
install_command: curl -fsSL https://code.visualstudio.com/install.sh | bash
source_repo: vscode
source_url: https://github.com/microsoft/vscode
synthesized_at: '2026-07-18T16:20:17.945237'
---
# Visual Studio Code Skill

Visual Studio Code is a distribution of the `Code - OSS` repository with Microsoft-specific customizations released under a traditional [Microsoft product license](https://code.visualstudio.com/License/). It combines the simplicity of a code editor with what developers need for their core edit-build-debug cycle. It provides comprehensive code editing, navigation, and understanding support along with lightweight debugging, a rich extensibility model, and lightweight integration with existing tools.

**Source repo:** [vscode](https://github.com/microsoft/vscode)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/visual_studio_code.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.
