output "resource_group_name" {
  description = "Resource group containing all resources for this learning project."
  value       = azurerm_resource_group.main.name
}

output "location" {
  description = "Azure region used by the resources."
  value       = azurerm_resource_group.main.location
}

output "storage_account_name" {
  description = "Storage account name for document blobs."
  value       = azurerm_storage_account.documents.name
}

output "storage_blob_endpoint" {
  description = "Blob service endpoint for the storage account."
  value       = azurerm_storage_account.documents.primary_blob_endpoint
}

output "storage_container_name" {
  description = "Private blob container for source documents."
  value       = azurerm_storage_container.documents.name
}

output "search_service_name" {
  description = "Azure AI Search service name."
  value       = azurerm_search_service.main.name
}

output "search_endpoint" {
  description = "Azure AI Search endpoint for app configuration."
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "openai_account_name" {
  description = "Azure OpenAI account name."
  value       = azurerm_cognitive_account.openai.name
}

output "openai_endpoint" {
  description = "Azure OpenAI endpoint for app configuration."
  value       = azurerm_cognitive_account.openai.endpoint
}

output "chat_deployment_name" {
  description = "Azure OpenAI chat deployment name for app configuration."
  value       = azurerm_cognitive_deployment.chat.name
}

output "embedding_deployment_name" {
  description = "Azure OpenAI embedding deployment name for app configuration."
  value       = azurerm_cognitive_deployment.embedding.name
}

output "app_env_values" {
  description = "Non-secret values that can be copied into .env after terraform apply."
  value = {
    AZURE_RESOURCE_GROUP              = azurerm_resource_group.main.name
    AZURE_LOCATION                    = azurerm_resource_group.main.location
    AZURE_OPENAI_ENDPOINT             = azurerm_cognitive_account.openai.endpoint
    AZURE_OPENAI_CHAT_DEPLOYMENT      = azurerm_cognitive_deployment.chat.name
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = azurerm_cognitive_deployment.embedding.name
    AZURE_SEARCH_ENDPOINT             = "https://${azurerm_search_service.main.name}.search.windows.net"
    AZURE_STORAGE_ACCOUNT_NAME        = azurerm_storage_account.documents.name
    AZURE_STORAGE_CONTAINER_NAME      = azurerm_storage_container.documents.name
  }
}
