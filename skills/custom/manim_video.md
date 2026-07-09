---
name: manim_video
version: '0.1'
category: experimental
status: active
triggers:
- manim video
- create animation
- math animation
- manim
- manimgl
command: python3 /home/junaid-eko/cortex/scripts/synthesized/manim_video.py {query}
ram_mb: 500
requires:
- python3
- ffmpeg
- opengl
- latex
- pango
source_repo: manim
source_url: https://github.com/3b1b/manim
synthesized_at: '2026-06-27T11:31:30.116095'
---
# Manim Video Skill

This skill provides a wrapper for ManimGL, the original animation engine by 3Blue1Brown, designed for creating precise programmatic animations and explanatory math videos. It is important to note that this skill specifically uses ManimGL, not the Manim Community Edition. Users must ensure that system dependencies like FFmpeg, OpenGL, LaTeX (optional for text rendering), and Pango (for Linux) are installed separately on their system for ManimGL to function correctly.

**Source repo:** [manim](https://github.com/3b1b/manim)

**Install:**
**Wrapper:** `/home/junaid-eko/cortex/scripts/synthesized/manim_video.py`

**Status:** experimental — synthesized automatically, not yet validated or promoted.
Review install_command and wrapper script before trusting this skill.
