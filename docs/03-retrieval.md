# Part 3: Retrieval Before Answering

Part 3 queries the Azure AI Search index created in Part 2 and prints the
retrieved chunks before any LLM answering is added.

This is a useful checkpoint because RAG quality starts with retrieval. If the
right context is not retrieved, a chat model has little chance of producing a
grounded answer. Inspecting chunks first makes it easier to catch indexing
mistakes, weak queries, missing documents, bad chunk sizes, and source metadata
problems before adding another moving part.

The goal is not to build a heavy evaluation framework. The goal is to give
learners a small set of known questions, expected sources, and repeatable
debugging steps they can use while watching retrieval happen.

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

## What Good Retrieval Looks Like

For this lesson, retrieval is good enough when:

- the expected source document appears near the top of the results;
- the preview contains the specific fact needed to answer the question;
- the `source_filename`, `source_blob_name`, and `chunk_number` fields are
  present;
- keyword, vector, and hybrid modes behave in ways you can explain.

Do this inspection before asking an LLM to answer. If the needed fact is not in
the retrieved chunks, the next step is retrieval debugging, not prompt tuning.

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

## Sample Questions

The committed sample documents produce 12 chunks with the default Part 2
settings, `CHUNK_SIZE=800` and `CHUNK_OVERLAP=120`. Use the table below as a
practical retrieval-quality checklist.

Scores and exact ordering can vary. Treat the expected chunk as a target, not a
hard assertion. If the expected chunk appears in the top few results and its
preview contains the listed fact, retrieval is doing its job for that question.

| Question | Expected source and chunk | Fact to find in the preview |
| --- | --- | --- |
| What days is Harbor Hill open? | `harbor-hill-overview.md`, chunk 1 | Tuesdays and Thursdays 4:00 PM to 8:00 PM; Saturdays 10:00 AM to 3:00 PM |
| Where is Harbor Hill located? | `harbor-hill-overview.md`, chunk 1 | 17 Cedar Quay in the fictional Dockside neighborhood |
| How can someone cover membership without paying the monthly fee? | `harbor-hill-overview.md`, chunk 1 or 2 | volunteering for two approved workshop hours during the same month |
| What are the three main workshop areas? | `harbor-hill-overview.md`, chunk 2 | bench room, clean table, materials shelf |
| What does the starter repair kit include? | `repair-kit-lending.md`, chunk 1 | screwdriver, wrench, tape measure, pencil, painter's tape, safety glasses, checklist |
| How long can a member borrow a starter repair kit? | `repair-kit-lending.md`, chunk 1 or 2 | seven calendar days, with one possible seven-day extension before the original due date |
| Which tote is reserved for first-time borrowers? | `repair-kit-lending.md`, chunk 2 | Orange tote: Kit C |
| What should members do if a tool is missing or damaged? | `repair-kit-lending.md`, chunk 3 | tell the shift lead when the kit is returned |
| Which rainwater planter needs a valve inspection? | `rainwater-planter-pilot.md`, chunk 1 or 3 | Planter R3, next to the notice board |
| What are volunteers not supposed to record during planter checks? | `rainwater-planter-pilot.md`, chunk 1 or 2 | names, phone numbers, license plates, or images of visitors |
| What should volunteers do if standing water remains for more than two days after rain? | `rainwater-planter-pilot.md`, chunk 2 | tell the Saturday shift lead |
| What approval is needed before using the soldering station? | `safety-and-orientation.md`, chunk 1 | basic orientation plus a five-minute heat safety check |
| What safety gear is required when drilling or hammering? | `safety-and-orientation.md`, chunk 2 | safety glasses |
| What does "reset the bench" mean? | `safety-and-orientation.md`, chunk 3 | put tools back, sweep debris, wipe the surface, report broken or missing items |

Try a few of these after every indexing change:

```bash
python scripts/retrieve.py --top-k 3 "What days is Harbor Hill open?"
python scripts/retrieve.py --top-k 3 "Which tote is reserved for first-time borrowers?"
python scripts/retrieve.py --top-k 3 "What should volunteers do if standing water remains for more than two days after rain?"
python scripts/retrieve.py --top-k 3 "What does reset the bench mean?"
```

## Retrieval Modes

Keyword retrieval searches the `content` text field. It is often strong for
exact terms such as program names, dates, part numbers, and policy wording.

Vector retrieval embeds the question and searches `content_vector`. It is often
stronger when the wording of the question differs from the wording in the
document.

