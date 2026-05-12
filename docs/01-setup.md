# Part 1 Setup

This guide is for **Part 1: Architecture and Infrastructure**. Part 1 creates the Azure foundation for the smallest useful RAG teaching app. Later parts add ingestion, retrieval, chat, and the optional Streamlit UI.

The commands below are intentionally plain so learners can follow them on video and understand which step creates cost.

## Prerequisites

Install or confirm:

- Python 3.11 or newer.
- Git.
- Azure CLI.
- Terraform.
- An Azure subscription where you can create a resource group, storage account, Azure AI Search service, and Azure OpenAI or Azure AI Foundry-compatible deployments.
- Access to one chat deployment and one embedding deployment, or permission to create them if the Terraform in `infra/` does so.
- A budget or spending alert for the subscription.

This is a teaching app. Use a personal dev subscription or sandbox where deleting the full resource group is acceptable.

## 1. Clone And Select The Checkpoint

```bash
git clone <repo-url>
cd ai-rag-azure
git checkout part-01-architecture-and-infra
```

If you already have the repo, pull the latest branch or checkpoint before running infrastructure commands.

## 2. Login To Azure CLI

```bash
az login
az account list --output table
az account set --subscription "<subscription-id-or-name>"
az account show --output table
```

If your account belongs to more than one tenant, use the tenant that owns the subscription:

```bash
az login --tenant "<tenant-id>"
```

Keep the subscription ID and tenant ID handy because they also belong in `.env`.

## 3. Review Local Configuration

Create a local `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

```bash
AZURE_SUBSCRIPTION_ID="..."
AZURE_TENANT_ID="..."
AZURE_RESOURCE_GROUP="rg-smallest-useful-rag-dev"
AZURE_LOCATION="uksouth"
```

After Terraform creates or connects the Azure resources, fill in:

```bash
AZURE_OPENAI_ENDPOINT="..."
AZURE_OPENAI_CHAT_DEPLOYMENT="..."
AZURE_OPENAI_EMBEDDING_DEPLOYMENT="..."
AZURE_OPENAI_API_KEY="..."
AZURE_SEARCH_ENDPOINT="..."
AZURE_SEARCH_INDEX_NAME="smallest-useful-rag"
AZURE_SEARCH_API_KEY="..."
AZURE_STORAGE_ACCOUNT_NAME="..."
AZURE_STORAGE_CONTAINER_NAME="rag-documents"
```

Do not commit `.env`, Terraform state, Azure credentials, or downloaded key files.

## 4. Create The Python Environment

From the repo root:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/requirements.txt
```

At this checkpoint, the app is still a placeholder. Runtime RAG dependencies are added in later parts when they are first used.

## 5. Provision Azure With Terraform

Part 1's infrastructure belongs under `infra/`. Review every file before applying it.

```bash
cd infra
terraform init
terraform fmt -check
terraform validate
terraform plan -out tfplan
terraform apply tfplan
terraform output
cd ..
```

The plan should be small and understandable. For this teaching app, expect resources such as a resource group, Blob Storage, Azure AI Search, and Azure OpenAI or Azure AI Foundry-compatible deployment configuration.

If your local checkout is still at a scaffold-only moment and `infra/` does not yet contain `.tf` files, do not force these commands. Continue once the Part 1 Terraform files have been added in the lesson.

## 6. Local Verification

Load the local environment values into your shell:

```bash
set -a
source .env
set +a
```

Confirm the Azure resource group exists:

```bash
az group show --name "$AZURE_RESOURCE_GROUP" --output table
az resource list --resource-group "$AZURE_RESOURCE_GROUP" --output table
```

Confirm the placeholder app runs:

```bash
python app/main.py
```

Expected output for Part 1:

```text
Part 1 placeholder: the RAG app is not implemented yet. See README.md for the series plan.
```

This verifies the local Python entry point. In later parts, verification will include indexing documents, querying Azure AI Search, and calling the chat deployment.

## Teardown

When you are done practicing, destroy the Terraform-managed resources:

```bash
cd infra
terraform plan -destroy -out tfdestroy
terraform apply tfdestroy
cd ..
```

If the Terraform state is missing or broken, inspect the resource group manually before deleting it:

```bash
az resource list --resource-group "$AZURE_RESOURCE_GROUP" --output table
az group delete --name "$AZURE_RESOURCE_GROUP" --yes --no-wait
```

Only use the resource group delete path if the group is dedicated to this lesson. It deletes everything inside the group.

## Cost Reminder

Azure AI Search and other provisioned resources can keep billing while idle. Azure OpenAI calls can consume quota and generate token charges. Blob Storage is usually small for this lesson, but retained data and transactions are still billable.

Use small SKUs, avoid leaving resources running between recording or practice sessions, and check Azure Cost Management after teardown.
