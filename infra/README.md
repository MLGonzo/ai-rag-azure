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

## Basic Flow

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -check
terraform validate
terraform plan -out tfplan
terraform apply tfplan
terraform output app_env_values
```

## Delete Resources

```bash
terraform plan -destroy -out tfdestroy
terraform apply tfdestroy
```

The outputs are intentionally non-secret. Add real Azure OpenAI and Azure AI
Search keys only to your local `.env` file when later parts need them.
