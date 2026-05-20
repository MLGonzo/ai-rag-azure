# Scripts

Automation scripts are added as the series grows.

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

Scripts that create, update, or delete Azure resources should print what they are about to do and should not hide destructive operations.
