# Part 4: RAG Chat App

Part 4 combines the retrieval flow from Part 3 with Azure OpenAI chat calls.
This checkpoint has one command-line experience and one small browser UI:

- `scripts/ask.py` answers one question and exits.
- `app/main.py` runs a Streamlit app for demonstrating the final RAG flow.

The Streamlit app is intentionally plain. It lets a learner start a short
conversation with session memory, inspect the retrieved chunks, and read
grounded answers in a lightweight community-workshop page.

For each question, the scripts and app:

1. retrieve fresh chunks from Azure AI Search;
2. build a constrained prompt;
3. call the configured chat deployment;
4. print or display the answer and retrieved sources.

The Streamlit app keeps a small in-memory list of recent turns. It uses recent
user questions to make follow-up retrieval less brittle, and passes recent
conversation history into the answer prompt. The prompt tells the model that
conversation history is only for understanding the current question. Factual
claims must still come from retrieved document chunks.

## Prerequisites

Complete Part 3 first so the Search index already contains chunks:

```bash
python scripts/upload_docs.py
python scripts/create_index.py
python scripts/run_indexer.py
python scripts/retrieve.py "What does the repair kit lending program include?"
```

Install dependencies from the repo root if your virtual environment is not
already ready:

```bash
python -m pip install -r app/requirements.txt
```

## Configuration

`ask.py` and the Streamlit app use the same Search, embedding, and chat
settings:

```bash
AZURE_SEARCH_ENDPOINT="https://your-search-service.search.windows.net"
AZURE_SEARCH_INDEX_NAME="smallest-useful-rag"
AZURE_SEARCH_API_KEY="replace-with-your-search-admin-or-query-key"
AZURE_OPENAI_ENDPOINT="https://your-azure-openai-resource.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2024-10-21"
AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4.1-mini"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-small"
AZURE_OPENAI_API_KEY="replace-with-your-azure-openai-key"
RETRIEVAL_MODE="hybrid"
RETRIEVAL_TOP_K="5"
RETRIEVAL_PREVIEW_CHARS="500"
```

Keyword mode does not need embeddings for retrieval, but answering still needs
the Azure OpenAI endpoint, API version, API key, and chat deployment because the
script must call the chat model after retrieval.

The Streamlit app exposes the chat memory window as "Memory turns" in the
sidebar. The default is 3 recent turns. You can set `CHAT_HISTORY_TURNS` in
your local `.env` if you want a different default, but it is optional.

## Ask One Question

Use `ask.py` when you want a single grounded answer:

```bash
python scripts/ask.py "How long can a member borrow a starter repair kit?"
```

Or run without a question and enter one at the prompt:

```bash
python scripts/ask.py
```

The default retrieval mode is hybrid. You can still compare retrieval modes:

```bash
python scripts/ask.py --mode keyword "What days is Harbor Hill open?"
python scripts/ask.py --mode vector "What extra check is required for hot electronics work?"
python scripts/ask.py --mode hybrid "Which planter needs a valve inspection?"
```

Show the retrieved chunks before the answer when you want to inspect grounding:

```bash
python scripts/ask.py --show-context --top-k 3 "Which tote is reserved for first-time borrowers?"
```

## Run The Streamlit App

Use the Streamlit app when you want to demonstrate the complete flow in a
browser:

```bash
python -m streamlit run app/main.py
```

Run the command from the repo root after installing `app/requirements.txt` and
filling in `.env`. Streamlit usually opens `http://localhost:8501`
automatically.

The app reads the same `.env` values as `ask.py`. The page introduces the
fictional Harbor Hill Community Workshop documents: the workshop overview,
repair kit lending notes, rainwater planter field notes, and safety orientation
guide.

The sidebar exposes the retrieval mode, `top_k`, Search index, chat deployment,
and memory window. After you ask a question, the page shows:

- the grounded answer;
- the conversation so far;
- the retrieval query sent to Azure AI Search;
- the latest retrieved chunks in expanded panels.

Use "Clear conversation" in the sidebar to reset Streamlit session memory.

If configuration is missing, the page shows a configuration error instead of a
Python traceback. If Azure AI Search returns no chunks, the app shows the
standard `I don't know based on the provided documents.` answer and an empty
retrieved-chunks section.

You can still use the CLI without Streamlit:

```bash
python scripts/ask.py "How long can a member borrow a starter repair kit?"
```

## Expected Not-Answerable Output

Ask something that is not in the sample documents:

```bash
python scripts/ask.py "What is the workshop Wi-Fi password?"
```

Or inside the Streamlit app:

```text
You: What is the workshop Wi-Fi password?
```

The answer should refuse instead of guessing:

```text
Answer:
I don't know based on the provided documents.

Sources:
[1] harbor-hill-overview.md (harbor-hill-overview.md), chunk 1
[2] safety-and-orientation.md (safety-and-orientation.md), chunk 1
```

The exact retrieved sources may vary. The important behavior is that the answer
does not invent a Wi-Fi password.

If Search returns no chunks, the Streamlit app returns the same I-do-not-know
answer and shows an empty retrieved-chunks section.

## How The Local Entry Points Differ

`ask.py` is single-turn. It retrieves context for one question, calls the chat
model once, prints the answer and sources, then exits. It is best for testing a
known question or debugging one retrieval result.

`app/main.py` is a multi-turn Streamlit UI around the same retrieval and answer
helpers used by `ask.py`. It is useful for demos because the conversation and
latest retrieved chunks stay visible in the browser.

None of these entry points is a production chat service. There is no
authentication layer, no shared state, and no persistence.

## Prompt Behavior

The prompt tells the model to:

- use only retrieved context chunks for factual claims;
- use recent conversation only to understand the current question;
- say `I don't know based on the provided documents.` when the context is
  insufficient;
- cite supporting chunks with bracketed source numbers like `[1]`;
- keep the answer concise and factual.

If the needed fact is absent from the retrieved chunks, fix retrieval first.
Use `--show-context`, increase `--top-k`, compare retrieval modes, and return to
[Part 3](03-retrieval.md) for retrieval debugging steps.

## Common Failure Modes

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| The answer says it does not know, but the fact exists in a source file. | The right chunk was not retrieved. | Run with `--show-context --top-k 5` and compare keyword, vector, and hybrid modes. |
| A follow-up question gives a weak answer. | The current question may be too vague, or the recent memory window is too small. | Rephrase the follow-up with the missing noun, or increase "Memory turns" in the Streamlit sidebar. |
| The answer is plausible but not cited. | The model did not follow the citation instruction perfectly. | Read the printed `Sources` section and rerun with `--show-context`; reduce ambiguity in the question. |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` is missing. | `.env` was copied before chat was added or the deployment name was not filled in. | Add the chat deployment name from your Azure OpenAI resource to `.env`. |
| Keyword mode retrieves chunks but the chat call fails. | Keyword retrieval does not use embeddings, but answering still needs Azure OpenAI chat settings. | Check `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_CHAT_DEPLOYMENT`. |
| The script returns no retrieved sources. | Empty index, wrong Search index, or overly narrow query. | Rerun the Part 2 indexing flow and inspect retrieval with `scripts/retrieve.py`. |
| `python app/main.py` only prints a command. | The Streamlit app must be launched by Streamlit. | Run `python -m streamlit run app/main.py` from the repo root. |
