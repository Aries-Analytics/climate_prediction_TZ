# Server Deployment Guide for Shadow Run

> **Purpose**: Step-by-step instructions to take the Tanzania Climate Prediction pipeline from a local laptop to an always-on remote server for the 90-day shadow run.
> **Date**: March 5, 2026

To achieve the 90-day unbroken chain of evidence required by reinsurers, the pipeline must run on an always-on server. If it runs locally, a closed laptop at 6:00 AM EAT means a permanently missed forecast day (due to `misfire_grace_time=1` and the in-memory job store).

Here is the exact process to securely deploy the Dockerized environment to a remote Linux server (e.g., Ubuntu 22.04 LTS on AWS EC2, DigitalOcean Droplet, or similar).

---

## Prerequisites

1. **A Linux Server**: Minimum 4GB RAM, 2 vCPUs, 20GB disk (to handle Postgres, the ML models, the API, the React dashboard, the scheduler, and the monitor).
2. **SSH Access**: You must be able to SSH into this server.
3. **Repository Clone**: The server needs access to your `phase2/feature-expansion` branch.

---

## Step 1: Server Preparation

SSH into your remote server and install the fundamental requirements: Docker and Git.

```bash
# Update packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Git
sudo apt-get install git -y

# Install Docker & Docker Compose
sudo apt-get install docker.io docker-compose -y

# Add your user to the docker group (so you don't need sudo for every docker command)
sudo usermod -aG docker $USER
```
*(You may need to log out and log back in for the Docker group changes to take effect).*

---

## Step 2: Clone the Project

Pull the codebase down to the server. 

```bash
git clone <YOUR_GIT_REPOSITORY_URL>
cd capstone-project-lordwalt/phase2
git checkout phase2/feature-expansion
```

---

## Step 3: Secure the API Credentials

Our pipeline relies on two critical credential files that **should not** be committed to Git:
1. Google Earth Engine credentials (`~/.config/earthengine/credentials`) for CHIRPS and NDVI.
2. The `.env` file containing the Slack Webhook and ERA5 API Key.

**A. Transfer Earth Engine Credentials:**
From your local laptop (Windows), securely copy the Earth Engine token to the server:
```bash
# On your local Windows machine (powershell or WSL):
scp ~/.config/earthengine/credentials user@remote_server_ip:~/.config/earthengine/credentials
```
*(Alternatively, you can just `cat` the file locally, then create and paste it into `~/.config/earthengine/credentials` on the server).*

**B. Create the Environment File:**
On the remote server, create the `.env` file required by the backend and scheduler:
```bash
nano .env
```
Paste in your actual keys:
```env
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ERA5_API_KEY=your_actual_ecmwf_token_here
```

---

## Step 4: Configure the 6 AM Shadow Run Schedule

Before we start the containers, we must switch the scheduler from the 30-minute testing interval to the daily 6 AM EAT (03:00 UTC) shadow run schedule.

Open `docker-compose.dev.yml` on the server:
```bash
nano docker-compose.dev.yml
```

Find the `pipeline-scheduler` service block and change `PIPELINE_SCHEDULE`:
```yaml
      - PIPELINE_SCHEDULE=0 6 * * *   # Changed from */30 * * * *
```
*(Note: Because `PIPELINE_TIMEZONE` is explicitly set to `Africa/Dar_es_Salaam` in the compose file, writing `0 6 * * *` accurately maps to 6 AM EAT).*

---

## Step 5: Launch the Shadow Run Environment

Now we bring up the entire stack using Docker Compose in detached mode (`-d`), so it keeps running even after you close your SSH terminal.

```bash
# Build the images (this takes a few minutes)
docker-compose -f docker-compose.dev.yml build

# Start the services in detached mode
docker-compose -f docker-compose.dev.yml up -d
```

Verify everything is running perfectly:
```bash
docker-compose -f docker-compose.dev.yml ps
```
You should see all 5 containers (`db`, `backend`, `frontend`, `pipeline-scheduler`, and `pipeline-monitor`) with an "Up" status.

---

## Step 6: Monitor the System

The system is now completely autonomous. You can safely close your laptop.

- **At 6:00 AM EAT every day:** The `pipeline-scheduler` will wake up, run the ingestion, select the active model (`xgboost_climate.pkl`, 83 features), and generate the 12 Evidence Pack forecasts.
- **At 6:30 AM EAT:** Your phone will receive the enriched `#climate-pipeline-daily` Slack notification.
- **To view the Evidence Pack Dashboard:** Open a web browser to `http://<YOUR_SERVER_IP>:3000` (ensure port 3000 is open in your server's firewall/security group).

If you ever need to manually check logs on the server:
```bash
# View the scheduler logs
docker logs climate_pipeline_scheduler_dev -f --tail 100
```
