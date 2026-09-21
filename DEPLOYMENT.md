# DeepTrace AI - Production Deployment Guide

DeepTrace AI is designed for containerized or bare-metal production deployments.

---

## 1. Docker Compose Deployment (Recommended)

The provided `docker-compose.yml` orchestrates:
1. `postgres`: PostgreSQL 16 relational database with persistent volume.
2. `redis`: Redis 7 in-memory message broker.
3. `backend`: FastAPI API service running on port 8000.
4. `worker`: Celery asynchronous worker executing heavy AI inference.
5. `frontend`: Next.js production server running on port 3000.

### Deployment Steps:

```bash
# 1. Clone repository and navigate to root
cd deeptrace-ai

# 2. Copy and configure production environment variables
cp .env.example .env

# Edit .env and set secure SECRET_KEY, PostgreSQL passwords, and ENVIRONMENT=production
nano .env

# 3. Build and start all services
docker compose up -d --build

# 4. Monitor service logs
docker compose logs -f backend worker
```

---

## 2. Bare-Metal Linux / Cloud VM Deployment

### System Requirements:
* OS: Ubuntu 22.04 LTS or Debian 12
* CPU: 4+ Cores (8+ recommended for high-throughput video sampling)
* RAM: 16 GB minimum
* GPU: Optional NVIDIA GPU with CUDA 12+ for accelerated ViT inference
* Storage: NVMe SSD with sufficient capacity for evidence preservation

### Step-by-Step Setup:

```bash
# 1. Install System Dependencies
sudo apt update && sudo apt install -y python3-pip python3-venv ffmpeg postgresql redis-server nodejs npm

# 2. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Initialize Checkpoints & Database
python scripts/setup_models.py
python -m backend.app.db.init_db

# 4. Start Celery Worker (using systemd or supervisor)
celery -A backend.app.workers.celery_app worker --loglevel=info --concurrency=2

# 5. Start Backend API with Uvicorn / Gunicorn
gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# 6. Build and Start Next.js Frontend
cd frontend
npm install
npm run build
npm run start -- -p 3000
```

---

## 3. Health Monitoring & Audits
* Backend Health Check: `GET /health`
* Model Status & Diagnostics: `GET /api/models/status`
* Dashboard Metrics: `GET /api/dashboard/stats`
