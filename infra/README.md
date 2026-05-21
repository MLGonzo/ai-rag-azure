# Infrastructure

This directory contains the Terraform for the smallest useful Azure RAG app
infrastructure used by Part 1. It creates the Azure resources described in
[../docs/00-architecture.md](../docs/00-architecture.md).

It intentionally uses plain resources instead of private endpoints, VNets, AKS,
or custom modules. The point is to make each Azure dependency visible before
later parts add ingestion and chat code.

Resources created:

- a dedicated resource group;
- a storage account and private blob container for source documents;
- an Azure AI Search service;
- an Azure OpenAI account;
- chat and embedding model deployments;
- non-secret outputs needed by `.env`.

Do not add Terraform state, local variable files, credentials, or generated
deployment output to Git.

The infrastructure is the end state for Part 1. Do not add ingestion, indexing,
retrieval, chat, or UI resources here until the later parts introduce them.
The Azure OpenAI deployments use `GlobalStandard` by default; this is not a
ProvisionedManaged/PTU setup.
Chat capacity defaults to `100`, which means 100,000 TPM for Standard-like
deployments. Embedding capacity defaults to `50`, which means 50,000 TPM.
That gives the ingestion scripts enough headroom for tutorial batches while
still using normal quota-based deployment capacity.

## Basic Flow

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -check
terraform validate
rm -f tfplan
terraform plan -out tfplan
terraform apply tfplan
terraform output app_env_values
```

`terraform validate` checks configuration and provider schemas after
`terraform init`. It does not prove your subscription has quota for the chosen
region or model deployments; `terraform plan` and `terraform apply` surface
those Azure-side issues.

If you change model names, versions, SKUs, or capacity in `terraform.tfvars`,
discard any old saved plan and run `terraform plan -out tfplan` again before
applying.

If Azure returns `InsufficientQuota`, lower the relevant
`*_capacity_thousands` value, choose another region, or request more Azure
OpenAI quota. In lower-quota subscriptions, lowering
`embedding_deployment_capacity_thousands` is the expected workaround for
indexing smaller batches.

## Teardown

```bash
terraform plan -destroy -out tfdestroy
terraform apply tfdestroy
```

If state is unavailable and the resource group is dedicated to this lesson,
inspect the group before deleting it with Azure CLI:

```bash
az resource list --resource-group "$AZURE_RESOURCE_GROUP" --output table
az group delete --name "$AZURE_RESOURCE_GROUP" --yes --no-wait
```

The outputs are intentionally non-secret. Add real Azure OpenAI and Azure AI
Search keys only to your local `.env` file when later parts need them.
