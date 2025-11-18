# AUPATOOL v0.1.2 - Installation Instructions (Linux & Mac)

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 4 cores (Intel i5 / AMD Ryzen 5 / Apple M1)
- RAM: 8 GB
- Disk: 100 GB free space (more for photos/archives)
- OS: macOS 12+ or Linux (Ubuntu 22.04+, Fedora 38+, Arch, etc.)

**Recommended:**
- CPU: 8+ cores
- RAM: 16 GB
- Disk: 500 GB+ SSD
- GPU: NVIDIA GPU with 8+ GB VRAM (for Immich ML acceleration)
- OS: macOS 14+ or Linux with kernel 5.15+

### Required Software

All platforms need:
1. Docker Engine 24+ and Docker Compose V2
2. Git 2.40+
3. Python 3.11+
4. Node.js 20+ LTS

Optional (for GPU acceleration):
5. NVIDIA CUDA 12+ (Linux only)
6. NVIDIA Container Toolkit

---

## Installation: macOS

### Step 1: Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Dependencies

```bash
# Docker Desktop (includes Docker Compose)
brew install --cask docker

# Start Docker Desktop
open /Applications/Docker.app

# Wait for Docker to start (whale icon in menu bar)

# Git
brew install git

# Python 3.11
brew install python@3.11

# Node.js 20 LTS
brew install node@20

# Verify installations
docker --version          # Should be 24.0+
docker compose version    # Should be v2.20+
git --version            # Should be 2.40+
python3 --version        # Should be 3.11+
node --version           # Should be 20.x
```

### Step 3: Clone AUPAT Repository

```bash
cd ~/Documents  # Or wherever you want the project
git clone https://github.com/bizzlechizzle/aupat.git
cd aupat
git checkout claude/aupatool-v0.1.2-setup-01H5db1Mfde6GUYrDnAekKgJ
```

### Step 4: Create Data Directories

```bash
mkdir -p data/{backups,documents,logs}
mkdir -p data/immich
mkdir -p data/archivebox
```

### Step 5: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env

# Set these variables:
AUPAT_DATA_DIR=/Users/$(whoami)/Documents/aupat/data
IMMICH_UPLOAD_LOCATION=/Users/$(whoami)/Documents/aupat/data/immich
ARCHIVEBOX_DATA_DIR=/Users/$(whoami)/Documents/aupat/data/archivebox

# For Mac M-series (Apple Silicon):
IMMICH_ML_DEVICE=cpu  # GPU acceleration not available on Mac

# Save and exit (Ctrl+O, Ctrl+X in nano)
```

### Step 6: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify
pytest --version
black --version
```

### Step 7: Start Docker Services

```bash
# Start all services
docker compose up -d

# Check status (all should be "healthy")
docker compose ps

# Expected output:
# NAME                STATUS          PORTS
# aupat-core          healthy         0.0.0.0:5000->5000/tcp
# immich-server       healthy         0.0.0.0:2283->2283/tcp
# immich-ml           healthy         0.0.0.0:3003->3003/tcp
# immich-postgres     healthy         5432/tcp
# immich-redis        healthy         6379/tcp
# archivebox          healthy         0.0.0.0:8001->8000/tcp

# View logs (Ctrl+C to exit)
docker compose logs -f
```

### Step 8: Initialize Database

```bash
# Run migrations
python scripts/db_migrate.py

# Import test data (optional)
python scripts/import_test_data.py

# Verify database
sqlite3 data/aupat.db "SELECT COUNT(*) FROM locations;"
```

### Step 9: Verify Services

```bash
# Test AUPAT Core API
curl http://localhost:5000/api/health
# Expected: {"status": "healthy", "version": "0.1.2"}

# Test Immich
curl http://localhost:2283/api/server-info/ping
# Expected: {"res": "pong"}

# Test ArchiveBox
curl http://localhost:8001/health
# Expected: {"status": "ok"}

# Open web interfaces
open http://localhost:2283  # Immich
open http://localhost:8001  # ArchiveBox
```

### Step 10: Build Desktop App (Optional for Development)

```bash
cd desktop-app

# Install dependencies
npm install

# Development mode
npm run dev
# App opens, auto-reloads on code changes

# Build production app
npm run build:mac
# Creates: desktop-app/dist/AUPAT-0.1.2-mac.dmg
```

### macOS Troubleshooting

**Docker not starting:**
- Check: System Preferences → Privacy & Security → Allow Docker
- Increase Docker resources: Docker Desktop → Preferences → Resources (8 GB RAM recommended)

**Permission denied errors:**
- Fix: `sudo chown -R $(whoami):staff data/`

