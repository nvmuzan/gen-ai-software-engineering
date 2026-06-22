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
