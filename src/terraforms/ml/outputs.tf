output "computeinstance_username" {
  value = azurerm_machine_learning_compute_instance.computeinstance.ssh[0].username
}