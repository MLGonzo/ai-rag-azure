resource "random_string" "suffix" {
  length  = 6
  lower   = true
  numeric = true
  special = false
  upper   = false
}

locals {
  suffix = random_string.suffix.result

  # These resources need globally unique names, so a short random suffix keeps
  # the example copy-pasteable without introducing a naming module.
  resource_group_name  = "rg-${var.project_name}-${local.suffix}"
  search_service_name  = "srch-${var.project_name}-${local.suffix}"
  openai_account_name  = "oai-${var.project_name}-${local.suffix}"
  storage_account_name = "st${replace(var.project_name, "-", "")}${local.suffix}"

  common_tags = merge(
    {
      project    = var.project_name
      managed_by = "terraform"
      purpose    = "rag-learning"
    },
    var.tags
  )
}

resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_storage_account" "documents" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # Public blob access is not needed for local ingestion. The account still has
  # a public endpoint so learners can use normal SDK calls without networking.
  allow_nested_items_to_be_public = false
  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"

  tags = local.common_tags
}

resource "azurerm_storage_container" "documents" {
  name                  = var.storage_container_name
  storage_account_id    = azurerm_storage_account.documents.id
  container_access_type = "private"
}

resource "azurerm_search_service" "main" {
  name                = local.search_service_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.search_sku

  # Key auth keeps the first learning path simple. Later hardening can replace
  # this with managed identity/RBAC without changing the app shape.
  local_authentication_enabled  = true
  public_network_access_enabled = true

  tags = local.common_tags
}

resource "azurerm_cognitive_account" "openai" {
  name                = local.openai_account_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  kind                = "OpenAI"
  sku_name            = var.openai_account_sku_name

  # Azure OpenAI is managed through the Cognitive Services control plane. A
  # custom subdomain gives SDKs the expected https://name.openai.azure.com shape.
  custom_subdomain_name         = local.openai_account_name
  local_auth_enabled            = true
  public_network_access_enabled = true

  tags = local.common_tags
}

resource "azurerm_cognitive_deployment" "chat" {
  name                   = var.chat_deployment_name
  cognitive_account_id   = azurerm_cognitive_account.openai.id
  version_upgrade_option = "OnceNewDefaultVersionAvailable"

  model {
    format  = "OpenAI"
    name    = var.chat_model_name
    version = var.chat_model_version
  }

  sku {
    name     = var.model_deployment_sku_name
    capacity = var.chat_deployment_capacity_thousands
  }
}

resource "azurerm_cognitive_deployment" "embedding" {
  name                   = var.embedding_deployment_name
  cognitive_account_id   = azurerm_cognitive_account.openai.id
  version_upgrade_option = "OnceNewDefaultVersionAvailable"

  model {
    format  = "OpenAI"
    name    = var.embedding_model_name
    version = var.embedding_model_version
  }

  sku {
    name     = var.model_deployment_sku_name
    capacity = var.embedding_deployment_capacity_thousands
  }
}
