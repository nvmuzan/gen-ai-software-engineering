# ▶️ How to Run — Homework 5: MCP Servers

## Prerequisites

- **Node.js 18+** — required for `npx` (GitHub, Filesystem, Notion servers)
- **Python 3** — required for the custom FastMCP server
- **Claude Code** — MCP client that reads `.mcp.json`

---

## 1. Set Environment Variables

Before connecting, set your credentials as environment variables.

**Windows (PowerShell):**
```powershell
$env:GITHUB_PERSONAL_ACCESS_TOKEN = "github_pat_..."
$env:NOTION_API_KEY = "secret_..."
```

**Getting credentials:**
- **GitHub PAT**: go to github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens. Grant read access to the `gen-ai-software-engineering` repo.
- **Notion API key**: go to notion.so/my-integrations → New integration → copy the Internal Integration Secret. Then open your Notion database → Share → Invite your integration.

---

## 2. Install Custom Server Dependencies

```bash
cd homework-5/custom-mcp-server
pip install -r requirements.txt
```

The external servers (GitHub, Filesystem, Notion) are installed automatically via `npx` on first use — no manual install needed.

---

## 3. Connect MCP Configuration to Claude Code

Claude Code auto-discovers `.mcp.json` when it is present in the project directory. Open `homework-5/` as your project root in Claude Code and the four servers will be picked up automatically.

Alternatively, copy `.mcp.json` contents into your global `~/.claude/mcp.json`.

---

## 4. Verify Servers Are Running

Open Claude Code and check the MCP servers panel — all four should show as connected:
- `github` ✓
- `filesystem` ✓
- `notion` ✓
- `custom-lorem` ✓

---

## 5. Test Each Server

### GitHub MCP
```
List the last 5 pull requests in the gen-ai-software-engineering repository.
```

### Filesystem MCP
```
List all files in the homework-5 directory.
```

### Notion MCP
```
Give me the tickets/pages of the last 5 bugs on my project.
```

### Custom MCP — read tool
```
Use the read tool with word_count=50
```

Expected response: first 50 words from `lorem-ipsum.md`.

---

## Resources vs Tools

**Resources** are URI-addressable data sources Claude can read from — similar to files or API endpoints. In this server, the resource URI is `lorem://ipsum/{word_count}`.

**Tools** are callable actions Claude can invoke to perform operations — similar to function calls. The `read` tool accepts `word_count` and returns content from the resource file.

---

## Run Tests for Custom Server

```bash
cd homework-5/custom-mcp-server
python -m pytest tests/ -v
```

Expected: 4 tests pass.
