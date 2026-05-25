# Part 1 Setup

This guide is for **Part 1: Architecture and Infrastructure**. Part 1 creates the Azure foundation for the smallest useful RAG teaching app. Later parts add ingestion, retrieval, chat, and the optional Streamlit UI.

The commands below are intentionally plain so learners can follow them on video and understand which step creates cost.
The Terraform is kept small on purpose: no private networking, no AKS, no custom
modules, and no secret outputs.

Teardown is part of the setup story for this checkpoint. If you only need the
cleanup commands, jump to [Teardown](#teardown).

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
git switch 01-architecture-and-infra
```

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

For the normal local learning path, this is enough:

- `az login` authenticates your shell.
- `az account set` selects the subscription Terraform and Azure CLI commands should use.
- `az login --tenant` is only needed when Azure CLI signs in to the wrong tenant.

You do not need to manually set a tenant ID just because you are using `.env`.

## 3. Review Local Configuration

Create a local `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and set the resource placement values:

```bash
AZURE_RESOURCE_GROUP="rg-smallest-useful-rag-dev"
AZURE_LOCATION="uksouth"
```

`AZURE_SUBSCRIPTION_ID` and `AZURE_TENANT_ID` are included as reference values
for local scripts and later parts. They do not log you in, and Terraform does
not read them from `.env` in this checkpoint. If you want them to match your
current Azure CLI context, copy them from:

```bash
az account show --query '{subscriptionId:id, tenantId:tenantId}' --output table
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
AZURE_STORAGE_ACCOUNT_URL="..."
AZURE_STORAGE_ACCOUNT_KEY="..."
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
cp terraform.tfvars.example terraform.tfvars
```

Open `terraform.tfvars` and adjust at least:

- `location`, using an Azure region where your OpenAI models are available;
- `project_name`, using a short lowercase prefix;
- model names, versions, and deployment SKU if your subscription needs different choices.

The default chat model is `gpt-4.1-mini` with model version `2025-04-14`. The
default model deployment SKU is `GlobalStandard`. This is not a
`ProvisionedManaged` or PTU deployment.

If you copied `terraform.tfvars` before these defaults were updated, make sure
your local file also uses:

```bash
chat_deployment_name = "gpt-4.1-mini"
chat_model_name = "gpt-4.1-mini"
chat_model_version = "2025-04-14"
model_deployment_sku_name = "GlobalStandard"
chat_deployment_capacity_thousands = 100
embedding_deployment_capacity_thousands = 30
```

For Standard-like Azure OpenAI deployments, capacity is assigned in thousands
of tokens per minute. `chat_deployment_capacity_thousands = 100` requests a
100,000 TPM chat deployment, and
`embedding_deployment_capacity_thousands = 30` requests a 30,000 TPM embedding
deployment. This allocates available quota; it does not create a
ProvisionedManaged/PTU deployment and does not create idle PTU billing.

Terraform uses Azure CLI authentication, but AzureRM 4.x still needs an explicit
subscription ID for plan and apply. The recommended path is to derive it from
the Azure CLI subscription you selected above:

```bash
export ARM_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
```

You can alternatively uncomment `subscription_id` in `terraform.tfvars`. You
normally do not need to set a tenant ID for Terraform when using Azure CLI auth.

Initialize and check the configuration:

```bash
terraform init
terraform fmt -check
terraform validate
```

Review and apply the planned resources:

```bash
rm -f tfplan
terraform plan -out tfplan
terraform apply tfplan
```

The saved `tfplan` file captures the exact model names, versions, SKUs, and
resource changes from the moment `terraform plan` ran. If you change
`terraform.tfvars`, create a fresh plan before applying.

If apply fails with `InsufficientQuota`, lower the relevant capacity value, use
another region with available quota, or request more quota in Azure AI Foundry.
For smaller tutorial batches, it is safe to lower
`embedding_deployment_capacity_thousands` if your subscription cannot allocate
the default embedding quota.

Show the non-secret outputs needed by later `.env` values:

```bash
terraform output
terraform output app_env_values
cd ..
```

Terraform does not output Azure OpenAI or Azure AI Search keys. Get those from
the Azure portal or Azure CLI only when later parts need local key-based calls,
then put them in your local `.env` file.

The plan should be small and understandable. For this teaching app, expect a
resource group, Blob Storage, Azure AI Search, an Azure OpenAI account, and chat
and embedding model deployments.

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
Part 1 placeholder: infrastructure is defined, but the RAG app is not implemented yet. See README.md for the series plan.
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
