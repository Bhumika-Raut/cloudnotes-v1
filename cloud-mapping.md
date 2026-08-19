# Cloud Notes v1.0 — Local Deployment to Google Compute Engine Mapping

This document maps each component of our local Linux server deployment to its equivalent service in **Google Cloud Platform (GCP) Compute Engine** and associated cloud services.

---

## Component Mapping Table

| What you built locally | Compute Engine equivalent | Explanation |
| :--- | :--- | :--- |
| **Linux server** (VirtualBox / UTM / WSL / Docker) | **Compute Engine VM** (`e2-medium`, Ubuntu) | Compute Engine provides an infrastructure-as-a-service Linux virtual machine running in Google Cloud data centers instead of on your local virtualization hardware. |
| **Your terminal / shell** | `gcloud compute ssh` | `gcloud compute ssh` provides an authenticated, secure SSH connection into your remote Cloud VM directly from your workstation terminal. |
| **localhost:5000 / VM IP** | **VM static external IP** | A GCP static external IP address provides a persistent public internet address for users to access your web application globally. |
| **OS firewall / open port** (`ufw allow 5000/tcp`) | **GCP VPC firewall rule** (`tcp:5000`) | GCP VPC firewall rules control network traffic at the virtual network border before packets reach your VM instance interface. |
| **Service manager** (`systemd` unit / Docker policy) | `systemd` on the VM | `systemd` runs on the Compute Engine Linux operating system to auto-start the Gunicorn application on boot and auto-restart it if it crashes. |
| **PostgreSQL on the environment** | **Cloud SQL** (managed PostgreSQL) | Cloud SQL replaces self-hosted PostgreSQL with a fully managed relational database that handles automated backups, patching, scaling, and high availability. |
| **`.env` / environment variables** | **Instance metadata / Secret Manager** | GCP Secret Manager and instance metadata securely store database connection credentials and secrets outside the codebase and inject them into running cloud workloads. |

---

## Architectural Transition Overview

```
LOCAL DEPLOYMENT:
User Workstation -> Local Bridge / Port 5000 -> UFW Firewall -> Linux VM (systemd) -> Gunicorn/Flask -> Local PostgreSQL

GOOGLE CLOUD PLATFORM (GCP):
Public Internet -> Static External IP -> GCP VPC Firewall (tcp:5000) -> Compute Engine VM (systemd) -> Gunicorn/Flask -> Cloud SQL (PostgreSQL)
```
