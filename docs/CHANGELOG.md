# Changelog

## [Unreleased]

### Added
- **CLI wrapper spec** (`specs/palinode-cli-spec.md`) — full `palinode` CLI wrapping REST API via Click
  - Commands: search, save, status, diff, consolidate, trigger, doctor
  - TTY-aware output (human text vs piped JSON)
  - Remote access via `PALINODE_API` env var or SSH
- **5060 GPU usage plane spec** (`specs/5060-usage-plane.md`) — VRAM budget for embeddings + transcription + general LLM
- **Architecture decision: CLI vs MCP** — CLI for agents/scripts/cron (8x fewer tokens), MCP for IDEs only
- Updated README architecture diagram to show CLI path
- Updated ROADMAP with Phase 1.25 (CLI + interface rationalization)
- Updated FEATURE-STATUS with CLI entry
- `palinode read` command — read memory files with optional `--meta` frontmatter parsing
- `palinode session-end` command — capture session outcomes to daily notes + project status

### Changed
- Removed API keys from systemd service files — all inference uses local Ollama/vLLM

### Infrastructure
- Configured Palinode MCP on calarts-mbp for Claude Desktop, Claude CLI, Antigravity IDE, Cursor

## [0.1.0] — 2026-03-22

### 🎉 MVP Launch

**Palinode is live.** Persistent memory that makes AI agents smarter over time.

### What's Working

**Python Core (palinode/)**
- SQLite-vec vector store with BGE-M3 embeddings (1024d, via Ollama)
- File watcher daemon — auto-indexes markdown files on create/modify/delete
- FastAPI server — `/search`, `/save`, `/status`, `/reindex` endpoints
- Markdown parser — YAML frontmatter extraction + heading-level section chunking
- CLI — `search` and `stats` commands

**OpenClaw Plugin (plugin/)**
- Core memory injection at session start (Phase 1: `core: true` files)
- Topic-specific context retrieval (Phase 2: vector search on first message)
- Three tools: `palinode_search`, `palinode_save`, `palinode_status`
- Session capture to daily notes on `agent_end`
- Reads extraction prompts from `specs/prompts/*.md` (not hardcoded)
- Reads `PROGRAM.md` for behavioral policy at runtime
- Runs alongside Mem0 without conflict

**Infrastructure**
- Systemd user services: `palinode-api` (port 6340) + `palinode-watcher`
- Enabled for boot survival
- Graceful degradation: Ollama down → files still readable; DB down → grep still works

### Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Source of truth | Markdown files, git-versioned | Human-readable, survives everything |
| Vector store | SQLite-vec (embedded) | No server, matches file-based philosophy |
| Embeddings (core) | BGE-M3 via Ollama on ***REMOVED***61 | Local, private, top-tier for structured text |
| Embeddings (future) | gemini-embedding-2-preview | Multimodal, Matryoshka dims, for research ingestion |
| OpenClaw integration | General plugin (not memory slot) | Runs alongside Mem0 during transition |
| Prompts | Read from specs/prompts/*.md files | Version-controlled, editable, diffable |

### Known Limitations

- Research docs not indexed yet (large files)
- No WAL mode on SQLite — concurrent writes can lock
- `agent_end` capture writes raw session text to daily/ — no LLM extraction yet (needs `api.llm` or external call)
- No consolidation cron yet (Phase 2)
- No entity linking yet (Phase 2)

### What's Next

See `PLAN.md` for the full roadmap:
- Phase 0.5: Capture expansion (Slack, Telegram, MBP watch folder, ingestion pipeline)
- Phase 1: Core memory files + retire MEMORY.md
- Phase 2: Weekly consolidation + entity linking + insights extraction
- Phase 3: Backfill from Mem0 (2,632 memories) + QC MCP (14K contexts)
- Phase 4: MCP server for cross-tool access
