# Employee App

```powershell
py -m pip install -r requirements.txt
py app.py
```

Open http://127.0.0.1:5000

Logins: `admin` / `admin123` (can see Dashboard), `user` / `user123` (employees only).

Optional environment variables:

- `SECRET_KEY`: session signing key. If unset, a random key is used and everyone is logged out on restart.
- `EMPLOYEES_DB`: path to the SQLite database (default `employees.db`).
- `FLASK_DEBUG=1`: turns on the debugger and auto-reload. Use it on a local machine only.

## Run tests

```powershell
py -m pip install -r requirements-dev.txt
py -m pytest
```

## Code review via GitHub/GitLab MCP

The `pr-reviewer` agent (`.claude/agents/pr-reviewer.md`) reviews a pull request or merge request through
the `github` or `gitlab` MCP server in `.mcp.json`. It writes `reviews/pr-<n>-review.md` (or `mr-<n>`) and
posts comments only when asked.

- **GitHub:** create a fine-grained personal access token with read access to *Contents* and *Pull requests*.
  Add write access to *Pull requests* only if you want it to post reviews. Set it before starting
  Claude Code, and never commit it:

  ```powershell
  $env:GITHUB_PAT = "<token>"
  ```

- **GitLab (gitlab.com):** no token needed. Run `/mcp` in Claude Code, select `gitlab` and sign in via OAuth.
  For self-managed GitLab, change the `url` in `.mcp.json` to `https://<your-gitlab-host>/api/v4/mcp`.

Then ask Claude, for example:

```
Use the pr-reviewer agent to review https://github.com/<owner>/<repo>/pull/12
Use the pr-reviewer agent to review https://gitlab.com/<group>/<project>/-/merge_requests/7 and post
```

Roadmap: [docs/PLAN.md](docs/PLAN.md).