**Port conflicts (5000, 2283, 8001 in use):**
- Check: `lsof -i :5000` (shows what's using port)
- Fix: Edit docker-compose.yml to use different ports, or kill conflicting process

**Immich ML slow:**
- Apple Silicon doesn't support CUDA
- Expect CPU-based ML (slower but works)
- Alternative: Disable ML in Immich settings, use manual tagging

---

## Installation: Linux (Ubuntu/Debian)

### Step 1: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Docker Engine

```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group (avoid sudo for docker commands)
sudo usermod -aG docker $USER
newgrp docker  # Activate group membership

# Verify
docker --version          # Should be 24.0+
docker compose version    # Should be v2.20+
```

### Step 3: Install NVIDIA Docker (GPU Support, Optional)

**Only if you have NVIDIA GPU and want ML acceleration:**

```bash
# Install NVIDIA drivers (if not installed)
sudo ubuntu-drivers autoinstall
sudo reboot  # Reboot required

# Verify GPU
nvidia-smi  # Should show GPU info

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker

# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
# Should show GPU info inside container
```

### Step 4: Install Git, Python, Node.js

```bash
# Git
sudo apt install -y git

# Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Node.js 20 LTS (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
git --version            # Should be 2.40+
python3.11 --version     # Should be 3.11+
node --version           # Should be 20.x
npm --version            # Should be 10.x
```

### Step 5: Clone AUPAT Repository

```bash
cd ~/Documents  # Or wherever you want the project
git clone https://github.com/bizzlechizzle/aupat.git
cd aupat
git checkout claude/aupatool-v0.1.2-setup-01H5db1Mfde6GUYrDnAekKgJ
```

### Step 6: Create Data Directories

```bash
mkdir -p data/{backups,documents,logs}
mkdir -p data/immich
mkdir -p data/archivebox

# Set permissions
chmod -R 755 data/
```

### Step 7: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env

# Set these variables:
AUPAT_DATA_DIR=/home/$(whoami)/Documents/aupat/data
IMMICH_UPLOAD_LOCATION=/home/$(whoami)/Documents/aupat/data/immich
ARCHIVEBOX_DATA_DIR=/home/$(whoami)/Documents/aupat/data/archivebox

# For GPU (if NVIDIA GPU available):
IMMICH_ML_DEVICE=cuda

# For CPU only (no GPU):
IMMICH_ML_DEVICE=cpu

# Save and exit (Ctrl+O, Enter, Ctrl+X in nano)
```

### Step 8: Install Python Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify
pytest --version
black --version
```

### Step 9: Start Docker Services

```bash
# If using GPU:
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# If using CPU only:
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f immich-ml  # Check ML service starts
```

### Step 10: Initialize Database

```bash
# Run migrations
python scripts/db_migrate.py

# Verify
sqlite3 data/aupat.db "PRAGMA integrity_check;"
# Expected: ok
```

### Step 11: Verify Services

```bash
# Test AUPAT Core API
curl http://localhost:5000/api/health

# Test Immich
curl http://localhost:2283/api/server-info/ping

# Test ArchiveBox
curl http://localhost:8001/health

# Open in browser
xdg-open http://localhost:2283  # Immich
xdg-open http://localhost:8001  # ArchiveBox
```

### Step 12: Build Desktop App

```bash
cd desktop-app

# Install dependencies
npm install

# Development mode
npm run dev

# Build production app
npm run build:linux
# Creates: desktop-app/dist/AUPAT-0.1.2.AppImage
```

### Linux Troubleshooting

**Docker permission denied:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**GPU not detected in Immich:**
```bash
# Check GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# If fails, check nvidia-container-toolkit installation
sudo systemctl restart docker
```

**Disk space issues:**
```bash
# Check disk usage
df -h

# Clean Docker images (frees space)
docker system prune -a
```

**Firewall blocking ports:**
```bash
# Allow ports (UFW firewall)
sudo ufw allow 5000/tcp
sudo ufw allow 2283/tcp
sudo ufw allow 8001/tcp
```

---

## Installation: Linux (Fedora/RHEL)

### Quick Install Script

```bash
# Install Docker
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Install Python, Node.js
sudo dnf install -y git python3.11 python3-pip nodejs npm

# Follow same steps as Ubuntu from Step 5 onward
```

---

## Installation: Linux (Arch Linux)

### Quick Install Script

```bash
# Install Docker
sudo pacman -S docker docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Install dependencies
sudo pacman -S git python nodejs npm

# Follow same steps as Ubuntu from Step 5 onward
```

---

## Post-Installation Setup

### Configure Immich

```bash
# Open Immich web UI
open http://localhost:2283  # Mac
xdg-open http://localhost:2283  # Linux

# First-time setup:
1. Create admin account (email: your@email.com, password: secure-password)
2. Go to Settings → Machine Learning
3. Enable: CLIP image tagging, facial recognition (optional)
4. Click "Run Missing Jobs" to process existing photos
```

### Configure ArchiveBox

```bash
# Open ArchiveBox web UI
open http://localhost:8001  # Mac
xdg-open http://localhost:8001  # Linux

# First-time setup:
1. Create superuser: docker compose exec archivebox archivebox manage createsuperuser
2. Login with credentials
3. Go to Settings → Archive Methods
4. Enable: WARC, screenshot, media extraction
5. Disable: PDF (slow), archive.org submission (unless desired)
```

### Set Up Automated Backups

```bash
# Create backup script
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR=data/backups

# Backup database
cp data/aupat.db $BACKUP_DIR/aupat_$DATE.db

# Git commit (version control)
git add data/aupat.db
git commit -m "Backup: $DATE"

# Backup with Restic (if configured)
if command -v restic &> /dev/null; then
    restic backup data/ --repo $BACKUP_DIR/restic-repo
fi

echo "Backup complete: $DATE"
EOF

chmod +x scripts/backup.sh

# Schedule daily backup (cron)
crontab -e

# Add line (runs daily at 2 AM):
0 2 * * * /home/$(whoami)/Documents/aupat/scripts/backup.sh >> /home/$(whoami)/Documents/aupat/data/logs/backup.log 2>&1
```

### Configure Cloudflare Tunnel (Remote Access)

```bash
# Install cloudflared
# Mac:
brew install cloudflare/cloudflare/cloudflared

# Linux (Debian/Ubuntu):
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Login to Cloudflare
cloudflared tunnel login
# Opens browser, select domain

# Create tunnel
cloudflared tunnel create aupat
# Note the tunnel ID

# Create config
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << EOF
tunnel: <TUNNEL_ID_FROM_ABOVE>
credentials-file: ~/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: aupat.yourdomain.com
    service: http://localhost:5000
  - hostname: photos.yourdomain.com
    service: http://localhost:2283
  - hostname: archive.yourdomain.com
    service: http://localhost:8001
  - service: http_status:404
EOF

# Route DNS
cloudflared tunnel route dns aupat aupat.yourdomain.com
cloudflared tunnel route dns aupat photos.yourdomain.com
cloudflared tunnel route dns aupat archive.yourdomain.com

# Run tunnel
cloudflared tunnel run aupat

# Install as service (runs on boot)
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Test
curl https://aupat.yourdomain.com/api/health
```

---

## Verification Checklist

After installation, verify:

- [ ] Docker services running: `docker compose ps` shows all healthy
- [ ] AUPAT Core API: `curl http://localhost:5000/api/health` returns 200
- [ ] Immich accessible: Open http://localhost:2283
- [ ] ArchiveBox accessible: Open http://localhost:8001
- [ ] Database exists: `ls data/aupat.db`
- [ ] Python environment: `source venv/bin/activate && python --version` shows 3.11+
- [ ] Import test: `python scripts/import_test_data.py` succeeds
- [ ] Desktop app (dev mode): `cd desktop-app && npm run dev` launches app
- [ ] Backup script: `./scripts/backup.sh` creates backup
- [ ] Cloudflare tunnel (if configured): `curl https://aupat.yourdomain.com/api/health` works

If all checks pass: Installation successful!

---

## Quick Start Commands

### Daily Usage

```bash
# Start AUPAT
cd ~/Documents/aupat
docker compose up -d

# Launch desktop app
cd desktop-app
npm run dev  # or run installed app

# View logs
docker compose logs -f

# Stop AUPAT
docker compose down
```

### Maintenance

```bash
# Backup
./scripts/backup.sh

# Update Docker images
docker compose pull
docker compose up -d

# View disk usage
du -sh data/

# Clean old Docker images
docker system prune -a
```

### Troubleshooting

```bash
# Restart all services
docker compose restart

# Rebuild AUPAT Core
docker compose up -d --build aupat-core

# Check database integrity
sqlite3 data/aupat.db "PRAGMA integrity_check;"

# View specific service logs
docker compose logs -f immich-server
```

---

## Uninstallation

```bash
# Stop all services
docker compose down

# Remove Docker volumes (WARNING: Deletes all data)
docker compose down -v

# Remove images
docker rmi $(docker images 'ghcr.io/immich-app/*' -q)
docker rmi $(docker images 'archivebox/*' -q)

# Remove project directory
cd ~
rm -rf ~/Documents/aupat

# Remove Docker (optional)
# Mac: Uninstall Docker Desktop app
# Linux: sudo apt remove docker-ce docker-ce-cli containerd.io
```

---

## Next Steps

1. Read: docs/v0.1.2/11_QUICK_REFERENCE.md (Common tasks)
2. Import your first photos: Use desktop app → Import
3. Explore: Browse map, view galleries
4. Archive: Test web archiving workflow
5. Customize: Edit settings in desktop app

For detailed usage, see user guide documentation.
