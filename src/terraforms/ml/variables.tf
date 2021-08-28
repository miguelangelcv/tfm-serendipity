variable "resource_group_name" {
  description = "RG name in Azure"
}

variable "resource_group_location" {
  type        = string
  description = "RG location in Azure"
}

variable "mlw_application_insights_name" {
  type        = string
  description = "Aplication Insight name in Azure"
}

variable "mlw_key_vault_name" {
  type        = string
  description = "Key Vault name for ML Workspace in Azure"
}

variable "mlw_storage_account_name" {
  type        = string
  description = "Storage account name for ML Workspace in Azure"
}

variable "ml_workspace_name" {
  type        = string
  description = "Machine Learning Workspace name in Azure"
}

variable "mlw_virtual_network_name" {
  type        = string
  description = "Virtual network name for ML workspace in Azure"
}

variable "mlw_subnetwork_name" {
  type        = string
  description = "Subnetwork name for ML workspace in Azure"
}

variable "ssh_key" {
  type        = string
  description = "SSH Key for compute instances"
}

variable "ml_compute_instance_name" {
  type        = string
  description = "Machine Learning Compute Intance name"
}