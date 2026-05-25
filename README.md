# The Smallest Useful RAG App on Azure

A beginner-friendly teaching repository for building a small retrieval-augmented generation (RAG) companion app on Azure.

The goal is to keep every part visible: local configuration, Azure infrastructure, document ingestion, search indexing, retrieval, chat, cost awareness, and cleanup. This is deliberately not an enterprise reference architecture.

This checkpoint is **Part 3: Retrieval**. It builds on the Part 2 indexing flow by querying Azure AI Search from Python and printing retrieved chunks before any LLM answering is added. Chat and any Streamlit UI come later.

## Part 3 Scope

This branch is intentionally a checkpoint, not a working chat app yet. It includes:

- architecture and setup documentation from Part 1;
- Terraform for the Azure foundation;
- original sample Markdown documents under `data/sample-docs/`;
- `scripts/upload_docs.py` for uploading sample docs to the configured Blob container;
- `scripts/create_index.py` for creating the chunk/vector Search index;
- `scripts/run_indexer.py` for Blob-to-Search chunk ingestion;
- `scripts/retrieve.py` for keyword, vector, and hybrid retrieval inspection;
- local `.env` conventions for Blob upload and indexing;
- teardown guidance from the start.

Later parts will add chat calls and any optional Streamlit UI.

## What This Repo Builds

By the end of the series, the app will answer questions over a tiny document set using:

- **Azure Blob Storage** for source documents.
- **Azure AI Search** for searchable chunks and vectors.
- **Azure OpenAI or Azure AI Foundry-compatible Azure OpenAI deployments** for embeddings and chat.
- **Python scripts** for ingestion, indexing, retrieval, and chat calls.
- **A local Python app**, with an optional Streamlit interface if a browser UI helps the lesson.
- **Terraform** for repeatable infrastructure creation and teardown.

The final app is intentionally small. Learners should be able to understand every resource, script, setting, and cleanup step.

## Start Here

- Read the architecture: [docs/00-architecture.md](docs/00-architecture.md)
- Follow setup: [docs/01-setup.md](docs/01-setup.md)
- Upload and index sample docs: [docs/02-indexing.md](docs/02-indexing.md)
- Inspect retrieval: [docs/03-retrieval.md](docs/03-retrieval.md)
- Keep troubleshooting nearby: [docs/troubleshooting.md](docs/troubleshooting.md)
- Done practicing? Jump to [Teardown](#teardown).

Part 1 creates the architecture, infrastructure, and local conventions. This
checkpoint adds source documents in Blob Storage and turns them into searchable
chunks in Azure AI Search, then queries those chunks directly. Later parts add
chat.

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
4. **Part 4: Hardening and Deploy**
   - Add chat, validation, troubleshooting, minimal tests, and deployment notes.
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
3. Create the Python virtual environment.
4. Review the Terraform files in `infra/`.
5. Export `ARM_SUBSCRIPTION_ID` from the active Azure CLI subscription, then run `terraform init`, `terraform plan`, and `terraform apply`.
6. Copy non-secret Terraform outputs into `.env`, then add real keys locally when later parts need them.
7. Run `python app/main.py` to verify the local entry point.
8. Add the storage account URL and key to `.env`, then run `python scripts/upload_docs.py --dry-run` and `python scripts/upload_docs.py`.
9. Add the Search and Azure OpenAI keys to `.env`, then run `python scripts/create_index.py`, `python scripts/run_indexer.py --dry-run`, and `python scripts/run_indexer.py`.
10. Inspect retrieved chunks with `python scripts/retrieve.py "What does the repair kit lending program include?"`.

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

The checkpoint branches are:

- `01-architecture-and-infra`
- `02-upload-and-index`
- `03-retrieval`
- `04-interrogation-and-chat`

Each checkpoint represents the repo at the end of that video part. Learners can compare checkpoints to see what changed.

When this Part 3 checkpoint is reviewed and ready, a maintainer can tag the reviewed branch:

```bash
git switch 03-retrieval
git status --short
git tag -a v0.3-part-03 -m "Part 3: retrieval"
git push origin 03-retrieval
git push origin v0.3-part-03
```
## Current Status

Implemented or documented in this checkpoint:

- Part 1 architecture docs.
- Learner setup flow.
- Terraform for a resource group, storage account, blob container, Azure AI Search, Azure OpenAI, and two model deployments.
- Non-secret Terraform outputs for later `.env` values.
- Azure CLI, Terraform, Python venv, and `.env` conventions.
- Cost warnings and teardown path.
- Placeholder app entry point.
- Original sample documents for grounded-answer testing.
- Blob Storage upload script for source documents.
- Azure AI Search index creation script.
- Blob-to-Search indexing script with deterministic chunking and embeddings.
- Part 2 upload and indexing instructions with expected command output.
- Azure AI Search retrieval script with keyword, vector, and hybrid modes.
- Part 3 retrieval-quality instructions with sample questions, expected chunks,
  mode comparison, and practical failure-mode debugging.

Not implemented yet:

- Chat.
- Streamlit UI.
