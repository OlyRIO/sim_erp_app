# Render.com Deployment Guide

## Prerequisites
- GitHub account connected to Render
- Repository: `OlyRIO/sim_erp_app`
- Branch: `main` (or `feature/initial_migration`)

## Deployment Steps

### Option 1: One-Click Deploy (Blueprint)

1. Push `render.yaml` to your repo
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click **"New +"** → **"Blueprint"**
4. Select your repository
5. Render auto-creates both database and web service
6. Wait 5-10 minutes for build and deployment

### Option 2: Manual Setup

#### Step 1: Create PostgreSQL Database
1. Render Dashboard → **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** `sim-erp-db`
   - **Database:** `sim_erp_db`
   - **User:** `sim_erp_user`
   - **Region:** Choose closest to you
   - **Plan:** Free
3. Click **"Create Database"**
4. Wait for provisioning (1-2 minutes)

#### Step 2: Create Web Service
1. Render Dashboard → **"New +"** → **"Web Service"**
2. Connect repository: `OlyRIO/sim_erp_app`
3. Configure:
   - **Name:** `sim-erp-app`
   - **Region:** Same as database
   - **Branch:** `main`
   - **Runtime:** Docker
   - **Plan:** Free
   - **Docker Command:** (leave empty, uses Dockerfile CMD)

#### Step 3: Set Environment Variables
In the web service **Environment** tab, add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Click **"Add from Database"** → Select `sim-erp-db` |
| `SEED_ON_START` | `false` |
| `FLASK_ENV` | `production` |

#### Step 4: Deploy
1. Click **"Create Web Service"**
2. Render will:
   - Clone your repo
   - Build Docker image
   - Run migrations (`alembic upgrade head`)
   - Start gunicorn server
3. First deploy takes 5-10 minutes

## Post-Deployment

### Check Logs
- Go to your web service → **Logs** tab
- Look for:
  ```
  INFO  [alembic.runtime.migration] Running upgrade  -> cbbf50c0b41e
  [INFO] Starting gunicorn 21.2.0
  [INFO] Listening at: http://0.0.0.0:10000
  ```

### Get Your URL
- Web service dashboard shows: `https://sim-erp-app.onrender.com`
- Test API: `https://sim-erp-app.onrender.com/api/v1/customers`

### Seed Database (Optional)
Run Flask CLI command via Render shell:

1. Web service → **Shell** tab
2. Run:
   ```bash
   flask seed --customers 100 --sims 200 --assignments 150 --reset
   ```

Or use SSH (if enabled):
```bash
render ssh sim-erp-app
flask seed --customers 1000 --sims 1000 --assignments 1000
```

## Configuration Details

### Auto-Migrations
The Dockerfile automatically runs `alembic upgrade head` on every deploy, so your schema stays up-to-date.

### Production Server
- **Gunicorn** with 2 workers, 4 threads per worker
- Handles concurrent requests efficiently
- 60-second timeout for long queries

### Free Tier Limitations
- Web service spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- 750 hours/month free compute
- Database: 1GB storage, 97 connection limit

### Port Configuration
- Render provides `PORT` environment variable (default 10000)
- Dockerfile uses `${PORT:-10000}` to read it dynamically
- Local development still works on port 8000

## Updating Your Deployment

### Push Changes
```powershell
git add .
git commit -m "Update feature"
git push origin main
```

Render auto-deploys on every push to `main` (or your configured branch).

### Manual Deploy
Web service → **Manual Deploy** → Select branch/commit

### Rollback
Web service → **Events** tab → Click **"Rollback"** on previous deploy

## Troubleshooting

### Build Fails
- Check **Logs** for Python/Docker errors
- Verify `requirements.txt` is valid
- Ensure `Dockerfile` syntax is correct

### Database Connection Error
- Verify `DATABASE_URL` is set correctly
- Check database is in the same region
- Database must be "Available" status

### Migrations Fail
- Check migration files in `migrations/versions/`
- Run shell: `alembic current` to see current revision
- Manually run: `alembic upgrade head`

### App Crashes
- Check logs for Python exceptions
- Verify all environment variables are set
- Test locally with same `DATABASE_URL` format

## Monitoring

### Health Checks
Render pings `/` every few minutes. If it fails 3 times, service restarts.

### Logs
- Real-time: Web service → **Logs** tab
- Download: **Download logs** button

### Metrics
- Web service → **Metrics** tab shows:
  - CPU usage
  - Memory usage
  - Request count
  - Response times

## Security Notes

- Database password is auto-generated and secure
- Connections use SSL by default
- Environment variables are encrypted
- Only accessible via your deployed URL

## Cost Estimate

**Free Tier:**
- PostgreSQL: Free (1GB, no credit card needed)
- Web Service: Free (750 hours/month, sleeps after inactivity)

**Paid Upgrade Options:**
- Web Service (always-on): $7/month
- PostgreSQL (10GB): $7/month
- Total: ~$14/month for production-ready setup

## Next Steps

1. Push deployment changes:
   ```powershell
   git add Dockerfile requirements.txt render.yaml DEPLOYMENT.md
   git commit -m "Configure for Render deployment"
   git push origin main
   ```

2. Deploy via Render dashboard
3. Test API endpoints
4. Seed database
5. Update `API.md` with production URL
6. Integrate with chatbot

Ready to deploy! 🚀
