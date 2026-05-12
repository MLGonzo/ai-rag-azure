# Infrastructure

Infrastructure files will be added in a later part.

This directory exists in Part 1 so learners know where Azure resource definitions or provisioning scripts will live. Do not add Terraform state, local variable files, credentials, or generated deployment output to Git.

Expected future resources may include:

- a resource group;
- an Azure OpenAI resource or references to existing deployments;
- an Azure AI Search service;
- optional storage for source documents;
- outputs needed by `.env`.

Teardown steps should be documented beside any infrastructure that creates billable resources.

