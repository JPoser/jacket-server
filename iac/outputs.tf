output "instance_public_ip" {
  description = "Public IP address of the instance"
  value       = oci_core_instance.jacket_server.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the instance"
  value       = oci_core_instance.jacket_server.private_ip
}

output "instance_ocid" {
  description = "OCID of the instance"
  value       = oci_core_instance.jacket_server.id
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = var.enable_tailscale ? "ssh ubuntu@jacketserver (via Tailscale)" : "ssh ubuntu@${oci_core_instance.jacket_server.public_ip}"
}

output "app_url" {
  description = "URL to access the application"
  value       = "http://${oci_core_instance.jacket_server.public_ip}:${var.app_port}"
}
