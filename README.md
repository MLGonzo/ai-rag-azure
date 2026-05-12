# The Smallest Useful RAG App on Azure

A public teaching repository for building a small, understandable retrieval-augmented generation (RAG) app on Azure. The goal is to keep every part visible enough for learners to inspect: local configuration, infrastructure, ingestion, retrieval, chat, and cleanup.

This checkpoint is **Part 1: Architecture and Infrastructure**. It defines the target architecture, establishes the repository and configuration conventions, and sets up the infrastructure area for the work that follows. It does not implement indexing, retrieval, or chat logic yet.

## Series Plan

1. **Part 1: Architecture and Infrastructure**
   - Define the target Azure RAG architecture.
   - Create the repo structure and project conventions.
   - Document prerequisites, setup flow, cost risks, and teardown expectations.
   - Establish where app code, scripts, sample data, and infrastructure files will live.
2. **Part 2: Ingest and Index**
   - Load a tiny set of local documents.
   - Chunk text, create embeddings, and write searchable records.
   - Keep the ingestion script small and inspectable.
3. **Part 3: Retrieve and Chat**
   - Query the search index.
   - Send retrieved context to an Azure OpenAI chat model.
   - Return an answer with simple source references.
4. **Part 4: Hardening and Deploy**
   - Add validation, troubleshooting, minimal tests, and deployment notes.
   - Improve teardown visibility and production-readiness boundaries.

## Intended Final Architecture

By the end of the series, the app is expected to use:

- **Local Python app** for a minimal learner-facing chat or CLI experience.
- **Azure OpenAI** for embeddings and chat completions.
- **Azure AI Search** for vector and keyword retrieval over small sample documents.
- **Azure Storage** only if a later part needs durable document storage.
- **Terraform or Azure CLI scripts** for repeatable infrastructure creation and teardown.

The final app is intentionally small. It is not meant to be a full production chatbot, a document management system, or a generalized enterprise RAG framework.

## Repository Shape

```text
.
├── app/
│   ├── main.py
│   └── requirements.txt
├── data/
│   └── sample-docs/
│       └── README.md
├── docs/
│   ├── 01-setup.md
│   └── troubleshooting.md
├── infra/
│   ├── .gitkeep
│   └── README.md
├── scripts/
│   └── README.md
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## Prerequisites

You will eventually need:

- Python 3.11 or newer.
- An Azure subscription where you can create resource groups and AI resources.
- Azure CLI installed and authenticated with `az login`.
- Terraform installed, if the infrastructure track uses Terraform in later parts.
- Access to Azure OpenAI model deployments for:
  - one chat model deployment;
  - one embedding model deployment.

Part 1 does not require Azure resources to be created.

## Cost Warning

Azure resources can cost money even when the app is idle. Search services, storage accounts, model deployments, logging, and networking choices can all affect spend.

For this teaching repo:

- Prefer the smallest SKUs that support the lesson.
- Use a dedicated resource group for the series.
- Tear down resources when you are done practicing.
- Review generated infrastructure before applying it.
- Never commit real keys, tokens, or tenant-specific secrets.

Teardown instructions will become more concrete once infrastructure files are added.

## Checkpoints

The planned checkpoint branches or tags are:

- `part-01-architecture-and-infra`
- `part-02-ingest-and-index`
- `part-03-retrieve-and-chat`
- `part-04-hardening-and-deploy`

Each checkpoint should represent the repo at the end of that video part. Learners can compare checkpoints to see what changed between parts.

## Getting Started

1. Clone the repo.
2. Copy `.env.example` to `.env`.
3. Fill in local values only when a later part asks for them.
4. Read [docs/01-setup.md](docs/01-setup.md) before creating Azure resources.
5. Keep [docs/troubleshooting.md](docs/troubleshooting.md) nearby as the series grows.

The current `app/main.py` is a tiny stub. It exists so learners can see where the application entry point will live before later parts add behavior.

## Current Status

Implemented in this checkpoint:

- public repo scaffold;
- target architecture overview;
- project conventions;
- setup and troubleshooting documentation;
- key-based local environment contract;
- app, data, scripts, and infrastructure locations for later parts.

Not implemented yet:

- document loading;
- chunking;
- embedding generation;
- Azure AI Search indexing;
- retrieval;
- chat;
- deployment automation.
