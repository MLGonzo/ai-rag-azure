terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}

  # AzureRM 4.x requires a subscription ID for plan/apply even when auth comes
  # from Azure CLI. Prefer exporting ARM_SUBSCRIPTION_ID from `az account show`.
  subscription_id = var.subscription_id
}
