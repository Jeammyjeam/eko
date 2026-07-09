import subprocess
import tempfile
import os

def run_in_sandbox(code, timeout=30):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name
    
    try:
        result = subprocess.run([
            "docker", "run", "--rm",
            "-m", "256m",
            "--cpus", "0.5",
            "--network", "none",
            "--cap-drop=ALL",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--read-only",
            "--tmpfs", "/tmp:size=64m",
            "-v", f"{tmp_path}:/sandbox/code.py:ro",
            "python:3.12-slim",
            "python", "/sandbox/code.py"
        ], capture_output=True, text=True, timeout=timeout)
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout", "returncode": 1}
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    import sys
    code = sys.stdin.read() if not sys.stdin.isatty() else "print('Hello from CORTEX sandbox!')"
    result = run_in_sandbox(code)
    print(result["stdout"])
    if result["stderr"]:
        print("STDERR:", result["stderr"])
