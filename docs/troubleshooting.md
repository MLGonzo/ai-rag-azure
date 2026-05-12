# Troubleshooting

This page covers the common problems learners are likely to hit while setting up the Part 1 Azure architecture. Later parts will add script-specific indexing, retrieval, and chat errors.

## First Checks

Start here before changing code or infrastructure:

- Confirm you are on `part-01-architecture-and-infra`.
- Confirm Azure CLI is logged in to the expected tenant and subscription.
- Confirm `.env` exists locally and was copied from `.env.example`.
- Confirm the Python virtual environment is active before running app commands.
- Confirm `infra/` contains the Terraform files for the point in the lesson you are following.
- Confirm real secrets are only in `.env`, never in Git.

## Azure CLI Authentication

If Azure CLI commands fail, check the active account:

```bash
az account show --output table
az account list --output table
```

Set the expected subscription:

```bash
az account set --subscription "<subscription-id-or-name>"
```

If the wrong tenant is active, login with the tenant explicitly:

```bash
az login --tenant "<tenant-id>"
```

Common symptoms:

- `Please run 'az login'`: login expired or never completed.
- `The subscription ... could not be found`: wrong tenant or wrong account.
- `AuthorizationFailed`: the account can see the subscription but lacks permission to create or update the resource.

## Provider Registration

Terraform can fail if the subscription has not registered the required Azure resource providers. Register the providers for this lesson:

```bash
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.Search
az provider register --namespace Microsoft.CognitiveServices
```

Then rerun:

```bash
cd infra
terraform plan -out tfplan
```

## Terraform Has No Configuration Files

If `terraform init`, `terraform validate`, or `terraform plan` says there are no configuration files, you are probably at the scaffold-only point before the Part 1 Terraform files were added.

Check:

```bash
find infra -maxdepth 2 -type f -print
```

Continue after the lesson has added the `.tf` files under `infra/`.

## Terraform State Problems

Terraform state records what it created. Do not delete or commit state files.

Common symptoms:

- Terraform wants to recreate resources you know already exist.
- Terraform reports a resource exists but is not in state.
- Manual portal changes cause unexpected drift in `terraform plan`.

Fixes:

- Prefer changing resources through Terraform during the lesson.
- Run `terraform plan` and read the proposed changes before applying.
- If the local state is unusable and this resource group is only for the lesson, delete the whole resource group and recreate it.
- Do not run `terraform apply` just to "see what happens"; use `terraform plan` first.

## Quota And Region Issues

Azure OpenAI and Azure AI Foundry-compatible deployments depend on regional availability and subscription quota. Not every model or SKU is available in every region.

Common symptoms:

- Deployment creation fails because quota is unavailable.
- A model is visible in one region but not another.
- The deployment succeeds in the portal but the app cannot call it because `.env` uses the model name instead of the deployment name.

Fixes:

- Use the smallest model deployments that support the lesson.
- Try another supported region if the selected one has no quota.
- Reuse existing chat and embedding deployments if your subscription allows that path.
- Put deployment names in `.env`, not raw model names.

## Missing Environment Variables

If local commands complain about missing settings, recreate the environment file:

```bash
cp .env.example .env
```

Fill in the values produced by Terraform or shown in the Azure Portal. Then reload the file:

```bash
set -a
source .env
set +a
```

Useful checks:

```bash
echo "$AZURE_RESOURCE_GROUP"
echo "$AZURE_OPENAI_ENDPOINT"
echo "$AZURE_SEARCH_ENDPOINT"
```

If those print empty lines, your shell has not loaded `.env` or the variable names do not match the template.

## Key-Based Auth Problems

This teaching repo uses key-based local auth. A `401` or `403` usually means the key, endpoint, or resource is wrong.

Check:

- The Azure OpenAI key belongs to the resource in `AZURE_OPENAI_ENDPOINT`.
- The Azure AI Search key belongs to the service in `AZURE_SEARCH_ENDPOINT`.
- Index creation and rebuild scripts use a Search admin key, not only a query key.
- Any regenerated key has also been updated in `.env`.

## Azure AI Search Issues

Search service names, index names, and endpoints must match exactly.

Common symptoms:

- `404` for an index: the index has not been created yet or `AZURE_SEARCH_INDEX_NAME` is wrong.
- `403` during indexing: the key does not have permission to write.
- Terraform cannot create the service name: Search service names are globally constrained, so choose a unique name if the lesson variable allows it.

Later parts will add more detail once indexing scripts exist.

## Blob Storage Issues

Blob container errors usually come from a missing account name, missing container, or a key/permission mismatch.

Check:

```bash
echo "$AZURE_STORAGE_ACCOUNT_NAME"
echo "$AZURE_STORAGE_CONTAINER_NAME"
az resource list --resource-group "$AZURE_RESOURCE_GROUP" --output table
```

For Part 1, Blob Storage is part of the target Azure architecture. Later parts decide whether files are read from local sample docs first, uploaded to Blob Storage, or both.

## Cost And Cleanup

If charges continue after the lesson:

1. Confirm you are looking at the subscription used by Azure CLI.
2. Inspect the resource group in the Azure Portal.
3. Run `terraform plan -destroy` from `infra/`.
4. If the state is lost and the resource group is dedicated to this repo, delete the group:

```bash
az group delete --name "$AZURE_RESOURCE_GROUP" --yes --no-wait
```

Deleting a shared resource group can remove unrelated resources. Keep this project in its own group.
