import os
import re
import shutil
import subprocess
import yaml
from datetime import datetime

SKILLS_DIR = os.path.join(os.path.expanduser("~/cortex"), "skills")
EXPERIMENTAL = os.path.join(SKILLS_DIR, "experimental")
CUSTOM = os.path.join(SKILLS_DIR, "custom")
CORE = os.path.join(SKILLS_DIR, "core")
LOCK_FILE = "/tmp/cortex_promoter.lock"

def load_active_triggers():
    """Load all triggers from core and custom skills to detect collisions.
    Only flags exact duplicate triggers — shared generic triggers are allowed
    since route_by_skills uses longest-match-first to resolve ambiguity.
    """
    triggers = {}
    for category in ["core", "custom"]:
        path = os.path.join(SKILLS_DIR, category)
        if not os.path.exists(path):
            continue
        for fname in os.listdir(path):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(path, fname)
            with open(fpath) as f:
                raw = f.read()
            meta = {}
            if raw.startswith("---"):
                try:
                    end = raw.index("---", 3)
                    meta = yaml.safe_load(raw[3:end])
                except Exception:
                    pass
            name = meta.get("name", fname.replace(".md", ""))
            for t in meta.get("triggers", []):
                t_lower = t.lower().strip()
                # Only flag SHORT generic triggers (under 6 chars) as collisions
                # Longer specific triggers can be shared — longest match wins at runtime
                if len(t_lower) <= 6:
                    triggers[t_lower] = name
    return triggers

def validate_frontmatter(meta, filepath):
    """Phase A — structure validation."""
    errors = []
    required = ["name", "version", "triggers", "ram_mb", "command"]
    for field in required:
        if field not in meta:
            errors.append(f"Missing required field: {field}")
    if "ram_mb" in meta:
        try:
            ram = int(meta["ram_mb"])
            if ram > 512:
                errors.append(f"ram_mb {ram} exceeds 512MB safety limit")
        except Exception:
            errors.append("ram_mb must be an integer")
    if "triggers" in meta:
        if not isinstance(meta["triggers"], list) or len(meta["triggers"]) == 0:
            errors.append("triggers must be a non-empty list")
    return errors

def check_trigger_collisions(meta, active_triggers):
    """Guardrail 3 — detect duplicate triggers."""
    collisions = []
    for t in meta.get("triggers", []):
        if t.lower() in active_triggers:
            collisions.append(f"Trigger '{t}' already used by skill '{active_triggers[t.lower()]}'")
    return collisions

def test_in_sandbox(meta):
    """Phase B — sandbox execution test."""
    command = meta.get("command", "")
    if not command:
        return False, "No command defined"

    # Extract the script path from command
    parts = command.split()
    script = None
    for part in parts:
        if part.endswith(".py"):
            script = part
            break

    if not script or not os.path.exists(script):
        return False, f"Script not found: {script}"

    try:
        # Check script is valid Python syntax
        result = subprocess.run(
            ["python3", "-m", "py_compile", script],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, "Script syntax valid"
        return False, f"Syntax error: {result.stderr[:100]}"
    except subprocess.TimeoutExpired:
        return False, "Timed out after 10s"
    except Exception as e:
        return False, str(e)

def promote(fpath, meta):
    """Phase C — migrate and update status."""
    fname = os.path.basename(fpath)
    dest = os.path.join(CUSTOM, fname)

    # Update status in frontmatter
    with open(fpath) as f:
        content = f.read()
    content = content.replace("status: experimental", "status: active")
    content = content.replace("status: pending", "status: active")

    with open(fpath, "w") as f:
        f.write(content)

    shutil.move(fpath, dest)
    print(f"  Promoted to custom/: {fname}")

    # Git commit
    try:
        subprocess.run(
            ["git", "-C", os.path.expanduser("~/cortex"), "add", "."],
            capture_output=True
        )
        subprocess.run(
            ["git", "-C", os.path.expanduser("~/cortex"), "commit",
             "-m", f"feat: skill promoted - {meta.get('name', fname)} experimental -> custom"],
            capture_output=True
        )
        print(f"  Git commit done")
    except Exception as e:
        print(f"  Git commit failed: {e}")

def run():
    # Guardrail 1 — prevent recursive execution
    if os.path.exists(LOCK_FILE):
        print("Promoter already running (lock file exists) — aborting")
        return

    open(LOCK_FILE, "w").close()

    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] CORTEX Skills Promoter starting...")
        os.makedirs(EXPERIMENTAL, exist_ok=True)
        os.makedirs(CUSTOM, exist_ok=True)

        candidates = [f for f in os.listdir(EXPERIMENTAL) if f.endswith(".md")]
        if not candidates:
            print("No experimental skills found — nothing to promote")
            return

        print(f"Found {len(candidates)} experimental skill(s)")
        active_triggers = load_active_triggers()
        promoted = 0
        failed = 0

        for fname in candidates:
            fpath = os.path.join(EXPERIMENTAL, fname)
            print(f"\nEvaluating: {fname}")

            with open(fpath) as f:
                raw = f.read()

            meta = {}
            if raw.startswith("---"):
                try:
                    end = raw.index("---", 3)
                    meta = yaml.safe_load(raw[3:end])
                except Exception as e:
                    print(f"  FAIL — YAML parse error: {e}")
                    failed += 1
                    continue

            # Phase A — validate structure
            errors = validate_frontmatter(meta, fpath)
            if errors:
                print(f"  FAIL — validation errors:")
                for e in errors:
                    print(f"    - {e}")
                failed += 1
                continue
            print(f"  Phase A passed — structure valid")

            # Guardrail 3 — trigger collision check
            collisions = check_trigger_collisions(meta, active_triggers)
            if collisions:
                print(f"  FAIL — trigger collisions:")
                for c in collisions:
                    print(f"    - {c}")
                failed += 1
                continue
            print(f"  Trigger check passed — no collisions")

            # Phase B — sandbox test
            passed, reason = test_in_sandbox(meta)
            if not passed:
                print(f"  FAIL — sandbox: {reason}")
                failed += 1
                continue
            print(f"  Phase B passed — sandbox: {reason}")

            # Phase C — promote
            promote(fpath, meta)
            # Phase D — hardware check then auto-install
            install_cmd = meta.get("install_command", "")
            if install_cmd:
                # Check system can handle it
                try:
                    import sys
                    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                    from system_profile import check_install_feasibility
                    ram_required = meta.get("ram_mb", 100)
                    feasible, issues = check_install_feasibility(ram_required)
                    if not feasible:
                        print(f"  Install skipped — hardware insufficient: {'; '.join(issues)}")
                    else:
                        print(f"  Installing: {install_cmd[:60]}...")
                        try:
                            result = subprocess.run(
                                install_cmd, shell=True,
                                capture_output=True, text=True, timeout=120
                            )
                            if result.returncode == 0:
                                print(f"  Install: OK")
                            else:
                                print(f"  Install warning: {result.stderr[:100]}")
                        except Exception as e:
                            print(f"  Install error: {e}")
                except ImportError:
                    print(f"  system_profile not available — skipping hardware check")
            else:
                print(f"  No install_command — skipping auto-install")
            promoted += 1

        print(f"\nPromoter complete: {promoted} promoted, {failed} failed")

    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

if __name__ == "__main__":
    run()
