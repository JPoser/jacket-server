terraform {
  required_version = ">= 1.12"
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

# Get availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

# Get the first availability domain
data "oci_identity_availability_domain" "ad" {
  compartment_id = var.compartment_ocid
  ad_number      = 2
}

# Create VCN
resource "oci_core_vcn" "vcn" {
  compartment_id = var.compartment_ocid
  display_name   = var.vcn_name
  cidr_blocks    = ["10.0.0.0/16"]
  dns_label      = "jacketserver"
  freeform_tags  = var.freeform_tags
}

# Create Internet Gateway
resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.vcn_name}-igw"
  enabled        = true
  freeform_tags  = var.freeform_tags
}

# Create Route Table
resource "oci_core_route_table" "rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.vcn_name}-rt"
  freeform_tags  = var.freeform_tags

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.igw.id
  }
}

# Create Subnet
resource "oci_core_subnet" "subnet" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.vcn.id
  display_name      = var.subnet_name
  cidr_block        = "10.0.1.0/24"
  dns_label         = "subnet"
  route_table_id    = oci_core_route_table.rt.id
  security_list_ids = [oci_core_security_list.jacket_server_sl.id]
  freeform_tags     = var.freeform_tags
}

# Get image for Ubuntu 22.04
data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.E2.1.Micro"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# Security list for allowing HTTP/HTTPS and SSH
resource "oci_core_security_list" "jacket_server_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "jacket-server-security-list"
  freeform_tags  = var.freeform_tags

  # Allow SSH (configurable source CIDR)
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = var.ssh_source_cidr
    source_type = "CIDR_BLOCK"
    description = "SSH access"
    tcp_options {
      min = 22
      max = 22
    }
  }

  # Allow Flask app port (configurable source CIDR)
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = var.app_source_cidr
    source_type = "CIDR_BLOCK"
    description = "Flask application access"
    tcp_options {
      min = var.app_port
      max = var.app_port
    }
  }

  # Allow all outbound traffic
  egress_security_rules {
    protocol         = "all"
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
  }
}

# Compute instance
resource "oci_core_instance" "jacket_server" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domain.ad.name
  display_name        = "jacket-server"
  shape               = "VM.Standard.E2.1.Micro" # Always Free eligible
  freeform_tags       = var.freeform_tags

  create_vnic_details {
    subnet_id        = oci_core_subnet.subnet.id
    assign_public_ip = true
    hostname_label   = "jacketserver"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/user_data.sh", {
      app_port = var.app_port
    }))
  }

  timeouts {
    create = "10m"
  }
}
