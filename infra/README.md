# Infrastructure

Part 1 infrastructure belongs in this directory. The Terraform for this lesson should create or connect the Azure resources described in [../docs/00-architecture.md](../docs/00-architecture.md).

Expected resources include:

- a dedicated resource group;
- Azure Blob Storage for source documents;
- Azure AI Search for chunks and vectors;
- Azure OpenAI or Azure AI Foundry-compatible deployments for embeddings and chat, or references to existing deployments;
- outputs needed by `.env`.

Do not add Terraform state, local variable files, credentials, or generated deployment output to Git.

Before applying changes:

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan -out tfplan
```

Before deleting resources:

```bash
terraform plan -destroy -out tfdestroy
terraform apply tfdestroy
```

If this directory only contains the scaffold files in your local checkout, continue once the Part 1 Terraform files have been added in the lesson.
