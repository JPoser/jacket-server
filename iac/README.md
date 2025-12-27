# Infrastructure as Code - Oracle Cloud Infrastructure

This directory contains Terraform configuration to deploy the jacket-server to Oracle Cloud Infrastructure (OCI) on a free tier VM.

## Directory Structure

- `main.tf`, `variables.tf`, `outputs.tf` - Main infrastructure configuration
- `backend/` - Terraform state backend setup (Object Storage bucket)
- `backend.tf.example` - Example backend configuration (copy to `backend.tf` after setting up backend)
- `terraform.tfvars.example` - Example variables file

## Setup Steps

### Step 1: Set Up State Backend (First Time Only)

Before deploying the main infrastructure, set up the remote state backend:

```bash
cd iac/backend
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OCI credentials
terraform init
terraform apply
```

Note the outputs (bucket name, namespace, endpoint) - you'll need these for the main Terraform.

### Step 2: Configure Main Terraform Backend

1. Copy the backend configuration example:
   ```bash
   cd iac
   cp backend.tf.example backend.tf
   ```

2. Edit `backend.tf` with the values from the backend setup output

3. Set environment variables for OCI authentication:
   ```bash
   export AWS_ACCESS_KEY_ID="<your-oci-user-ocid>"
   export AWS_SECRET_ACCESS_KEY="<your-oci-api-private-key-content>"
   export AWS_DEFAULT_REGION="<your-oci-region>"
   ```

   Or use a credentials file (see OCI documentation for S3-compatible API access).

### Step 3: Deploy Main Infrastructure

Continue with the main deployment steps below.

## Prerequisites

1. **OCI Account** with Always Free tier eligibility
2. **Terraform** installed (>= 1.0)
3. **OCI CLI** configured with API keys
4. **SSH Key Pair** for accessing the VM

## OCI Setup

### 1. Create API Key

1. Go to OCI Console → Identity → Users → Your User
2. Click "API Keys" → "Add API Key"
3. Download the private key and note the fingerprint
4. Copy the configuration shown (you'll need the OCIDs)

### 2. Get Required OCIDs

You'll need:
- **Tenancy OCID**: Found in Administration → Tenancy Details
- **User OCID**: Found in Identity → Users → Your User
- **Compartment OCID**: Found in Identity → Compartments → Your Compartment

### 3. Create VCN and Subnet (if needed)

If you don't have a VCN yet:
1. Go to Networking → Virtual Cloud Networks
2. Create a VCN with Internet Gateway
3. Create a public subnet
4. Note the names (default is usually "Default VCN" and "Default Subnet")

## Configuration

1. **Ensure backend is set up** (see Step 1 above)

2. **Copy the example variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit `terraform.tfvars`** with your values:
   - OCI authentication details
   - Compartment OCID
   - SSH public key
   - VCN and subnet names
   - Application port (default: 5000)

3. **Add `terraform.tfvars` to `.gitignore`** (already done)

## Deployment

1. **Initialize Terraform** (with backend configured):
   ```bash
   cd iac
   terraform init
   # If backend.tf is configured, Terraform will ask to migrate state
   # Type 'yes' to migrate to remote state
   ```

2. **Review the plan:**
   ```bash
   terraform plan
   ```

3. **Apply the configuration:**
   ```bash
   terraform apply
   ```

4. **Note the outputs:**
   - Public IP address
   - SSH command
   - Application URL

## Post-Deployment

After the VM is created, you need to:

1. **SSH into the instance:**
   ```bash
   ssh opc@<public-ip>
   ```

2. **Deploy your code:**
   ```bash
   cd /opt/jacket-server
   # Option 1: Clone from git
   git clone https://github.com/yourusername/jacket-server.git .

   # Option 2: Use scp to copy files
   # From your local machine:
   scp -r . opc@<public-ip>:/opt/jacket-server/
   ```

3. **Create config.ini:**
   ```bash
   cd /opt/jacket-server
   cp config.example.ini config.ini
   # Edit config.ini with your credentials
   nano config.ini
   ```

4. **Build and start with Docker Compose:**
   ```bash
   cd /opt/jacket-server
   docker compose up -d --build
   ```

5. **Check container status:**
   ```bash
   docker compose ps
   docker compose logs -f
   ```

6. **Useful Docker commands:**
   ```bash
   # Stop the service
   docker compose down

   # Restart the service
   docker compose restart

   # View logs
   docker compose logs -f jacket-server

   # Rebuild after code changes
   docker compose up -d --build
   ```

## Security Considerations

- **SSH Access**: By default, SSH is allowed from anywhere (0.0.0.0/0). For better security, set `ssh_source_cidr` in `terraform.tfvars` to your IP address (e.g., "203.0.113.1/32")
- **Application Access**: The Flask app port is configurable via `app_source_cidr`. Restrict to specific IPs in production
- **Firewall**: All firewall rules are managed via OCI Security Lists (no ufw needed)
- **SSL/TLS**: Use a reverse proxy (nginx) with SSL/TLS in production
- **Secrets**: Keep your `terraform.tfvars` file secure and never commit it
- **API Keys**: Ensure your `config.ini` with API keys is never committed to git

## Cost

This configuration uses:
- **VM.Standard.E2.1.Micro** - Always Free eligible (1 OCPU, 1GB RAM)
- **Block Storage** - 200GB free tier
- **Network** - Free tier includes 10TB egress per month

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

## Troubleshooting

### Instance not accessible
- Check security list rules
- Verify internet gateway is attached to VCN
- Check route table has default route (0.0.0.0/0 → Internet Gateway)

### Service won't start
- Check logs: `sudo journalctl -u jacket-server -n 50`
- Verify config.ini exists and has correct values
- Check if port is already in use: `sudo netstat -tlnp | grep 5000`

### Can't SSH
- Verify security list allows port 22
- Check SSH key is correct in terraform.tfvars
- Verify instance is running in OCI console
