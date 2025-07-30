# P6XER MCP Server

This is the Model Context Protocol (MCP) Server for P6 XER files, built on top of [PyP6XER](https://github.com/HassanEmam/PyP6Xer).

It exposes machine-readable MCP manifests for PyP6XER's modules for use by AI models such as:

- XER Parser
- XER Analyzer  
- XER Converter

## 🚀 Features

### 🔧 Tools

- **`parse_xer_file(file_path)`** - Parse Primavera P6 XER files and extract basic project information
- **`get_project_activities(file_path, project_id?)`** - Get activities from XER files, optionally filtered by project
- **`get_critical_path(file_path, project_id?)`** - Find critical path activities (zero or negative total float)
- **`analyze_resource_utilization(file_path)`** - Analyze resource allocation, hours, and costs
- **`check_schedule_quality(file_path, project_id?)`** - Perform schedule quality checks and identify issues

### 📋 Resources

- **`xer-project://{file_path}/{project_id}`** - Get detailed information about a specific project
- **`xer-activities://{file_path}`** - Get comprehensive activities summary with status breakdown
- **`xer-resources://{file_path}`** - Get resources summary with type breakdown and assignment statistics

### 💬 Prompts

- **`analyze_xer_project(file_path, analysis_type)`** - Generate analysis prompts for different types of project analysis
  - Analysis types: `general`, `schedule`, `resources`, `progress`, `quality`
- **`xer_reporting_prompt(file_path, report_type)`** - Generate prompts for creating professional project reports
  - Report types: `executive`, `detailed`, `critical_path`, `resource`, `milestone`

## � Installation

```bash
# Clone the repository
git clone https://github.com/osama-ata/p6xer-mcp-server.git
cd p6xer-mcp-server

# Install dependencies using uv (recommended)
uv sync

# Or install using pip
uv pip install mcp[cli] pyp6xer
```

## �🚀 Running the standalone MCP development tools

```bash
uv run mcp
```

Open in your browser:

- MCP server status: <http://localhost:8000>
- Development tools interface

## 🏃‍♂️ Quick Start

1. **Start the MCP server:**

   ```bash
   uv run --with mcp mcp run server.py
   ```

2. **Connect from your AI assistant or MCP client**

3. **Use the tools:** Parse XER files, analyze critical paths, check resource utilization, and generate comprehensive reports

## 📊 What You Can Analyze

- **Project Overview**: Basic project information, activities count, resources, calendars
- **Critical Path Analysis**: Activities with zero or negative float, schedule risks
- **Resource Utilization**: Resource allocation, hours, costs, over-allocation detection
- **Schedule Quality**: Missing predecessors/successors, long duration activities, logic issues
- **Progress Tracking**: Activity status, completion percentages, schedule performance

## 🎯 Use Cases

- **Project Management**: Schedule analysis, resource optimization, progress tracking
- **Quality Assurance**: Schedule quality checks, best practices validation
- **Reporting**: Executive summaries, detailed analysis reports, milestone tracking
- **Data Integration**: Extract P6 data for external systems and dashboards

## 📋 Example Workflow

1. **Parse XER File**: `parse_xer_file("project.xer")` → Get basic project info
2. **Analyze Critical Path**: `get_critical_path("project.xer", "PROJECT_ID")` → Find critical activities  
3. **Check Resources**: `analyze_resource_utilization("project.xer")` → Review resource allocation
4. **Quality Check**: `check_schedule_quality("project.xer")` → Identify schedule issues
5. **Generate Report**: Use prompts to create comprehensive analysis reports
