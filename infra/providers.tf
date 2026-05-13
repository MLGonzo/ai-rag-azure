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

  # AzureRM 4.x requires a subscription for plan/apply. Set this variable
  # or export ARM_SUBSCRIPTION_ID before running Terraform.
  subscription_id = var.subscription_id
}
