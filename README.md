# P6XER MCP Server

This is the Model Context Protocol (MCP) Server for P6 XER files, built on top of [PyP6XER](https://github.com/HassanEmam/PyP6Xer).

It exposes machine-readable MCP manifests for PyP6XER's modules for use by AI models such as:
- XER Parser
- XER Analyzer
- XER Converter

## 🚀 How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
uvicorn main:app --reload
```

3. Open in your browser:

- List models: http://localhost:8000/models

- Specific model MCP: http://localhost:8000/models/xer_parser/mcp.json
