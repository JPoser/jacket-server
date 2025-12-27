# Terraform State Backend Setup

This directory contains Terraform configuration to create an OCI Object Storage bucket for storing Terraform state files.

## Why Use Remote State?

- **Team Collaboration**: Multiple team members can work with the same state
- **State Locking**: Prevents concurrent modifications
- **State History**: Versioning enabled for recovery
- **Security**: State stored securely in OCI Object Storage

## Setup

1. **Copy the example variables file:**
   ```bash
   cd iac/backend
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit `terraform.tfvars`** with your OCI credentials (same as main terraform)

3. **Initialize and apply:**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Note the outputs** - You'll need the bucket name and namespace for the main Terraform backend configuration

## Backend Configuration

After creating the bucket, you'll need to add the backend configuration to the main Terraform. The output from this configuration provides the exact backend block to use.

Alternatively, you can manually configure the backend in `iac/backend.tf` (see main README).

## Security

- Bucket is created with `NoPublicAccess` - only accessible via OCI API
- Versioning is enabled for state file recovery
- Ensure your OCI user has proper IAM policies:
  - `Allow group <group> to manage objects in compartment <compartment>`
  - `Allow group <group> to read buckets in compartment <compartment>`

## Cleanup

To destroy the state bucket (⚠️ **WARNING**: This will delete your Terraform state!):
```bash
terraform destroy
```

**Note**: Only destroy this if you're sure you want to lose all Terraform state!
