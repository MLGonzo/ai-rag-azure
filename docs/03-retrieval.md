# Part 3: Retrieval Before Answering

Part 3 queries the Azure AI Search index created in Part 2 and prints the
retrieved chunks before any LLM answering is added.

This is a useful checkpoint because RAG quality starts with retrieval. If the
right context is not retrieved, a chat model has little chance of producing a
grounded answer. Inspecting chunks first makes it easier to catch indexing
mistakes, weak queries, missing documents, bad chunk sizes, and source metadata
problems before adding another moving part.

## Prerequisites

Complete Part 2 first:

```bash
python scripts/upload_docs.py
python scripts/create_index.py
python scripts/run_indexer.py
```

Install dependencies from the repo root if your virtual environment is not
already ready:

```bash
python -m pip install -r app/requirements.txt
```

## Configuration

The retrieval script uses the same `.env` values as indexing:

```bash
AZURE_SEARCH_ENDPOINT="https://your-search-service.search.windows.net"
AZURE_SEARCH_INDEX_NAME="smallest-useful-rag"
AZURE_SEARCH_API_KEY="replace-with-your-search-admin-or-query-key"
AZURE_OPENAI_ENDPOINT="https://your-azure-openai-resource.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2024-10-21"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-small"
AZURE_OPENAI_API_KEY="replace-with-your-azure-openai-key"
RETRIEVAL_MODE="hybrid"
RETRIEVAL_TOP_K="5"
RETRIEVAL_PREVIEW_CHARS="500"
```

Vector and hybrid retrieval call `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, the same
embedding deployment used by `scripts/run_indexer.py`. Keyword retrieval does
not need the Azure OpenAI values.

## Run Retrieval

Pass a question as command-line arguments:

```bash
python scripts/retrieve.py "What does the repair kit lending program include?"
```

Or run the script without a question and enter one at the prompt:

```bash
python scripts/retrieve.py
```

The default mode is hybrid. You can choose a mode explicitly:

```bash
python scripts/retrieve.py --mode keyword "When is orientation required?"
python scripts/retrieve.py --mode vector "What labels are used for planters?"
python scripts/retrieve.py --mode hybrid "How long can someone borrow a repair kit?"
```

Change the result count with `--top-k`:

```bash
python scripts/retrieve.py --top-k 3 "What happens at Harbor Hill?"
```

## Expected Output Shape

The exact scores can vary by Search service version and index contents, but the
output should show the query settings and then one block per retrieved chunk:

```text
Using Search endpoint: https://your-search-service.search.windows.net
Using embedding deployment: text-embedding-3-small
Question: How long can someone borrow a repair kit?
Retrieval mode: hybrid
Search index: smallest-useful-rag
Embedding deployment: text-embedding-3-small
Chunks returned: 5

[1] score=0.0333
Source: repair-kit-lending.md (repair-kit-lending.md)
Chunk: 1  id=2f0f...
Preview: # Repair Kit Lending The workshop lends repair kits...
```

Each result includes:

- `score`: Azure AI Search relevance score for that query mode.
- `source`: source filename and blob name.
- `chunk`: 1-based chunk number and stable chunk id.
- `preview`: the beginning of the indexed chunk content.

Read the previews before building a chat answer. If the expected facts are not
present in the retrieved chunks, fix retrieval, chunking, or the source content
first.

## Retrieval Modes

Keyword retrieval searches the `content` text field. It is often strong for
exact terms such as program names, dates, part numbers, and policy wording.

Vector retrieval embeds the question and searches `content_vector`. It is often
stronger when the wording of the question differs from the wording in the
document.

Hybrid retrieval sends both the keyword query and the vector query to Azure AI
Search. For this lesson it is the default because it keeps exact text matching
and semantic similarity in one simple command.

## Troubleshooting

If keyword retrieval works but vector or hybrid retrieval fails, check the Azure
OpenAI settings in `.env` and confirm that the embedding deployment name matches
the deployment used when running `scripts/run_indexer.py`.

If results are empty, rerun Part 2 indexing:

```bash
python scripts/create_index.py --reset
python scripts/run_indexer.py
```

If scores look low but previews contain the right facts, continue. Search scores
are ranking signals, not percentages.
