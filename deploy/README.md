# Deploy — zeroFIR

Operator quick reference. Fresh install below; day-to-day is `update.sh`.

## Layout

```
/opt/zerofir-src/    # git checkout (or /opt/scrb/zeroFIR/ if bundled)
/opt/zerofir/        # runtime
  backend/           # synced from src by update.sh
  frontend/dist/     # built SPA
  backups/
  uploads/
```

## First-time install (once per server)

zeroFIR coexists with CyberFraud on the same Ubuntu 24.04 host. Reuses
system deps (mysql, python3.12, nginx, nodejs) already installed for
CyberFraud.

```bash
# 1. Create the zerofir OS user
sudo useradd -r -m -s /bin/bash -d /opt/zerofir zerofir

# 2. Clone source (adjust path if bundled inside a monorepo)
sudo mkdir -p /opt/zerofir-src
sudo chown zerofir:zerofir /opt/zerofir-src
sudo -u zerofir git clone https://github.com/rajibdassharma/zeroFIR.git /opt/zerofir-src

# 3. Runtime tree
sudo mkdir -p /opt/zerofir/backend /opt/zerofir/uploads /opt/zerofir/backups
sudo cp -r /opt/zerofir-src/backend/* /opt/zerofir/backend/
sudo -u zerofir python3.12 -m venv /opt/zerofir/backend/venv
sudo -u zerofir /opt/zerofir/backend/venv/bin/pip install -r /opt/zerofir/backend/requirements.txt
sudo chown -R zerofir:zerofir /opt/zerofir

# 4. Create .env — set ZFIR_JWT_SECRET or backend refuses to boot
sudo cp /opt/zerofir-src/.env.example /opt/zerofir/backend/.env
sudo bash /opt/zerofir-src/deploy/rotate-jwt-secret.sh
# ... then edit .env for DB credentials, CORS_ORIGINS, and DISABLE_DOCS=true

# 5. Seed the DB + bootstrap super_admin (Phase 0)
sudo -u zerofir bash -c "cd /opt/zerofir/backend && venv/bin/python seed.py --fresh"
# Capture the credentials CSV from stdout, then delete it.

# 6. Install systemd unit for the backend
sudo cp /opt/zerofir-src/deploy/zerofir-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now zerofir-backend

# 7. Install nightly backup
sudo bash /opt/zerofir-src/deploy/install-backup.sh

# 8. Nginx (extends existing CyberFraud config with a second server block)
sudo cp /opt/zerofir-src/deploy/nginx.conf /etc/nginx/sites-available/zerofir
sudo ln -s /etc/nginx/sites-available/zerofir /etc/nginx/sites-enabled/zerofir
sudo nginx -t
sudo systemctl reload nginx

# 9. SSL cert
sudo certbot --nginx -d zerofir.ksp.gov.in
```

## Day-to-day: update.sh

Every code change deploys with:

```bash
cd /opt/zerofir-src && git pull && sudo bash deploy/update.sh
```

Idempotent, self-verifying.

## JWT secret rotation

```bash
sudo bash /opt/zerofir-src/deploy/rotate-jwt-secret.sh
```

Invalidates all existing sessions. Users re-login on next request.

## Coexistence with CyberFraud

Both services run on the same host on distinct ports (CyberFraud
8000, zeroFIR 8002), distinct MySQL DBs (`cyber_fraud_dsr`,
`zerofir`), distinct OS users (`cyberfraud`, `zerofir`), distinct
systemd unit names. Backups are scheduled 15 min apart
(CyberFraud 02:00, zeroFIR 02:15) so they don't collide on the DB.
