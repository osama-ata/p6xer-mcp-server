# P6XER MCP Server

[![PyPI version](https://badge.fury.io/py/p6xer-mcp-server.svg)](https://badge.fury.io/py/p6xer-mcp-server)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)

A full-featured [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for **Primavera P6 XER** files, built on [PyP6XER](https://github.com/HassanEmam/PyP6Xer).

Exposes **13 Tools**, **3 Resources**, and **2 Prompts** so any MCP-compatible AI client (Claude Desktop, Claude Code, Cursor, etc.) can interactively parse, query, and analyze `.xer` schedule files.

---

## 🚀 Features

### 🔧 Tools (13)

| Tool | Description |
|------|-------------|
| `parse_xer_file` | Parse an XER file — project list, totals, status breakdowns |
| `get_project_activities` | Activities with filters: project_id, project_short_name, status, task_type |
| `get_critical_path` | Critical path activities (float ≤ 0), sorted by early start |
| `analyze_resource_utilization` | Planned/actual hours & costs per resource; over-allocation flags |
| `check_schedule_quality` | DCMA-style check: missing logic, long durations, high float, unresourced tasks |
| `get_resources` | List resources, optionally filtered by type |
| `get_resource_assignments` | Resource–activity assignments with enriched names and costs |
| `get_wbs` | Work Breakdown Structure hierarchy |
| `get_relationships` | Predecessor/successor relationships enriched with task codes |
| `get_calendars` | Calendar definitions with hours-per-period data |
| `get_schedule_summary` | At-a-glance stats: counts, date range, critical count |
| `get_earned_value` | EVM: PV, EV, AC, CV, SV, CPI, SPI, EAC per project |
| `get_activity_detail` | Full detail for one activity (preds + succs + resources) |

### 📋 Resources (3)

| URI | Description |
|-----|-------------|
| `xer-project://{file_path}/{project_id}` | Detailed text summary of a specific project |
| `xer-activities://{file_path}` | Activities summary with status breakdown and duration stats |
| `xer-resources://{file_path}` | Resources summary with type breakdown and assignment stats |

### 💬 Prompts (2)

| Prompt | Types |
|--------|-------|
| `analyze_xer_project` | `general` · `schedule` · `resources` · `progress` · `quality` |
| `xer_reporting_prompt` | `executive` · `detailed` · `critical_path` · `resource` · `milestone` |

---

## � Install from Store

### Via PyPI (uvx — no install needed)
```bash
uvx p6xer-mcp-server
```

### Via PyPI (pip)
```bash
pip install p6xer-mcp-server
p6xer-mcp-server
```

### Via Smithery
Search for `p6xer-mcp-server` on [smithery.ai](https://smithery.ai) and click Install.
It will generate the correct Claude Desktop config automatically.

### Via GitHub MCP Registry
The server is listed in the GitHub MCP Registry. In Claude Code:
```bash
claude mcp add p6xer -- uvx p6xer-mcp-server
```

### Claude Desktop config (after PyPI install)
```json
{
  "mcpServers": {
    "p6xer": {
      "command": "uvx",
      "args": ["p6xer-mcp-server"]
    }
  }
}
```

---

## �📦 Installation

```bash
# Clone the repo
git clone https://github.com/your-org/p6xer-mcp-server.git
cd p6xer-mcp-server

# Install with uv (recommended)
uv sync

# Or with pip
pip install "mcp[cli]>=1.12.2" pyp6xer
```

---

## 🏃 Running

**Development / MCP Inspector:**
```bash
uv run --with mcp mcp run src/server.py
```

**Stdio (Claude Desktop / Claude Code):**
```bash
python src/server.py
```

---

## 🔌 Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "p6xer": {
      "command": "python",
      "args": ["/absolute/path/to/p6xer-mcp-server/src/server.py"]
    }
  }
}
```

Config file locations:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

## 🔌 Claude Code (CLI)

```bash
claude mcp add p6xer -- python /absolute/path/to/p6xer-mcp-server/src/server.py
```

---

## 💬 Example Prompts

Once connected:

```
Parse project.xer and give me an overview of all projects

What are all the critical path activities, sorted by start date?

Run a DCMA schedule quality check on project.xer

Calculate earned value metrics — what are the CPI and SPI?

Show all resource assignments for "John Smith"

What are the predecessors and successors of activity A1000?

List all over-allocated labor resources

Generate an executive summary report for project.xer
```

---

## 📊 Tool Reference

### Filter parameters (most tools accept)
- `project_id` – numeric P6 project ID (e.g. `"1234"`)
- `project_short_name` – project short name string (e.g. `"PROJ1"`)

### Status codes
`TK_NotStart` · `TK_Active` · `TK_Complete`

### Task types
`TT_Task` · `TT_Mile` · `TT_FinMile` · `TT_WBS`

### Resource types
`RT_Labor` · `RT_Mat` · `RT_Equip`

---

## 🗂️ Project Structure

```
p6xer-mcp-server/
├── src/
│   └── server.py       # All tools, resources, and prompts
├── pyproject.toml
└── README.md
```

---

## 📋 Requirements

- Python ≥ 3.12
- `mcp[cli] >= 1.12.2`
- `pyp6xer >= 1.16.0`

---

## 📄 License

MIT