Hybrid retrieval sends both the keyword query and the vector query to Azure AI
Search. For this lesson it is the default because it keeps exact text matching
and semantic similarity in one simple command.

## Compare Keyword, Vector, And Hybrid

Use the same question with each mode and compare the printed chunks:

```bash
QUESTION="Which rainwater planter needs a valve inspection?"

python scripts/retrieve.py --mode keyword --top-k 3 "$QUESTION"
python scripts/retrieve.py --mode vector --top-k 3 "$QUESTION"
python scripts/retrieve.py --mode hybrid --top-k 3 "$QUESTION"
```

Then try a more paraphrased question:

```bash
QUESTION="What outdoor container by the notice board needs someone to check a valve?"

python scripts/retrieve.py --mode keyword --top-k 3 "$QUESTION"
python scripts/retrieve.py --mode vector --top-k 3 "$QUESTION"
python scripts/retrieve.py --mode hybrid --top-k 3 "$QUESTION"
```

When comparing the outputs, look for:

- whether `rainwater-planter-pilot.md` appears in the top results;
- whether chunk 1 or chunk 3 contains the R3 valve-inspection fact;
- whether keyword mode drops when the query avoids exact words like
  `rainwater`, `planter`, or `valve`;
- whether vector mode finds the right topic even with different wording;
- whether hybrid keeps exact-match strength while still helping with paraphrase.

Repeat the comparison with exact and paraphrased versions of other sample
questions:

| Exact question | Paraphrased question | Expected source |
| --- | --- | --- |
| How long can a member borrow a starter repair kit? | When does a borrowed home repair set have to come back? | `repair-kit-lending.md`, chunk 1 or 2 |
| What approval is needed before using the soldering station? | What extra check is required for hot electronics work? | `safety-and-orientation.md`, chunk 1 |
| What are the three main workshop areas? | Which spaces make up the workshop? | `harbor-hill-overview.md`, chunk 2 |

Keyword search can win on exact terms. Vector search can win on paraphrase.
Hybrid search should often be the most forgiving option for this small lesson
index, but do not assume it is magic. Read the chunks.

## Inspect Before Asking The LLM

Use this quick routine when a question behaves unexpectedly:

1. Run retrieval with `--top-k 3`.
2. Check the `Source` and `Chunk` lines before reading the preview.
3. Confirm the preview actually contains the fact needed for the answer.
4. Increase `--preview-chars` if the answer might be just outside the visible
   snippet.
5. Run the same question in keyword, vector, and hybrid modes.
6. Rewrite one weak query into a more specific query and compare again.
7. Only move to LLM answering after the needed chunks are visible.

Useful commands:

```bash
python scripts/retrieve.py --mode hybrid --top-k 3 --preview-chars 900 "What does the starter repair kit include?"
python scripts/retrieve.py --mode keyword --top-k 5 "Orange tote Kit C"
python scripts/retrieve.py --mode vector --top-k 5 "borrowed home repair set return deadline"
```

## Common Retrieval Failure Modes

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| The answer is in the source document, but not in any retrieved preview. | Poor chunking or weak query. | Run `python scripts/run_indexer.py --dry-run`, inspect chunk counts, increase `--top-k`, and try a query with source terms from the document. |
| The right text appears, but `Source` says `unknown` or chunk numbers are missing. | Missing metadata in indexed records or a mismatched index schema. | Recreate the index with `python scripts/create_index.py --reset`, then rerun `python scripts/run_indexer.py`. |
| Keyword retrieval works, but vector and hybrid fail with a dimension error. | The index vector dimensions do not match the embedding deployment output. | Keep `AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536` for the default `text-embedding-3-small`, then reset and rebuild the index. |
| All modes return zero chunks. | Empty index, wrong index name, wrong Search endpoint, or documents were uploaded to a different container/prefix. | Rerun the Part 2 flow, confirm `Blobs read: 4` and `Chunks indexed: 12`, and check `AZURE_SEARCH_INDEX_NAME`. |
| Keyword results are strong for exact wording but poor for paraphrase. | Keyword search matches text, not meaning. | Compare vector and hybrid mode with the same paraphrased question. |
| Vector results are topically close but miss an exact label, date, or tote color. | Vector search is similarity-based and may underweight exact tokens. | Try hybrid mode or include the exact label, date, or named item in the query. |
| The top score looks low even when the preview is correct. | Search scores are ranking signals, not percentages. | Judge the retrieved context by source and preview content, not by score alone. |

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
