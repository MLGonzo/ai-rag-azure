# The Smallest Useful RAG App on Azure

A beginner-friendly teaching repository for building a small retrieval-augmented
generation (RAG) companion app on Azure.

This repo is designed to be followed as a four-part video series. Each part has
its own branch, and each branch shows the repository at the end of that lesson.
Use `main` as the overview and final finished state; use the numbered branches
when you want to follow the lessons step by step.

The goal is to keep every part visible: local configuration, Azure
infrastructure, document ingestion, search indexing, retrieval, chat, cost
awareness, and cleanup. This is deliberately not an enterprise reference
architecture.

## How To Use This Repo

Start from `main` to understand the structure, then move through the checkpoint
branches in order:

```bash
git clone <repo-url>
cd ai-rag-azure
git switch 01-architecture-and-infra
```

At the end of a lesson, switch to the next branch:

```bash
git switch 02-upload-and-index
git switch 03-retrieval
git switch 04-interrogation-and-chat
```

Each checkpoint represents the repo at the end of that video part. The branch
README explains the scope of that checkpoint, and the docs available on that
branch contain the commands for that stage of the build.

## Branch Guide

| Part | Branch | What You Build | Main Docs To Read |
| --- | --- | --- | --- |
| 1 | `01-architecture-and-infra` | Azure foundation, Terraform, `.env` conventions, cost and teardown path | `docs/00-architecture.md`, `docs/01-setup.md`, `docs/troubleshooting.md` |
| 2 | `02-upload-and-index` | Sample documents, Blob upload, Search index creation, chunking, embeddings, indexing | `docs/01-setup.md`, `docs/02-indexing.md`, `docs/troubleshooting.md` |
| 3 | `03-retrieval` | Keyword, vector, and hybrid retrieval inspection before any LLM answering | `docs/02-indexing.md`, `docs/03-retrieval.md`, `docs/troubleshooting.md` |
| 4 | `04-interrogation-and-chat` | Grounded answers, source citations, and a small Streamlit chat UI | `docs/03-retrieval.md`, `docs/04-chat-app.md`, `docs/troubleshooting.md` |

`main` contains the finished Part 4 code plus this series-level guide. The
`04-interrogation-and-chat` branch is the Part 4 checkpoint with branch-specific
README wording.

## Documentation Guide

- `docs/00-architecture.md`: the target architecture and why the repo is shaped
  this way.
- `docs/01-setup.md`: prerequisites, local setup, Terraform provisioning,
  verification, cost notes, and teardown.
- `docs/02-indexing.md`: uploading sample documents, creating the Search index,
  chunking, embeddings, and indexing.
- `docs/03-retrieval.md`: inspecting retrieval quality with keyword, vector, and
  hybrid modes.
- `docs/04-chat-app.md`: asking grounded questions and running the local
  Streamlit chat app.
- `docs/troubleshooting.md`: common Azure CLI, Terraform, Blob Storage, Search,
  embedding, retrieval, and chat problems.

When following the videos, read the docs that exist on the branch you are on.
Later branches include more docs because later lessons add more behavior.

## What This Repo Builds

By the end of the series, the app answers questions over a tiny document set
using:

- **Azure Blob Storage** for source documents.
- **Azure AI Search** for searchable chunks and vectors.
- **Azure OpenAI or Azure AI Foundry-compatible Azure OpenAI deployments** for
  embeddings and chat.
- **Python scripts** for ingestion, indexing, retrieval, and chat calls.
- **A small local Streamlit app** for a multi-turn chat that exposes retrieved
  chunks.
- **Terraform** for repeatable infrastructure creation and teardown.

The final app is intentionally small. Learners should be able to understand
every resource, script, setting, and cleanup step.

## Prerequisites

You need:

- Python 3.11 or newer.
- Git.
- Azure CLI authenticated with `az login`.
- Terraform.
- An Azure subscription where you can create learning resources.
- Permission to create or use Azure OpenAI or Azure AI Foundry-compatible chat
  and embedding deployments.
- A budget or spending alert for the subscription.

## Full Flow At A Glance

The branch docs provide the exact commands for each lesson. The finished flow is:

1. Login with Azure CLI and select the right subscription.
2. Copy `.env.example` to `.env`.
3. Create the Python virtual environment and install `app/requirements.txt`.
4. Review the Terraform files in `infra/`.
5. Export `ARM_SUBSCRIPTION_ID` from the active Azure CLI subscription, then run
   `terraform init`, `terraform plan`, and `terraform apply`.
6. Copy non-secret Terraform outputs into `.env`, then add real keys locally.
7. Upload sample documents with `scripts/upload_docs.py`.
8. Create the Search index with `scripts/create_index.py`.
9. Build chunks and embeddings with `scripts/run_indexer.py`.
10. Inspect retrieved chunks with `scripts/retrieve.py`.
11. Ask grounded questions with `scripts/ask.py`.
12. Open the browser app with `python -m streamlit run app/main.py`.

For the normal local learning path, `az login` provides authentication and
`az account set` chooses the subscription. You usually do not need to manually
set a tenant ID. The subscription and tenant values in `.env` are reference
values for local scripts, not a replacement for Azure CLI login.

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

Earlier branches have fewer files because they intentionally stop before later
lesson code is introduced.

## Cost Warning

Azure resources can cost money even when the app is idle. For this repo, watch
Azure AI Search, Azure OpenAI token usage, Blob Storage, logging, and any extra
resources created while experimenting.

Use the smallest SKUs that support the lesson, keep everything in a dedicated
resource group, review every Terraform plan, and tear down resources when you
are done.

## Teardown

Prefer Terraform teardown:

```bash
cd infra
terraform plan -destroy -out tfdestroy
terraform apply tfdestroy
```

If Terraform state is unavailable and the resource group is dedicated to this
lesson, inspect it and delete the group:

```bash
az resource list --resource-group "$AZURE_RESOURCE_GROUP" --output table
az group delete --name "$AZURE_RESOURCE_GROUP" --yes --no-wait
```

Never delete a shared resource group as a shortcut.

## Status

`main` and `04-interrogation-and-chat` contain the finished learning app for the
four-part series. Production hardening and deployment workflow are intentionally
outside the scope of this sample.
