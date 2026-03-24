# Changelog

## [0.1.2] - 2026-03-24
### Fixed
- `FastMCP` initialization by removing unsupported `title` keyword argument from `src/p6xer_mcp_server/server.py` and moving it into `instructions` text.
- Addressed startup crash `TypeError: FastMCP.__init__() got an unexpected keyword argument 'title'`.

## [0.1.1] - prior release (already tagged)
- Baseline MCP server functionality for parsing Primavera P6 XER files.
