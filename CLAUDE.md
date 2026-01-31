# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**semi-autocad** - A system for semi-automatic CAD operations using Claude Code as orchestrator, Onshape as CAD engine, and Neo4j for persistent memory/knowledge graph.

## Architecture

```
Claude Code (Orchestrator)
    ├── MCP Servers
    │   ├── neo4j-memory (bolt://localhost:7688) - Knowledge graph for designs, decisions, patterns
    │   ├── neo4j-cypher - Direct Cypher queries
    │   ├── playwright - Browser automation for Onshape web UI
    │   └── sequential-thinking - Complex reasoning
    │
    └── Onshape API
        ├── REST API (https://cad.onshape.com/api/v6/)
        ├── OAuth2 Authentication
        └── FeatureScript (parametric features)
```

## MCP Configuration

Project uses local `.claude/settings.json` with dedicated Neo4j instance:
- **Container**: `neo4j-semicad`
- **Bolt**: `bolt://localhost:7688`
- **Browser**: `http://localhost:7475`
- **Credentials**: `neo4j` / `semicad2026`

## Key Research Areas

1. **Onshape REST API** - Core CAD operations (parts, assemblies, features)
2. **Onshape OAuth2** - Authentication flow for API access
3. **FeatureScript** - Custom parametric features
4. **Playwright + Onshape** - UI automation for operations not exposed via API
5. **CAD Knowledge Graph** - Storing design patterns, decisions, parametric relationships

## External Resources

- Onshape API Docs: https://onshape-public.github.io/docs/
- Onshape Developer Portal: https://dev-portal.onshape.com/
