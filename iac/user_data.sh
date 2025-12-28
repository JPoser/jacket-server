#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git

# Install Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add opc user to docker group
usermod -aG docker opc

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Create app directory
mkdir -p /opt/jacket-server
chown opc:opc /opt/jacket-server

# Note: Firewall rules are managed via OCI Security Lists
# No need for ufw - OCI handles all firewall rules at the network level

# Log completion
echo "User data script completed at $(date)" >> /var/log/user-data.log
echo "Docker installed and ready. Next steps:" >> /var/log/user-data.log
echo "1. Deploy your code to /opt/jacket-server" >> /var/log/user-data.log
echo "2. Create config.ini with your credentials" >> /var/log/user-data.log
echo "3. Run: cd /opt/jacket-server && docker compose up -d" >> /var/log/user-data.log
