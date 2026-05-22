# The Smallest Useful RAG App on Azure

A beginner-friendly teaching repository for building a small retrieval-augmented generation (RAG) companion app on Azure.

The goal is to keep every part visible: local configuration, Azure infrastructure, document ingestion, search indexing, retrieval, chat, cost awareness, and cleanup. This is deliberately not an enterprise reference architecture.

This checkpoint is **Part 4: RAG Chat App**. It builds on the Part 3 retrieval flow by retrieving chunks from Azure AI Search, sending them to the configured Azure OpenAI chat deployment, and showing grounded answers with source references. It includes a single-turn question script and a simple community-workshop Streamlit app for demonstrating a multi-turn chat in a browser.

## Part 4 Scope

This branch is intentionally a small local RAG app checkpoint. It includes:

- architecture and setup documentation from Part 1;
- Terraform for the Azure foundation;
- original sample Markdown documents under `data/sample-docs/`;
- `scripts/upload_docs.py` for uploading sample docs to the configured Blob container;
- `scripts/create_index.py` for creating the chunk/vector Search index;
- `scripts/run_indexer.py` for Blob-to-Search chunk ingestion;
- `scripts/retrieve.py` for keyword, vector, and hybrid retrieval inspection;
- `scripts/ask.py` for retrieval plus grounded chat answers;
- `app/main.py` for a multi-turn Streamlit UI that shows retrieved chunks and answers;
- local `.env` conventions for Blob upload, indexing, retrieval, and chat;
- teardown guidance from the start.

Later parts can add hardening, validation, and deployment notes.

## What This Repo Builds

By the end of the series, the app will answer questions over a tiny document set using:

- **Azure Blob Storage** for source documents.
- **Azure AI Search** for searchable chunks and vectors.
- **Azure OpenAI or Azure AI Foundry-compatible Azure OpenAI deployments** for embeddings and chat.
- **Python scripts** for ingestion, indexing, retrieval, and chat calls.
- **A small local Streamlit app** for a multi-turn chat that exposes retrieved chunks.
- **Terraform** for repeatable infrastructure creation and teardown.

The final app is intentionally small. Learners should be able to understand every resource, script, setting, and cleanup step.

## Start Here

