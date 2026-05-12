# Part 1 Setup

This document is the learner setup guide for **Part 1: Architecture and Infrastructure**.

Part 1 is intentionally light on commands. The goal is to establish the repo structure and make the future Azure workflow predictable before any resources are created.

## Local Setup

From the repo root:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/requirements.txt
cp .env.example .env
```

At this checkpoint, `app/requirements.txt` does not install runtime RAG dependencies yet.

## Azure Setup Checklist

Before later parts create resources, confirm that you have:

- an Azure subscription you are allowed to use for learning resources;
- permission to create a resource group;
- Azure CLI installed;
- Terraform installed, if following the Terraform path;
- access to Azure OpenAI chat and embedding deployments;
- a budget or spending alert configured for the subscription.

No Azure resources are required for Part 1.

## Configuration

`.env.example` lists the local settings the app and scripts are expected to use as the series grows. Copy it to `.env` and fill values only when needed.

This learning project uses key-based auth for local app calls. Put real Azure OpenAI and Azure AI Search keys only in your local `.env` file.

Never commit `.env`, Azure keys, Azure tokens, Terraform state, or downloaded credential files.

## Expected Future Flow

Later parts are expected to follow this rough order:

1. create or select Azure resources;
2. put endpoint and deployment names in `.env`;
3. add sample documents under `data/sample-docs/`;
4. run an ingestion script;
5. run the app;
6. tear down resources when finished.

## Teardown Reminder

Use a dedicated resource group for this project. That makes cleanup easier because the whole learning environment can be removed together.

Concrete teardown commands will be added when infrastructure files are introduced.
