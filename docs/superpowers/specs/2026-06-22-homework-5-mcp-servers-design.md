---
name: homework-5-mcp-servers
description: Design spec for Homework 5 — configuring GitHub, Filesystem, Notion, and custom FastMCP servers
metadata:
  type: project
---

# Homework 5: MCP Servers — Design Spec

**Date:** 2026-06-22  
**Author:** Vladyslav Nahirych

---

## Context & Decisions

| Question | Decision |
|---|---|
| Jira or Notion? | Notion |
| GitHub demo repo | `gen-ai-software-engineering` (this repo) |
| GitHub token | User creates manually (Fine-grained PAT) |
| Filesystem path | `homework-5/` only |
| Notion workspace | User creates test DB with bug entries |
| MCP config location | Local in `homework-5/.mcp.json` |
| Custom server transport | `stdio` (Approach A) |

---

## Project Structure

```
homework-5/
├── README.md
├── HOWTORUN.md
├── .mcp.json
├── custom-mcp-server/
│   ├── server.py
│   ├── lorem-ipsum.md
│   └── requirements.txt
└── docs/
    └── screenshots/
        ├── github-mcp-result.png
        ├── filesystem-mcp-result.png
        ├── notion-mcp-result.png
        └── custom-mcp-read-tool-result.png
```

---

## MCP Configuration (`.mcp.json`)

Four servers registered. Secrets via environment variable placeholders — no hardcoded credentials committed.

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\NahirychVladyslav\\Documents\\Antigravity\\gen-ai-software-engineering\\homework-5"
      ]
    },
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer ${NOTION_API_KEY}\", \"Notion-Version\": \"2022-06-28\"}"
      }
    },
    "custom-lorem": {
      "command": "python",
      "args": [
        "C:\\Users\\NahirychVladyslav\\Documents\\Antigravity\\gen-ai-software-engineering\\homework-5\\custom-mcp-server\\server.py"
      ]
    }
  }
}
```

---

## Custom MCP Server (`server.py`)

**Transport:** stdio (spawned by Claude Code, no manual server startup needed)  
**Dependency:** `fastmcp`

### Resource

- URI template: `lorem://ipsum/{word_count}`
- Default `word_count`: 30
- Reads `lorem-ipsum.md`, splits on whitespace, returns first N words

### Tool

- Name: `read`
- Parameter: `word_count: int = 30` (optional)
- Returns same N words from `lorem-ipsum.md`
- Docstring explains Resources vs Tools distinction (per task requirement)

### Implementation

```python
from fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("lorem-ipsum-server")
LOREM_FILE = Path(__file__).parent / "lorem-ipsum.md"

@mcp.resource("lorem://ipsum/{word_count}")
def lorem_resource(word_count: int = 30) -> str:
    text = LOREM_FILE.read_text(encoding="utf-8")
    words = text.split()
    return " ".join(words[:word_count])

@mcp.tool()
def read(word_count: int = 30) -> str:
    """Read lorem ipsum text. Resources are URIs Claude reads from. Tools are actions Claude calls."""
    text = LOREM_FILE.read_text(encoding="utf-8")
    words = text.split()
    return " ".join(words[:word_count])

if __name__ == "__main__":
    mcp.run()
```

---

## Documentation

### README.md

Format mirrors homework-1: emoji header, blockquote with student name/date/tools, project overview section, centered footer.

### HOWTORUN.md

Four sections:
1. **Prerequisites** — Node.js 18+, Python 3, env vars (`GITHUB_PERSONAL_ACCESS_TOKEN`, `NOTION_API_KEY`)
2. **Install dependencies** — `pip install -r requirements.txt` for custom server; npx handles the rest
3. **Connect MCP** — how to add `.mcp.json` to Claude Code project settings
4. **Test the `read` tool** — example prompt: *"Use the read tool with word_count=50"*

Resources vs Tools explanation included in HOWTORUN.md per task requirement.

---

## Deliverables Checklist

- [ ] `homework-5/.mcp.json` — all 4 servers configured
- [ ] `homework-5/custom-mcp-server/server.py` — FastMCP with resource + read tool
- [ ] `homework-5/custom-mcp-server/requirements.txt` — includes `fastmcp`
- [ ] `homework-5/custom-mcp-server/lorem-ipsum.md` — lorem ipsum source text
- [ ] `homework-5/README.md` — description + author name
- [ ] `homework-5/HOWTORUN.md` — install, run, connect, test instructions
- [ ] `homework-5/docs/screenshots/*.png` — 4 screenshots (user provides)

---

## What User Does Manually

1. Create GitHub Fine-grained PAT (read access to repo)
2. Create Notion test database with ~5 bug entries
3. Get Notion API key from [notion.so/my-integrations](https://www.notion.so/my-integrations)
4. Set env vars: `GITHUB_PERSONAL_ACCESS_TOKEN`, `NOTION_API_KEY`
5. Take 4 screenshots during MCP interactions and place in `docs/screenshots/`
