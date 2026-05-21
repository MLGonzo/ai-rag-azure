# Scripts

Small local automation scripts for the learning path.

## Available Scripts

### `upload_docs.py`

Uploads files from `data/sample-docs/` to the configured Azure Blob Storage
container. It reads `.env`, skips `data/sample-docs/README.md`, and prints
progress without printing secrets.

From the repo root:

```bash
python scripts/upload_docs.py --dry-run
python scripts/upload_docs.py
```

### `create_index.py`

Creates or updates the Azure AI Search index used by the sample. The index has
plain metadata fields, searchable chunk text, and a vector field named
`content_vector`.

From the repo root:

```bash
python scripts/create_index.py
```

Use `--reset` when you want to delete indexed chunks and recreate the index:

```bash
python scripts/create_index.py --reset
```

### `run_indexer.py`

Reads supported UTF-8 text blobs from the configured container, chunks them,
embeds each chunk with the configured embedding deployment, and uploads chunk
documents to Azure AI Search.

From the repo root:

```bash
python scripts/run_indexer.py --dry-run
python scripts/run_indexer.py
```

The script uses stable chunk IDs based on blob name and chunk number, so
rerunning it overwrites the same chunk records.

Scripts that create, update, or delete Azure resources should print what they are about to do and should not hide destructive operations.
