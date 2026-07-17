import subprocess
import sys

# Auto-generated CORTEX skill wrapper for: react
# React is a JavaScript library for building user interfaces. It provides a declarative and component-

def execute_skill(query=""):
    args = ["node_modules/react/bin/react-cli.js", "--flag", "{query}"]
    # Replace {query} placeholder with actual input
    args = [a.replace("{{query}}", query) for a in args]
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode != 0:
            print(f"CLI Error: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)
        print(result.stdout)
    except FileNotFoundError:
        print(f"Error: CLI tool not found — is it installed?", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"Error: Command timed out after 15s", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Execution Failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    execute_skill(query)
