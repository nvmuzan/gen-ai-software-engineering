# Homework 5: MCP Servers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create all deliverables for Homework 5 — configure four MCP servers (GitHub, Filesystem, Notion, custom FastMCP) and produce complete documentation.

**Architecture:** Custom server uses FastMCP with stdio transport (spawned by Claude Code). Three external servers (GitHub, Filesystem, Notion) configured via npx in `.mcp.json`. Screenshots are taken manually by the user after setup.

**Tech Stack:** Python 3, FastMCP, Node.js/npx for external MCP servers, Markdown docs.

## Global Constraints

- Python: use `python` command (Windows — `python3` does not exist as alias)
- All files under `homework-5/` (relative to repo root `c:\Users\NahirychVladyslav\Documents\Antigravity\gen-ai-software-engineering\`)
- No secrets committed — env var placeholders only in `.mcp.json`
- `fastmcp` must be explicit in `requirements.txt`
- README format mirrors homework-1 (emoji header, blockquote metadata, centered footer)
- Screenshots are user responsibility — create placeholder `.gitkeep` only

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `homework-5/custom-mcp-server/lorem-ipsum.md` | Create | Source text for MCP resource |
| `homework-5/custom-mcp-server/requirements.txt` | Create | Python deps including `fastmcp` |
| `homework-5/custom-mcp-server/server.py` | Create | FastMCP server with resource + read tool |
| `homework-5/custom-mcp-server/tests/test_server.py` | Create | Unit test for word-slice logic |
| `homework-5/.mcp.json` | Create | All 4 MCP servers configured |
| `homework-5/README.md` | Create | Project description + author |
| `homework-5/HOWTORUN.md` | Create | Full setup and usage instructions |
| `homework-5/docs/screenshots/.gitkeep` | Create | Placeholder for user screenshots |

---

### Task 1: Custom MCP Server — foundation files

**Files:**
- Create: `homework-5/custom-mcp-server/lorem-ipsum.md`
- Create: `homework-5/custom-mcp-server/requirements.txt`

**Interfaces:**
- Produces: `lorem-ipsum.md` — plain text file with 200+ words for word-slice logic

- [ ] **Step 1: Create lorem-ipsum.md**

Create `homework-5/custom-mcp-server/lorem-ipsum.md` with this content (200+ words so word_count up to 100 works):

```markdown
Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium totam rem aperiam eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.

Neque porro quisquam est qui dolorem ipsum quia dolor sit amet consectetur adipisci velit sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam quis nostrum exercitationem ullam corporis suscipit laboriosam nisi ut aliquid ex ea commodi consequatur.
```

- [ ] **Step 2: Create requirements.txt**

Create `homework-5/custom-mcp-server/requirements.txt`:

```
fastmcp>=2.0.0
```

- [ ] **Step 3: Commit**

```bash
git add homework-5/custom-mcp-server/lorem-ipsum.md homework-5/custom-mcp-server/requirements.txt
git commit -m "feat(hw5): add lorem-ipsum source and requirements for custom MCP server"
```

---

### Task 2: Custom MCP Server — server.py with TDD

**Files:**
- Create: `homework-5/custom-mcp-server/tests/__init__.py`
- Create: `homework-5/custom-mcp-server/tests/test_server.py`
- Create: `homework-5/custom-mcp-server/server.py`

**Interfaces:**
- Consumes: `lorem-ipsum.md` from Task 1
- Produces:
  - `read(word_count: int = 30) -> str` — MCP tool, returns first N words
  - `lorem_resource(word_count: int = 30) -> str` — MCP resource at `lorem://ipsum/{word_count}`

- [ ] **Step 1: Install fastmcp**

```bash
cd homework-5/custom-mcp-server
pip install -r requirements.txt
```

Expected: `Successfully installed fastmcp-...`

- [ ] **Step 2: Create test file**

Create `homework-5/custom-mcp-server/tests/__init__.py` (empty file).

Create `homework-5/custom-mcp-server/tests/test_server.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import slice_words


def test_slice_words_default():
    text = "one two three four five six"
    assert slice_words(text, 3) == "one two three"


def test_slice_words_more_than_available():
    text = "one two three"
    assert slice_words(text, 10) == "one two three"


def test_slice_words_zero():
    assert slice_words("one two three", 0) == ""


def test_slice_words_single():
    assert slice_words("hello world", 1) == "hello"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd homework-5/custom-mcp-server
python -m pytest tests/test_server.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `server` does not exist yet.

- [ ] **Step 4: Create server.py**

Create `homework-5/custom-mcp-server/server.py`:

```python
from fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("lorem-ipsum-server")

LOREM_FILE = Path(__file__).parent / "lorem-ipsum.md"


def slice_words(text: str, word_count: int) -> str:
    words = text.split()
    return " ".join(words[:word_count])


@mcp.resource("lorem://ipsum/{word_count}")
def lorem_resource(word_count: int = 30) -> str:
    return slice_words(LOREM_FILE.read_text(encoding="utf-8"), word_count)


@mcp.tool()
def read(word_count: int = 30) -> str:
    """Read lorem ipsum text from the resource file.

    Resources are URIs that Claude can read from (e.g., files, APIs).
    Tools are actions Claude can call to perform operations (e.g., reading a file, running a command).
    """
    return slice_words(LOREM_FILE.read_text(encoding="utf-8"), word_count)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd homework-5/custom-mcp-server
python -m pytest tests/test_server.py -v
```

Expected output:
```
test_server.py::test_slice_words_default PASSED
test_server.py::test_slice_words_more_than_available PASSED
test_server.py::test_slice_words_zero PASSED
test_server.py::test_slice_words_single PASSED

4 passed
```

- [ ] **Step 6: Verify server starts without errors**

```bash
cd homework-5/custom-mcp-server
python server.py &
```

Expected: process starts (FastMCP prints startup message to stderr). Kill it with Ctrl+C after confirming.

- [ ] **Step 7: Commit**

```bash
git add homework-5/custom-mcp-server/server.py homework-5/custom-mcp-server/tests/
git commit -m "feat(hw5): add FastMCP custom server with read tool and word-slice logic"
```

---

### Task 3: MCP Configuration

**Files:**
- Create: `homework-5/.mcp.json`

**Interfaces:**
- Consumes: `server.py` path from Task 2
- Produces: Valid `.mcp.json` registering all 4 MCP servers

- [ ] **Step 1: Create .mcp.json**

Create `homework-5/.mcp.json`:

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

- [ ] **Step 2: Validate JSON syntax**

```bash
python -c "import json; json.load(open('homework-5/.mcp.json')); print('JSON valid')"
```

Expected: `JSON valid`

- [ ] **Step 3: Commit**

```bash
git add homework-5/.mcp.json
git commit -m "feat(hw5): add MCP configuration for all 4 servers"
```

---

### Task 4: Documentation

**Files:**
- Create: `homework-5/README.md`
- Create: `homework-5/HOWTORUN.md`
- Create: `homework-5/docs/screenshots/.gitkeep`

**Interfaces:**
- Produces: Complete documentation per task requirements

- [ ] **Step 1: Create README.md**

Create `homework-5/README.md`:

```markdown
# 🔌 Homework 5: Configure MCP Servers

> **Student Name**: Vladyslav Nahirych
> **Date Submitted**: 2026-06-22
> **AI Tools Used**: Claude Code

---

## 📋 Project Overview

Configured four MCP servers to extend Claude Code with external integrations:

- **GitHub MCP** — connects Claude to the `gen-ai-software-engineering` repository for listing PRs, commits, and issues
- **Filesystem MCP** — gives Claude read access to the `homework-5/` directory
- **Notion MCP** — connects Claude to a Notion workspace for querying bug tickets
- **Custom FastMCP** — a hand-built MCP server that exposes a `read` tool returning N words from a lorem ipsum file

The custom server (`custom-mcp-server/server.py`) uses FastMCP with stdio transport and demonstrates both Resources (URI-addressable data) and Tools (callable actions).

---

<div align="center">

*This project was completed as part of the AI-Assisted Development course.*

</div>
```

- [ ] **Step 2: Create HOWTORUN.md**

Create `homework-5/HOWTORUN.md`:

```markdown
# ▶️ How to Run — Homework 5: MCP Servers

## Prerequisites

- **Node.js 18+** — required for `npx` (GitHub, Filesystem, Notion servers)
- **Python 3** — required for the custom FastMCP server
- **Claude Code** — MCP client that reads `.mcp.json`

## 1. Set Environment Variables

Before connecting, set your credentials as environment variables.

**Windows (PowerShell):**
```powershell
$env:GITHUB_PERSONAL_ACCESS_TOKEN = "github_pat_..."
$env:NOTION_API_KEY = "secret_..."
```

**Getting credentials:**
- **GitHub PAT**: go to github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens. Grant read access to the `gen-ai-software-engineering` repo.
- **Notion API key**: go to notion.so/my-integrations → New integration → copy the Internal Integration Secret. Then share your Notion database with the integration.

## 2. Install Custom Server Dependencies

```bash
cd homework-5/custom-mcp-server
pip install -r requirements.txt
```

The external servers (GitHub, Filesystem, Notion) are installed automatically via `npx` on first use — no manual install needed.

## 3. Connect MCP Configuration to Claude Code

Copy or symlink `.mcp.json` to your Claude Code project config location, or add the servers via the Claude Code UI:

In Claude Code, open the project settings and point MCP config to:
```
homework-5/.mcp.json
```

Alternatively, Claude Code auto-discovers `.mcp.json` if it is placed in the project root or opened as a project directory.

## 4. Verify Servers Are Running

Open Claude Code and check the MCP servers panel — all four should show as connected:
- `github` ✓
- `filesystem` ✓
- `notion` ✓
- `custom-lorem` ✓

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

Expected response: first 50 words from lorem-ipsum.md.

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
```

- [ ] **Step 3: Create screenshots placeholder**

Create empty file `homework-5/docs/screenshots/.gitkeep`.

- [ ] **Step 4: Commit**

```bash
git add homework-5/README.md homework-5/HOWTORUN.md homework-5/docs/
git commit -m "feat(hw5): add README, HOWTORUN docs and screenshots placeholder"
```

---

### Task 5: Final verification

- [ ] **Step 1: Verify full project structure**

```bash
find homework-5 -not -path "*/\.*" -not -name "*.pyc" | sort
```

Expected output includes:
```
homework-5/.mcp.json
homework-5/HOWTORUN.md
homework-5/README.md
homework-5/custom-mcp-server/lorem-ipsum.md
homework-5/custom-mcp-server/requirements.txt
homework-5/custom-mcp-server/server.py
homework-5/custom-mcp-server/tests/__init__.py
homework-5/custom-mcp-server/tests/test_server.py
homework-5/docs/screenshots/.gitkeep
```

- [ ] **Step 2: Validate .mcp.json**

```bash
python -c "import json; d=json.load(open('homework-5/.mcp.json')); print('Servers:', list(d['mcpServers'].keys()))"
```

Expected: `Servers: ['github', 'filesystem', 'notion', 'custom-lorem']`

- [ ] **Step 3: Run all tests one final time**

```bash
cd homework-5/custom-mcp-server
python -m pytest tests/ -v
```

Expected: `4 passed`

- [ ] **Step 4: Final commit**

```bash
git add -u
git status
git commit -m "feat(hw5): complete Homework 5 — MCP servers configured and documented"
```

---

## What User Does After Implementation

1. Set `GITHUB_PERSONAL_ACCESS_TOKEN` and `NOTION_API_KEY` env vars
2. Create Notion test database with ~5 bug entries, share with integration
3. Open Claude Code with `homework-5/` as project (`.mcp.json` auto-discovered)
4. Confirm all 4 servers show as connected
5. Run the 4 test prompts from HOWTORUN.md
6. Take screenshots and save to `homework-5/docs/screenshots/`:
   - `github-mcp-result.png`
   - `filesystem-mcp-result.png`
   - `notion-mcp-result.png`
   - `custom-mcp-read-tool-result.png`
7. Commit screenshots and submit PR
