variable "resource_group_name" {
  description = "RG name in Azure"
}

variable "resource_group_location" {
  type        = string
  description = "RG location in Azure"
}

variable "rec_storage_account_name" {
  type        = string
  description = "Storage account name for ML Workspace in Azure"
}

variable "webapp_index_document" {
  type        = string
  description = "Nombre del documento de la página de inicio de la aplicación web"
}

variable "cosmosdb_account_name" {
  type        = string
  description = "Cosmos DB account name in Azure"
}

variable "cosmosdb_mongodb_db_name" {
  type        = string
  description = "MongoDB database name in Azure"
}

variable "app_service_plan_name" {
  type        = string
  description = "Application Service Plan name in Azure"

}

variable "function_app_name" {
  type        = string
  description = "Azure Functions app name in Azure"
}

variable "api_managment_name" {
  type        = string
  description = "API Managment name in Azure"
}

variable "publisher_name" {
  type = string
}

variable "publisher_email" {
  type = string
}