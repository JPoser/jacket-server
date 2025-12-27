output "bucket_name" {
  description = "Name of the state bucket"
  value       = oci_objectstorage_bucket.terraform_state.name
}

output "bucket_namespace" {
  description = "Namespace of the state bucket"
  value       = oci_objectstorage_bucket.terraform_state.namespace
}

output "backend_endpoint" {
  description = "S3-compatible endpoint URL for the bucket"
  value       = "https://${data.oci_objectstorage_namespace.ns.namespace}.compat.objectstorage.${var.region}.oraclecloud.com"
}

output "backend_config" {
  description = "Backend configuration block for main Terraform (copy to iac/backend.tf)"
  value = <<-EOT
terraform {
  backend "s3" {
    bucket   = "${oci_objectstorage_bucket.terraform_state.name}"
    key      = "jacket-server/terraform.tfstate"
    region   = "${var.region}"
    endpoint = "https://${data.oci_objectstorage_namespace.ns.namespace}.compat.objectstorage.${var.region}.oraclecloud.com"
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style             = true
  }
}
  EOT
  sensitive = false
}
