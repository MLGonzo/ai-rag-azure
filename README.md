# The Smallest Useful RAG App on Azure

A beginner-friendly teaching repository for building a small retrieval-augmented generation (RAG) companion app on Azure.

The goal is to keep every part visible: local configuration, Azure infrastructure, document ingestion, search indexing, retrieval, chat, cost awareness, and cleanup. This is deliberately not an enterprise reference architecture.

This checkpoint is **Part 1: Architecture and Infrastructure**. In this part, the series defines and creates the Azure foundation with readable Terraform. Indexing, retrieval, chat, and any Streamlit UI come later.

## Part 1 Scope

This branch is intentionally a checkpoint, not a working RAG app yet. It includes:

- architecture and setup documentation;
- a small repo scaffold with placeholder `app/`, `scripts/`, and `data/sample-docs/` locations;
- Terraform for the Azure foundation;
- local `.env` conventions and non-secret Terraform outputs;
- teardown guidance from the start.

Later parts will add the actual sample documents, ingestion code, indexing code, retrieval flow, chat calls, and any optional Streamlit UI.

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
- Keep troubleshooting nearby: [docs/troubleshooting.md](docs/troubleshooting.md)
- Done practicing? Jump to [Teardown](#teardown).

Part 1 creates the architecture, infrastructure, and local conventions. Later parts turn that foundation into a working RAG flow.

## Series Plan

1. **Part 1: Architecture and Infrastructure**
   - Define the target Azure RAG architecture.
   - Create the Azure foundation with Terraform.
   - Establish the `.env` contract and local project layout.
   - Document prerequisites, setup flow, cost risks, and teardown.
2. **Part 2: Ingest and Index**
   - Load a tiny set of documents.
   - Chunk text, create embeddings, and write searchable records to Azure AI Search.
   - Keep the ingestion script small and inspectable.
3. **Part 3: Retrieve and Chat**
   - Query Azure AI Search.
   - Send retrieved context to the chat deployment.
   - Return an answer with simple source references.
4. **Part 4: Hardening and Deploy**
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
|       `-- README.md
|-- docs/
|   |-- 00-architecture.md
|   |-- 01-setup.md
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
|   `-- README.md
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
- `part-02-ingest-and-index`
- `part-03-retrieve-and-chat`
- `part-04-hardening-and-deploy`

Each checkpoint represents the repo at the end of that video part. Learners can compare checkpoints to see what changed.

When the Part 1 checkpoint is reviewed and ready, a maintainer can create the matching tag:

```bash
git switch part-01-architecture-and-infra
git status --short
git tag -a v0.1-part-01 -m "Part 1: architecture and infrastructure"
git push origin part-01-architecture-and-infra
git push origin v0.1-part-01
```

If the branch does not exist yet, create it from the reviewed Part 1 commit with:

```bash
git switch -c part-01-architecture-and-infra
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

Not implemented yet:

- Document loading.
- Chunking.
- Embedding generation.
- Azure AI Search indexing.
- Retrieval.
- Chat.
- Streamlit UI.
