import subprocess
import json
import os
from pathlib import Path
from typing import Optional
PROJECT_ROOT = Path(__file__).resolve().parent
ACTION_TO_MARKER = {
    "create-account": "register",
    "login": "login",
    "transfer-funds": "transfer",
    "admin-add-funds": "account",
}
def build_pytest_command(action: Optional[str]) -> list[str]:
    cmd = ["pytest", "-q"]
    marker = ACTION_TO_MARKER.get(action)
    if marker:
        cmd.extend(["-m", marker]) 
    return cmd # pytest -q -m register
def run_pytest(action: str | None = None) -> dict:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    root_str = str(PROJECT_ROOT)
    if existing:
        env["PYTHONPATH"] = root_str + os.pathsep + existing
    else:
        env["PYTHONPATH"] = root_str

    cmd = build_pytest_command(action)
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        success = result.returncode == 0
        return {
            "action": action,
            "success": success,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except Exception as exc:
        return {
            "action": action,
            "success": False,
            "exit_code": 1,
            "stdout": "",
            "stderr": f"Error running pytest: {exc!r}",
        }
if __name__ == "__main__":
    print(json.dumps(run_pytest("manual"), indent=2))
