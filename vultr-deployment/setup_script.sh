#!/bin/bash
# ------------------------------------------------------------------
# Vultr Cloud Compute - Startup Configuration
# Target: Ubuntu 24.04 LTS (Vultr)
# ------------------------------------------------------------------

# 1. Update the Vultr Instance
echo "Updating Vultr instance..."
apt-get update && apt-get upgrade -y

# 2. Install Python, Git, and Pip
echo "Installing dependencies..."
apt-get install -y python3-pip python3-venv git

# 3. Clone the Repository
echo "Cloning AeroCraft..."
cd /opt
git clone https://github.com/YOUR_GITHUB_USERNAME/AeroCraft.git
cd AeroCraft

# 4. Setup Environment
# Note: Secrets would be injected via Vultr User Data or Secret Manager
echo "Setting up Virtual Environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Start the Application
echo "Starting Application on Port 80..."
uvicorn main:app --host 0.0.0.0 --port 80