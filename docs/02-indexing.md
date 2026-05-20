# Part 2: Blob Source Documents

Part 2 starts by putting a tiny, safe document set in Azure Blob Storage. Blob
Storage is the durable source of content for the RAG pipeline: later indexing
steps can read source files from one Azure location instead of depending on a
developer's local filesystem.

This checkpoint uploads documents only. It does not create the Azure AI Search
index, chunk text, or call the embedding deployment yet.

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

After `terraform apply`, copy the non-secret storage values from Terraform:

```bash
terraform -chdir=infra output app_env_values
```

Make sure `.env` contains:

```bash
AZURE_RESOURCE_GROUP="rg-smallest-useful-rag-dev"
AZURE_STORAGE_ACCOUNT_NAME="replace-with-storage-account-name"
AZURE_STORAGE_ACCOUNT_URL="https://replace-with-storage-account-name.blob.core.windows.net/"
AZURE_STORAGE_CONTAINER_NAME="rag-documents"
SAMPLE_DOCS_DIR="data/sample-docs"
```

Then get a storage account key from Azure CLI:

```bash
az storage account keys list \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --account-name "$AZURE_STORAGE_ACCOUNT_NAME" \
  --query "[0].value" \
  --output tsv
```

Put that value in your local `.env`:

```bash
AZURE_STORAGE_ACCOUNT_KEY="replace-with-storage-account-key"
```

Do not commit `.env`. `AZURE_STORAGE_ACCOUNT_KEY` is secret.

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

## Preview The Upload

Run a dry run first. This checks the local files without connecting to Azure:

```bash
python scripts/upload_docs.py --dry-run
```

Expected output for the committed sample documents:

```text
Using docs directory: data/sample-docs
Found 4 document(s) to upload.
Would upload harbor-hill-overview.md -> harbor-hill-overview.md (1630 bytes)
Would upload rainwater-planter-pilot.md -> rainwater-planter-pilot.md (1513 bytes)
Would upload repair-kit-lending.md -> repair-kit-lending.md (1659 bytes)
Would upload safety-and-orientation.md -> safety-and-orientation.md (1783 bytes)
Dry run complete. No blobs were uploaded.
```

## Upload To Blob Storage

Run the upload:

```bash
python scripts/upload_docs.py
```

Expected output for the committed sample documents:

```text
Using docs directory: data/sample-docs
Found 4 document(s) to upload.
Using storage account: <your-storage-account-name>
Using storage account URL: https://<your-storage-account-name>.blob.core.windows.net/
Using storage container: rag-documents
Overwrite enabled: existing blobs with the same names will be replaced.
Container ready: rag-documents (already exists).
Uploaded harbor-hill-overview.md -> harbor-hill-overview.md (1630 bytes)
Uploaded rainwater-planter-pilot.md -> rainwater-planter-pilot.md (1513 bytes)
Uploaded repair-kit-lending.md -> repair-kit-lending.md (1659 bytes)
Uploaded safety-and-orientation.md -> safety-and-orientation.md (1783 bytes)
Done. Uploaded 4 document(s), 6585 bytes.
```

The script overwrites blobs with matching names so it is safe to rerun after
editing the local sample documents.

To verify with Azure CLI:

```bash
az storage blob list \
  --account-name "$AZURE_STORAGE_ACCOUNT_NAME" \
  --account-key "$AZURE_STORAGE_ACCOUNT_KEY" \
  --container-name "$AZURE_STORAGE_CONTAINER_NAME" \
  --query "[].name" \
  --output table
```

You should see the four uploaded Markdown filenames.

## Why Blob Storage First

Using Blob Storage as the source location keeps the later indexing flow clear:

- local files are the teaching fixtures;
- Blob Storage is the Azure source of record;
- Azure AI Search will store chunked and searchable records derived from those
  source documents;
- retrieval and chat will cite records that can be traced back to source blob
  names.

This separation matters even in a small sample. Source documents and search
records have different lifecycles: you can rebuild the search index without
changing the original files in Blob Storage.
