# CloudNotes v1.0 — Linux Server Deployment Guide

This document details the production-ready Linux server deployment for **CloudNotes v1.0**, incorporating Gunicorn WSGI application server, process management, environment variables configuration, PostgreSQL database migration, network firewall rules, and persistence validation.

---

## 1. Linux Server Environment Choice

- **Chosen Environment**: Linux Server Environment (WSL2 Ubuntu / Linux VM / Docker Container).
- **OS / Runtime**: Ubuntu 22.04 LTS / Debian Linux with Python 3.11+, Gunicorn 26.1.0, and PostgreSQL 15+.
- **Binding & Network Setup**: Bound to `0.0.0.0:5000` to accept external host network connections.

---

## 2. Environment Variables Configuration

All configuration is externalized from application source code into environment variables using `python-dotenv`.

### File Structure
- `.env.example`: Committed to Git with dummy/placeholder values. Real credentials MUST NOT be committed.
- `.env`: Excluded via `.gitignore`. Contains runtime production configuration.

### Sample Configuration (`.env`)
```env
DATABASE_URL=postgresql://cloudnotes_user:cloudnotes_password@localhost:5432/cloudnotes
SECRET_KEY=super-secret-production-key-98765
UPLOAD_FOLDER=uploads
PORT=5000
```

---

## 3. Step-by-Step Installation & Deployment Commands

Run the following commands on your Linux server or execute the included `setup.sh` script:

```bash
# 1. Update system packages
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Install Python 3, virtual environment tools, PostgreSQL, and firewall
sudo apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib ufw curl

# 3. Start and enable PostgreSQL service
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 4. Create PostgreSQL database & user for CloudNotes
sudo -u postgres psql -c "CREATE DATABASE cloudnotes;"
sudo -u postgres psql -c "CREATE USER cloudnotes_user WITH PASSWORD 'cloudnotes_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cloudnotes TO cloudnotes_user;"

# 5. Clone repository and navigate into project directory
cd /var/www/cloudnotes-v1

# 6. Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 7. Configure environment variables
cp .env.example .env
# Edit .env with your real DB credentials & secret key
```

---

## 4. Managed Background Service Setup (`systemd` & Docker)

To ensure **always-on operation**, auto-start on system boot, and auto-restart on process crash, CloudNotes is managed by a background supervisor service.

### Option A: `systemd` Unit File (`/etc/systemd/system/cloudnotes.service`)

```ini
[Unit]
Description=CloudNotes v1.0 Managed Service
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=/var/www/cloudnotes-v1
EnvironmentFile=/var/www/cloudnotes-v1/.env
ExecStart=/var/www/cloudnotes-v1/.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 3 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Service Activation Commands:
```bash
sudo cp cloudnotes.service /etc/systemd/system/cloudnotes.service
sudo systemctl daemon-reload
sudo systemctl enable cloudnotes.service
sudo systemctl start cloudnotes.service
sudo systemctl status cloudnotes.service
```

### Option B: Docker Container Policy (`docker-compose.yml`)

For containerized environments, the service uses `restart: always`:

```bash
docker compose up -d --build
```

---

## 5. Network & Firewall Configuration

CloudNotes is bound to `0.0.0.0:5000` so that it listens on all network interfaces.

### OS Firewall Setup (`ufw`)
```bash
# Allow HTTP port 5000 and SSH port 22
sudo ufw allow 5000/tcp
sudo ufw allow 22/tcp
sudo ufw enable
sudo ufw status verbose
```

---

## 6. Request Path Architecture

When a user opens CloudNotes from a host web browser, the network packet flows through the following stages:

```
+------------------+     +-------------------+     +-------------------------+     +------------------+     +----------------------------+
|  Host Web        | --> |  Host / VM        | --> |  OS Firewall (UFW)      | --> |  Linux Server    | --> |  Flask / Gunicorn App      |
|  Browser         |     |  Network Bridge   |     |  Open Port (5000/tcp)   |     |  (Systemd / VM)  |     |  Listening on 0.0.0.0:5000 |
+------------------+     +-------------------+     +-------------------------+     +------------------+     +----------------------------+
```

### Explanation of Request Flow:
1. **Your Web Browser**: Sends an HTTP request to `http://<SERVER_IP>:5000/` or `http://localhost:5000/`.
2. **Host / VM Network**: Routes the IP packet across the virtual network bridge / port forwarding interface to the Linux virtual environment.
3. **OS Firewall / Open Port**: UFW inspects incoming TCP traffic on port `5000`. Traffic is permitted through the firewall rules (`sudo ufw allow 5000/tcp`).
4. **Linux Server**: Passes the packet to the socket listening on `0.0.0.0:5000`.
5. **Flask on 0.0.0.0:5000**: Gunicorn receives the HTTP request, routes it to the Flask application handler, queries PostgreSQL, and returns the HTML/JSON response back to the client browser.

---

## 7. Service Verification & Proof of Resilience

### Proof 1: Auto-Restart on Process Crash (`kill -9` Test)
```bash
# Check service running PID
sudo systemctl status cloudnotes.service

# Simulate application crash by killing the main Gunicorn master process
sudo kill -9 $(pgrep -f gunicorn | head -n 1)

# Check service status after crash - systemd automatically restarts Gunicorn
sudo systemctl status cloudnotes.service
```

### Proof 2: Auto-Start on System Boot
```bash
# Reboot server
sudo reboot

# After reboot completes, verify service started automatically
sudo systemctl is-active cloudnotes.service
# Output: active
```

---

## 8. Persistence Verification with PostgreSQL

1. **Add a Note via API or UI**:
   ```bash
   curl -X POST http://localhost:5000/api/notes \
     -F "title=PostgreSQL Persistence Test" \
     -F "body=This note is stored in PostgreSQL and must survive server restart."
   ```
2. **Restart Application Service & Server**:
   ```bash
   sudo systemctl restart cloudnotes.service
   ```
3. **Confirm Note Remains in Database**:
   ```bash
   curl -s http://localhost:5000/api/notes | grep "PostgreSQL Persistence Test"
   ```
   *Result*: Note is fetched successfully from PostgreSQL tables after restart, confirming data persistence.
