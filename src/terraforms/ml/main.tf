data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name[terraform.workspace]
  location = var.resource_group_location
}

resource "azurerm_application_insights" "mlw_insights" {
  name                = var.mlw_application_insights_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
}

resource "azurerm_key_vault" "mlw_key" {
  name                = var.mlw_key_vault_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
}

resource "azurerm_storage_account" "mlw-storage" {
  name                     = var.mlw_storage_account_name
  location                 = azurerm_resource_group.rg.location
  resource_group_name      = azurerm_resource_group.rg.name
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_machine_learning_workspace" "mlw" {
  name                    = var.ml_workspace_name
  location                = azurerm_resource_group.rg.location
  resource_group_name     = azurerm_resource_group.rg.name
  application_insights_id = azurerm_application_insights.mlw_insights.id
  key_vault_id            = azurerm_key_vault.mlw_key.id
  storage_account_id      = azurerm_storage_account.mlw-storage.id

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_virtual_network" "mlw-vnet" {
  name                = var.mlw_virtual_network_name
  address_space       = ["10.1.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_subnet" "mlw-subnet" {
  name                 = var.mlw_subnetwork_name
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.mlw-vnet.name
  address_prefixes     = ["10.1.0.0/24"]
}

resource "azurerm_machine_learning_compute_instance" "computeinstance" {
  name                          = var.ml_compute_instance_name
  location                      = azurerm_resource_group.rg.location
  machine_learning_workspace_id = azurerm_machine_learning_workspace.mlw.id
  virtual_machine_size          = "Standard_F32s_v2"
  authorization_type            = "personal"
  ssh {
    public_key = var.ssh_key
  }
  subnet_resource_id = azurerm_subnet.mlw-subnet.id
  description        = "Main compute instance for Serenditipy-ML"
}