variable "subscription_id" {
  description = "Azure subscription ID for Terraform. Leave null if you export ARM_SUBSCRIPTION_ID."
  type        = string
  default     = null
}

variable "location" {
  description = "Azure region for the learning resources. Pick a region where your Azure OpenAI models are available."
  type        = string
  default     = "uksouth"
}

variable "project_name" {
  description = "Short lowercase project prefix used in resource names. Keep it short because storage account names have a 24-character limit."
  type        = string
  default     = "smallrag"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,13}[a-z0-9]$", var.project_name)) && !can(regex("--", var.project_name))
    error_message = "Use 3-15 lowercase letters, numbers, or hyphens. Start with a letter, end with a letter or number, and avoid consecutive hyphens."
  }
}

variable "tags" {
  description = "Optional tags applied to all supported resources."
  type        = map(string)
  default     = {}
}

variable "storage_container_name" {
  description = "Blob container for source documents used by later ingestion steps."
  type        = string
  default     = "rag-documents"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", var.storage_container_name)) && !can(regex("--", var.storage_container_name))
    error_message = "Use 3-63 lowercase letters, numbers, or hyphens. Start and end with a letter or number, and avoid consecutive hyphens."
  }
}

variable "search_sku" {
  description = "Azure AI Search SKU. Use basic for a small but useful learning service; free can be limited or unavailable in some subscriptions."
  type        = string
  default     = "basic"

  validation {
    condition     = contains(["free", "basic", "standard"], var.search_sku)
    error_message = "Use one of: free, basic, standard."
  }
}

variable "openai_account_sku_name" {
  description = "SKU for the Azure OpenAI account. S0 is the normal starting point."
  type        = string
  default     = "S0"
}

variable "chat_deployment_name" {
  description = "Azure OpenAI deployment name used by the app for chat completions."
  type        = string
  default     = "gpt-4o-mini"
}

variable "chat_model_name" {
  description = "Chat model to deploy."
  type        = string
  default     = "gpt-4o-mini"
}

variable "chat_model_version" {
  description = "Chat model version. Change this if your chosen region exposes a different version."
  type        = string
  default     = "2024-07-18"
}

variable "embedding_deployment_name" {
  description = "Azure OpenAI deployment name used by the app for embeddings."
  type        = string
  default     = "text-embedding-3-small"
}

variable "embedding_model_name" {
  description = "Embedding model to deploy."
  type        = string
  default     = "text-embedding-3-small"
}

variable "embedding_model_version" {
  description = "Embedding model version. The current text-embedding-3-small version is 1."
  type        = string
  default     = "1"
}

variable "model_deployment_sku_name" {
  description = "SKU for Azure OpenAI model deployments. Change to GlobalStandard if your region/quota requires it."
  type        = string
  default     = "Standard"

  validation {
    condition = contains([
      "Standard",
      "GlobalStandard",
      "DataZoneStandard"
    ], var.model_deployment_sku_name)
    error_message = "Use one of: Standard, GlobalStandard, DataZoneStandard."
  }
}

variable "model_deployment_capacity" {
  description = "Model deployment capacity in thousands of tokens per minute. Keep this low for learning."
  type        = number
  default     = 1

  validation {
    condition     = var.model_deployment_capacity >= 1 && var.model_deployment_capacity <= 20
    error_message = "Use a capacity between 1 and 20 for this learning project."
  }
}
