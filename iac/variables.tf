variable "tenancy_ocid" {
  description = "OCID of your tenancy"
  type        = string
}

variable "user_ocid" {
  description = "OCID of the user calling the API"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint of the API key"
  type        = string
}

variable "private_key" {
  description = "Private key content for OCI API authentication"
  type        = string
  sensitive   = true
}

variable "compartment_ocid" {
  description = "OCID of the compartment where resources will be created"
  type        = string
}

variable "region" {
  description = "OCI region (e.g., us-ashburn-1, us-phoenix-1)"
  type        = string
  default     = "us-ashburn-1"
}

variable "vcn_name" {
  description = "Name of the existing VCN to use"
  type        = string
  default     = "Default VCN"
}

variable "subnet_name" {
  description = "Name of the existing subnet to use"
  type        = string
  default     = "Default Subnet"
}

variable "ssh_public_key" {
  description = "Public SSH key for accessing the instance"
  type        = string
}

variable "app_port" {
  description = "Port the Flask app will run on"
  type        = number
  default     = 5000
}

variable "ssh_source_cidr" {
  description = "CIDR block allowed to SSH to the instance (use your IP for security)"
  type        = string
  default     = "0.0.0.0/0" # Allow from anywhere - change this to your IP for better security
}

variable "app_source_cidr" {
  description = "CIDR block allowed to access the Flask app (0.0.0.0/0 for public access)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "freeform_tags" {
  description = "Free-form tags for resources"
  type        = map(string)
  default = {
    Project = "jacket-server"
  }
}
