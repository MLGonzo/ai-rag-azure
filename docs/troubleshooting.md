# Troubleshooting

This page starts as a placeholder for common learner issues. Later parts will add exact errors and fixes as real commands, SDK calls, and Azure resources are introduced.

## First Checks

- Confirm you are using the intended checkpoint branch or tag.
- Confirm your virtual environment is active.
- Confirm `.env` exists locally and was copied from `.env.example`.
- Confirm secrets are not committed.
- Confirm Azure CLI is logged in with the expected tenant and subscription.

## Common Areas To Inspect Later

### Authentication

This learning project uses key-based auth for local app calls. If an Azure SDK call fails, confirm the relevant key is present in your local `.env`, has not expired or been regenerated, and belongs to the resource named by the endpoint.

### Azure OpenAI

Model names and deployment names are different. The app will use deployment names from `.env`, not raw model names.

### Azure AI Search

Index names must match exactly. Recreating an index can delete indexed data, so later scripts should make destructive actions visible.

### Cost And Cleanup

If resources continue to bill after a lesson, inspect the resource group in the Azure Portal and remove resources that are no longer needed.

## Still A Placeholder

Part 1 does not include live Azure calls, indexing, retrieval, or chat. Those troubleshooting sections will be filled in when the behavior exists.
