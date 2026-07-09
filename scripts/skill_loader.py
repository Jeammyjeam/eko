import os
import yaml

SKILLS_DIR = os.path.join(os.path.expanduser("~/cortex"), "skills")

def load_skills():
    skills = {}
    for category in ["core", "custom", "experimental"]:
        path = os.path.join(SKILLS_DIR, category)
        if not os.path.exists(path):
            continue
        for fname in os.listdir(path):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(path, fname)
            with open(fpath, "r") as f:
                content = f.read()
            # Parse YAML frontmatter between --- blocks
            meta = {}
            if content.startswith("---"):
                try:
                    end = content.index("---", 3)
                    meta = yaml.safe_load(content[3:end])
                except Exception:
                    meta = {}
            name = meta.get("name", fname.replace(".md", ""))
            skills[name] = {
                "name": name,
                "category": meta.get("category", category),
                "status": meta.get("status", "unknown"),
                "version": meta.get("version", "1.0"),
                "triggers": meta.get("triggers", []),
                "command": meta.get("command", ""),
                "ram_mb": meta.get("ram_mb", 0),
                "requires": meta.get("requires", []),
                "file": fpath,
                "meta": meta
            }
    return skills

def route_by_skills(task, skills):
    task_lower = task.lower()
    # Sort by trigger length descending — longer triggers match first
    # This prevents "search" matching before "add goal research"
    all_triggers = []
    for name, skill in skills.items():
        if skill.get("status") != "active":
            continue
        for trigger in skill.get("triggers", []):
            all_triggers.append((len(trigger), trigger.lower(), name))
    all_triggers.sort(reverse=True)
    for _, trigger, name in all_triggers:
        if trigger in task_lower:
            return name
    return "web_search"  # default fallback

if __name__ == "__main__":
    skills = load_skills()
    print(f"CORTEX Skills loaded: {len(skills)}")
    for name, s in skills.items():
        triggers = ", ".join(s["triggers"][:3])
        print(f"  [{s['category']}] {name} v{s['version']} | triggers: {triggers}")
    print()
    # Test routing
    tests = [
        "find repos related to AI agents",
        "check system health",
        "search web for latest LLM news",
        "ingest this pdf document",
        "run code in sandbox",
    ]
    print("Routing tests:")
    for t in tests:
        routed = route_by_skills(t, skills)
        print(f"  '{t}' -> {routed}")
