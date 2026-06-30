# Semantic Index

This folder contains generated semantic search artifacts for IoTables documentation.

The source of truth remains the Markdown documentation under `docs/`. The JSONL index is a deterministic, rebuildable cache for search, LLM context retrieval, and later code/test traceability.

## Files

| File | Purpose |
| --- | --- |
| [index.jsonl](index.jsonl) | Generated semantic records, one JSON object per Markdown section. |

## Build Command

Run from the repository root:

```powershell
python tools/build_semantic_index.py
```

The script reads Markdown files under `docs/` and writes `docs/semantic/index.jsonl`.

## Record Shape

Each JSONL row contains:

| Field | Meaning |
| --- | --- |
| `schema_version` | JSONL record schema version. |
| `semantic_id` | Stable ID derived from documentation path and heading context. |
| `title` | Current section title. |
| `heading_path` | Full Markdown heading context. |
| `metadata.layer` | `app`, `module`, `data`, `database`, `api`, or `documentation`. |
| `metadata.kind` | More specific document type such as `app`, `module_contract`, `module_api`, or `database`. |
| `metadata.app` | App owner when the source path is app-specific. |
| `metadata.module_context` | Module context when the source path is module-owned. |
| `metadata.module` | Module name when available. |
| `source.path` | Markdown source file. |
| `source.start_line`, `source.end_line` | Source line range for direct inspection. |
| `symbols` | Extracted app names, module commands, HTTP endpoints, and snake_case identifiers. |
| `links` | Markdown links found in the section. |
| `content_hash` | SHA-256 hash of the section text. |
| `text` | Original Markdown section text. |
| `embedding_text` | Search/embedding-ready text with source context. |
| `token_estimate` | Rough token estimate for retrieval chunking. |

## Usage Rules

- Do not edit `index.jsonl` manually.
- Update the owning Markdown source, then regenerate the index.
- Treat JSONL as a local search and retrieval cache, not as product truth.
- Prefer exact `semantic_id`, symbol, path, app, module, or endpoint filters before vector similarity.
- Use vector search for semantic discovery such as "where did we define duplicate submit safety?"
- Keep records small enough to retrieve as LLM context without loading entire documents.

## Code and Test Traceability

When implementation starts, code and tests may reference semantic IDs in comments, test names, or metadata.

Examples:

```text
semantic_id: module.docs-modules-ordering-customer-ordering-contracts.module-contracts-customer-ordering-commands
semantic_id: app.docs-apps-shared-master-end-to-end.v1-end-to-end-app-flow-main-happy-path-5-customer-submits-order
```

The reference direction is one-way: code and tests can point to semantic documentation, but documentation remains the source that defines behavior.

## Embeddings

V1 stores embedding-ready JSONL only. It does not store vector values in the repository.

If a vector store is added later, it must be built from `index.jsonl` and remain disposable. The vector store must never become the source of truth.
