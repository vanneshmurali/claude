"""PostToolUse hook: after a push, say whether DB scripts need to be run.

Reads the hook JSON from stdin. Works for `git push` (Bash / PowerShell) and for
the github MCP push tools. Prints a hook JSON reply with a systemMessage.
"""
import json
import subprocess
import sys

EMPTY_TREE = "4b825dc642cb6eb9a060e54bd8d69288fbefdc04"


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def pushed_files_git(resp):
    text = json.dumps(resp) if not isinstance(resp, str) else resp
    if "Everything up-to-date" in text:
        return []
    up = git("rev-parse", "--abbrev-ref", "@{u}")
    if not up:
        branch = git("rev-parse", "--abbrev-ref", "HEAD")
        up = "origin/" + branch if branch else None
    if not up or not git("rev-parse", up):
        return None
    old = git("rev-parse", up + "@{1}") or EMPTY_TREE
    out = git("diff", "--name-only", old, up)
    return out.splitlines() if out else []


def pushed_files_mcp(inp):
    if "files" in inp:
        return [f.get("path", "") for f in inp.get("files") or []]
    return [inp.get("path", "")]


def needs_db(path):
    p = path.replace("\\", "/").lower()
    return p.endswith(".sql") or "migrations/" in p or p == "db.py" or p.endswith("/db.py")


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    if tool.startswith("mcp__github__"):
        files = pushed_files_mcp(data.get("tool_input") or {})
    else:
        files = pushed_files_git(data.get("tool_response"))

    if files is None:
        msg = "DB check: could not work out which files were pushed. Check for new SQL scripts or db.py changes yourself."
    else:
        hits = [f for f in files if needs_db(f)]
        if hits:
            msg = ("DB scripts need to be run. Pushed DB changes: " + ", ".join(hits) + ". "
                   "Run any .sql / migration files against the database. For db.py changes, restart the app "
                   "(init_db runs on startup) or run: py -c \"from db import init_db; init_db('employees.db')\"")
        else:
            msg = "DB check: no DB scripts need to be run for this push."

    print(json.dumps({
        "systemMessage": msg,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "Tell the user this DB check result in your reply: " + msg,
        },
    }))


if __name__ == "__main__":
    main()
