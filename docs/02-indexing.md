# Part 2: Blob Source Documents and Search Indexing

Part 2 puts a tiny, safe document set in Azure Blob Storage, then turns those
source documents into searchable Azure AI Search records.

The flow is deliberately direct:

1. Upload local Markdown files to Blob Storage.
2. Create an Azure AI Search index with text, metadata, and vector fields.
3. Read text blobs with Python.
4. Split each blob into deterministic chunks.
5. Create an embedding for each chunk.
6. Upload chunk records to Azure AI Search.

## What Gets Uploaded

The source files live in `data/sample-docs/`. They are original Markdown
documents about a fictional community workshop called Harbor Hill Community
Workshop.

The upload script skips `data/sample-docs/README.md` and uploads:

- `harbor-hill-overview.md`
- `rainwater-planter-pilot.md`
- `repair-kit-lending.md`
- `safety-and-orientation.md`

These files are useful for grounded-answer testing because they contain
specific facts such as opening hours, lending periods, orientation rules,
planter labels, and next actions.

## Configuration

Copy `.env.example` to `.env` if you have not already done so:

```bash
cp .env.example .env
```

After `terraform apply`, copy the non-secret values from Terraform:

```bash
terraform -chdir=infra output app_env_values
```

Make sure `.env` contains the Blob Storage, Azure AI Search, and Azure OpenAI
values for your resources:

```bash
AZURE_STORAGE_ACCOUNT_NAME="replace-with-storage-account-name"
AZURE_STORAGE_ACCOUNT_URL="https://replace-with-storage-account-name.blob.core.windows.net/"
AZURE_STORAGE_CONTAINER_NAME="rag-documents"
AZURE_SEARCH_ENDPOINT="https://your-search-service.search.windows.net"
AZURE_SEARCH_INDEX_NAME="smallest-useful-rag"
AZURE_OPENAI_ENDPOINT="https://your-azure-openai-resource.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2024-10-21"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-small"
AZURE_OPENAI_EMBEDDING_DIMENSIONS="1536"
SAMPLE_DOCS_DIR="data/sample-docs"
CHUNK_SIZE="800"
CHUNK_OVERLAP="120"
INDEXER_BATCH_SIZE="16"
```

Then add the secret keys to your local `.env`. Do not commit `.env`.

Storage account key:

```bash
az storage account keys list \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --account-name "$AZURE_STORAGE_ACCOUNT_NAME" \
  --query "[0].value" \
  --output tsv
```

Search admin key:

```bash
az search admin-key show \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --service-name "<search-service-name-from-terraform-output>" \
  --query primaryKey \
  --output tsv
```

Azure OpenAI key:

```bash
az cognitiveservices account keys list \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "<openai-account-name-from-terraform-output>" \
  --query key1 \
  --output tsv
```

Put those values in `.env`:

```bash
AZURE_STORAGE_ACCOUNT_KEY="replace-with-storage-account-key"
AZURE_SEARCH_API_KEY="replace-with-search-admin-key"
AZURE_OPENAI_API_KEY="replace-with-your-azure-openai-key"
```

`AZURE_OPENAI_EMBEDDING_DIMENSIONS` must match both the embedding deployment and
the Search index vector field. The default `1536` matches
`text-embedding-3-small` when no custom dimensions are requested.

## Install Dependencies

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/requirements.txt
```

If you already created the virtual environment in Part 1, reactivate it and run
only the final install command.

## Upload To Blob Storage

Run a dry run first. This checks the local files without connecting to Azure:

```bash
python scripts/upload_docs.py --dry-run
```

Then upload the sample documents:

```bash
python scripts/upload_docs.py
```

Expected output for the committed sample documents ends with:

```text
Done. Uploaded 4 document(s), 6585 bytes.
```

The upload script overwrites blobs with matching names, so it is safe to rerun
after editing the local sample documents.

## Create The Search Index

Create the Azure AI Search index:

```bash
python scripts/create_index.py
```

Expected output ends with:

```text
Done. Search index is ready: smallest-useful-rag
```

The index contains:

- `id`: stable chunk key.
- `content`: searchable chunk text.
- `content_vector`: embedding vector for vector search.
- `source_blob_name`: original blob name.
- `source_filename`: original filename.
- `chunk_number`: 1-based chunk number within the source blob.

Use `--reset` if you want to delete all indexed chunks and recreate the index:

```bash
python scripts/create_index.py --reset
```

## Preview Chunking

Run the indexer dry run:

```bash
python scripts/run_indexer.py --dry-run
```

This reads the configured Blob container and chunks supported text blobs, but it
does not call the embedding deployment and does not upload to Search.

Expected counts for the committed sample documents with the default chunking
settings:

```text
Blobs read: 4
Chunks created: 12
Dry run complete. No embeddings were created and no chunks were indexed.
Done. Blobs read: 4. Chunks created: 12. Chunks indexed: 0.
```

## Run The Indexer

Index the chunks:

```bash
python scripts/run_indexer.py
```

Expected counts for the committed sample documents:

```text
Blobs read: 4
Chunks created: 12
Indexed batch 1: 12 chunk(s)
Done. Blobs read: 4. Chunks created: 12. Chunks indexed: 12.
```

The indexer supports UTF-8 `.md`, `.txt`, `.csv`, and `.json` blobs. It skips
other file extensions because this lesson does not include PDF, Word, OCR, or
HTML extraction.

## Chunking Rules

Chunking is intentionally simple and deterministic:

- Normalize line endings to `\n`.
- Trim leading and trailing whitespace from the whole document.
- Take `CHUNK_SIZE` characters for each chunk.
- Move forward by `CHUNK_SIZE - CHUNK_OVERLAP` characters.
- Trim whitespace around each chunk.
- Number chunks from `1` for each blob.

With the defaults, each chunk is at most 800 characters, and the next chunk
repeats the previous 120 characters. This overlap helps retrieval when an
answer-relevant sentence lands near a chunk boundary.

This is not token-aware and it can split a sentence or word. That tradeoff is
acceptable here because the documents are tiny and the goal is to make every
step visible. Later production code would usually use a token-aware splitter,
format-specific extraction, and stronger metadata handling.

## Rerunning Safely

`scripts/run_indexer.py` creates a stable Search document `id` from the blob
name and chunk number. Re-running the indexer overwrites those same chunk
records with `upload_documents`.

That is safe enough for the lesson when you edit a document and rerun the
script. If you delete a source blob, rename a blob, or make a document much
shorter, old chunk records can remain in the index. For a clean rebuild, run:

```bash
python scripts/create_index.py --reset
python scripts/run_indexer.py
```

## Why Simple Python Ingestion

Azure AI Search also supports managed indexers, data sources, skillsets,
integrated vectorization, and enrichment pipelines. Those are useful when you
want Azure to schedule ingestion, crawl Blob Storage, crack documents, call
skills, and manage more of the pipeline.

This checkpoint uses a small Python ingestion script instead because it keeps
the learning surface visible:

- learners can see exactly which blobs are read;
- chunking is a short Python function;
- embedding calls are explicit;
- Search upload records are plain dictionaries;
- rerun behavior is easy to reason about.

The cost is that this script is not a production ingestion service. It has no
scheduler, no incremental deletion tracking, no PDF parsing, no OCR, no retry
policy beyond the SDK defaults, and no managed enrichment pipeline. For a
larger or more automated system, compare this code with Azure AI Search managed
indexers and skillsets before choosing the ingestion design.