- Read the architecture: [docs/00-architecture.md](docs/00-architecture.md)
- Follow setup: [docs/01-setup.md](docs/01-setup.md)
- Upload and index sample docs: [docs/02-indexing.md](docs/02-indexing.md)
- Inspect retrieval: [docs/03-retrieval.md](docs/03-retrieval.md)
- Ask grounded questions and try the local chat app: [docs/04-chat-app.md](docs/04-chat-app.md)
- Keep troubleshooting nearby: [docs/troubleshooting.md](docs/troubleshooting.md)
- Done practicing? Jump to [Teardown](#teardown).

Part 1 creates the architecture, infrastructure, and local conventions. This
checkpoint adds source documents in Blob Storage and turns them into searchable
chunks in Azure AI Search, queries those chunks directly, and uses the retrieved
context to answer questions with the configured chat model. It also adds a
community-workshop browser UI for a short memory-backed chat over the final RAG
flow.

## Series Plan

1. **Part 1: Architecture and Infrastructure**
   - Define the target Azure RAG architecture.
   - Create the Azure foundation with Terraform.
   - Establish the `.env` contract and local project layout.
   - Document prerequisites, setup flow, cost risks, and teardown.
2. **Part 2: Blob Source Documents and Indexing**
   - Add a tiny, safe set of original documents.
   - Upload source documents to Azure Blob Storage.
   - Then chunk text, create embeddings, and write searchable records to Azure AI Search.
3. **Part 3: Retrieval**
   - Query Azure AI Search.
   - Compare keyword, vector, and hybrid retrieval.
   - Use known sample questions to check expected sources and chunks.
   - Print and inspect retrieved chunks before any LLM answering.
4. **Part 4: RAG Chat App**
   - Combine retrieval with a chat model call.
   - Instruct the model to answer only from retrieved context.
   - Print source references and handle questions the documents do not answer.
   - Add a simple Streamlit app with session memory and visible retrieved chunks.
5. **Later: Hardening and Deploy**
   - Add validation, troubleshooting, minimal tests, and deployment notes.
   - Clarify what this sample does not try to solve for production.

## Repository Shape

```text
.
|-- app/
|   |-- main.py
|   `-- requirements.txt
|-- data/
|   `-- sample-docs/
|       |-- README.md
|       |-- harbor-hill-overview.md
|       |-- rainwater-planter-pilot.md
|       |-- repair-kit-lending.md
|       `-- safety-and-orientation.md
|-- docs/
|   |-- 00-architecture.md
|   |-- 01-setup.md
|   |-- 02-indexing.md
|   |-- 03-retrieval.md
|   |-- 04-chat-app.md
|   `-- troubleshooting.md
|-- infra/
|   |-- .terraform.lock.hcl
|   |-- main.tf
|   |-- outputs.tf
|   |-- providers.tf
|   |-- terraform.tfvars.example
|   |-- variables.tf
|   `-- README.md
|-- scripts/
|   |-- README.md
|   |-- ask.py
|   |-- create_index.py
|   |-- retrieve.py
|   |-- run_indexer.py
|   `-- upload_docs.py
|-- .env.example
|-- .gitignore
|-- LICENSE
`-- README.md
```

## Prerequisites

You need:

- Python 3.11 or newer.
- Git.
- Azure CLI authenticated with `az login`.
- Terraform.
- An Azure subscription where you can create learning resources.
- Permission to create or use Azure OpenAI or Azure AI Foundry-compatible chat and embedding deployments.
- A budget or spending alert for the subscription.

## Setup Flow

The full Part 1 setup is in [docs/01-setup.md](docs/01-setup.md). The short version is:

1. Login with Azure CLI and select the right subscription.
2. Copy `.env.example` to `.env`.
3. Create the Python virtual environment and install `app/requirements.txt`.
4. Review the Terraform files in `infra/`.
5. Export `ARM_SUBSCRIPTION_ID` from the active Azure CLI subscription, then run `terraform init`, `terraform plan`, and `terraform apply`.
6. Copy non-secret Terraform outputs into `.env`, then add real keys locally when later parts need them.
7. Add the storage account URL and key to `.env`, then run `python scripts/upload_docs.py --dry-run` and `python scripts/upload_docs.py`.
8. Add the Search and Azure OpenAI keys to `.env`, then run `python scripts/create_index.py`, `python scripts/run_indexer.py --dry-run`, and `python scripts/run_indexer.py`.
9. Inspect retrieved chunks with `python scripts/retrieve.py "What does the repair kit lending program include?"`.
10. Ask a grounded question with `python scripts/ask.py "How long can a member borrow a starter repair kit?"`.
11. Open the browser app with `python -m streamlit run app/main.py`.

For the normal local learning path, `az login` provides authentication and
`az account set` chooses the subscription. You usually do not need to manually
set a tenant ID. The subscription and tenant values in `.env` are reference
values for local scripts and later parts, not a replacement for Azure CLI login.

## Cost Warning

Azure resources can cost money even when the app is idle. For this repo, watch Azure AI Search, Azure OpenAI token usage, Blob Storage, logging, and any extra resources created while experimenting.

Use the smallest SKUs that support the lesson, keep everything in a dedicated resource group, review every Terraform plan, and tear down resources when you are done.

## Teardown

Prefer Terraform teardown:

```bash
cd infra
terraform plan -destroy -out tfdestroy
terraform apply tfdestroy
```

If Terraform state is unavailable and the resource group is dedicated to this lesson, inspect it and delete the group:

```bash
az resource list --resource-group "$AZURE_RESOURCE_GROUP" --output table
az group delete --name "$AZURE_RESOURCE_GROUP" --yes --no-wait
```

Never delete a shared resource group as a shortcut.

## Checkpoints

The planned checkpoint branches are:

- `part-01-architecture-and-infra`
- `part-02-blob-to-search-index`
- `part-03-retrieval`
- `part-04-rag-chat-app`

Each checkpoint represents the repo at the end of that video part. Learners can compare checkpoints to see what changed.

When this Part 4 checkpoint is reviewed and ready, a maintainer can create the
matching branch and tag:

```bash
git switch -c part-04-rag-chat-app
git status --short
git tag -a v0.4-part-04 -m "Part 4: RAG chat app"
git push origin part-04-rag-chat-app
git push origin v0.4-part-04
```

If `part-04-rag-chat-app` already exists locally, use:

```bash
git switch part-04-rag-chat-app
```

## Current Status

Implemented or documented in this checkpoint:

- Part 1 architecture docs.
- Learner setup flow.
- Terraform for a resource group, storage account, blob container, Azure AI Search, Azure OpenAI, and two model deployments.
- Non-secret Terraform outputs for later `.env` values.
- Azure CLI, Terraform, Python venv, and `.env` conventions.
- Cost warnings and teardown path.
- Simple Streamlit app that supports short conversations, describes the Harbor
  Hill sample docs, shows retrieved chunks, and displays grounded answers.
- Original sample documents for grounded-answer testing.
- Blob Storage upload script for source documents.
- Azure AI Search index creation script.
- Blob-to-Search indexing script with deterministic chunking and embeddings.
- Part 2 upload and indexing instructions with expected command output.
- Azure AI Search retrieval script with keyword, vector, and hybrid modes.
- Part 3 retrieval-quality instructions with sample questions, expected chunks,
  mode comparison, and practical failure-mode debugging.
- RAG question-answering script that retrieves context, calls the configured
  chat deployment, and prints source references.
- Part 4 chat app instructions with single-turn CLI, multi-turn Streamlit, and
  not-answerable examples.

Not implemented yet:

- Production hardening and deployment workflow.
