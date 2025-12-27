terraform {
  required_version = ">= 1.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# Get namespace
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_ocid
}

# Create Object Storage bucket for Terraform state
resource "oci_objectstorage_bucket" "terraform_state" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = var.bucket_name
  access_type    = "NoPublicAccess" # Private bucket
  freeform_tags  = var.freeform_tags

  # Enable versioning for state file safety
  versioning = "Enabled"

  # Retention rules (optional - uncomment if needed)
  # retention_rules {
  #   display_name = "terraform-state-retention"
  #   duration {
  #     time_amount = "365"
  #     time_unit   = "DAYS"
  #   }
  # }
}
