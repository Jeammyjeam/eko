import subprocess
import sys
import re

# Auto-generated CORTEX skill wrapper for: sherlock
# Find social media accounts by username across multiple platforms

def execute_skill(query=""):
    # Extract just the username from natural language queries
    # e.g. "search social media accounts for username jeammy" -> "jeammy"
    username_match = re.search(r'(?:username|user|for|@)\s+(\S+)$', query.strip(), re.IGNORECASE)
    username = username_match.group(1) if username_match else query.strip().split()[-1]
    
    args = ["sherlock", username, "--timeout", "5", "--print-found"]
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            print(f"CLI Error: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)
        print(result.stdout)
    except FileNotFoundError:
        print(f"Error: sherlock not installed — run: pip install sherlock-project", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"Error: Command timed out after 120s", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Execution Failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    execute_skill(query)
