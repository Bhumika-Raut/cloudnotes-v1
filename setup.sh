#!/bin/bash
set -e

echo "=== CloudNotes v1.0 Linux Deployment Setup Script ==="

# 1. Update system packages
echo "[1/7] Updating package index..."
sudo apt-get update -y

# 2. Install required packages
echo "[2/7] Installing Python, PostgreSQL, and network tools..."
sudo apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib ufw curl

# 3. Enable and start PostgreSQL service
echo "[3/7] Enabling and starting PostgreSQL service..."
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 4. Create PostgreSQL database and user for CloudNotes
echo "[4/7] Setting up PostgreSQL database and user..."
sudo -u postgres psql -c "CREATE DATABASE cloudnotes;" || echo "Database cloudnotes already exists."
sudo -u postgres psql -c "CREATE USER cloudnotes_user WITH PASSWORD 'cloudnotes_password';" || echo "User cloudnotes_user already exists."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cloudnotes TO cloudnotes_user;" || echo "Privileges granted."

# 5. Set up Python virtual environment and dependencies
echo "[5/7] Setting up Python environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Configure environment variables
echo "[6/7] Setting up .env configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    sed -i 's/YOUR_PASSWORD/cloudnotes_password/g' .env
fi

# 7. Configure UFW Firewall and systemd service
echo "[7/7] Configuring UFW Firewall and systemd service..."
sudo ufw allow 5000/tcp
sudo ufw allow 22/tcp
echo "y" | sudo ufw enable || true

sudo cp cloudnotes.service /etc/systemd/system/cloudnotes.service
sudo systemctl daemon-reload
sudo systemctl enable cloudnotes.service
sudo systemctl restart cloudnotes.service

echo "=== Setup Complete! Checking CloudNotes service status ==="
sudo systemctl status cloudnotes.service --no-pager
