# 🚀 HeliX Coach — Deployment & Setup Checklist

This document lists everything you need to do to get HeliX Coach running in production. It is divided into **what the code already handles** and **what YOU must configure manually** in GCP/Firebase consoles.

---

## ✅ What's Already Done (Code Complete)

| Area | Status | Details |
|------|--------|---------|
| Backend — Agent framework | ✅ | 7 agents (orchestrator + 6 specialists) with Google ADK |
| Backend — Database tools | ✅ | 12 AlloyDB tools (CRUD for users, workouts, logs, readiness) |
| Backend — Firebase Auth verification | ✅ | `firebase_auth.py` verifies ID tokens |
| Backend — Per-user Calendar OAuth | ✅ | `auth.py` manages per-user refresh tokens |
| Backend — API routes | ✅ | `/api/auth/verify`, `/api/auth/calendar`, `/api/auth/callback`, `/api/auth/status`, `/api/health` |
| Backend — Secret Manager integration | ✅ | `database.py` fetches DB_PASS securely |
| Backend — Dockerfile | ✅ | Production-ready container definition |
| Frontend — Next.js + Tailwind | ✅ | Dark Vercel-style UI with file-based routing |
| Frontend — Firebase client auth | ✅ | Login page with Google Sign-In popup |
| Frontend — Chat Interface | ✅ | Connected to ADK backend via HTTP |
| Frontend — Dashboard widgets | ✅ | ReadinessGauge, WeeklyCalendar, ProgressChart |

---

## 🔧 What YOU Need to Do

### Step 1: Rotate the AlloyDB Password

> ⚠️ **CRITICAL**: The old password was committed to Git history and is compromised.

1. Go to [AlloyDB Console](https://console.cloud.google.com/alloydb/clusters) → Your cluster → Users
2. Change the password for the `postgres` user
3. Note the new password for Step 3 below

---

### Step 2: Set Up Firebase Authentication

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. **Create or select a project** linked to your GCP project (`helix-coach-app-252961914897`)
3. Enable **Authentication** → **Sign-in method** → **Google** → Enable
4. Go to **Project Settings** → **General** → scroll to "Your apps" → click **Add app** (Web)
5. Copy the config object and fill in `frontend/.env.local`:

```env
NEXT_PUBLIC_FIREBASE_API_KEY="AIza..."
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="your-project.firebaseapp.com"
NEXT_PUBLIC_FIREBASE_PROJECT_ID="your-project-id"
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET="your-project.appspot.com"
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID="123456789"
NEXT_PUBLIC_FIREBASE_APP_ID="1:123456789:web:abc123"
NEXT_PUBLIC_API_URL="http://localhost:8080"
```

---

### Step 3: Create a Secret in Google Secret Manager

1. Go to [Secret Manager](https://console.cloud.google.com/security/secret-manager)
2. Click **Create Secret**
3. Name: `alloydb-password`
4. Value: your new AlloyDB password from Step 1
5. Grant the Cloud Run service account the **Secret Manager Secret Accessor** role

---

### Step 4: Create Google OAuth Credentials for Calendar

1. Go to [APIs & Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `HeliX Calendar OAuth`
5. Authorized redirect URIs:
   - `http://localhost:8080/api/auth/callback` (local dev)
   - `https://<YOUR_CLOUD_RUN_URL>/api/auth/callback` (production)
6. Copy the **Client ID** and **Client Secret**

---

### Step 5: Deploy the Backend to Cloud Run

From the **project root** directory:

```bash
# Set environment variables for the deployment
gcloud run deploy helix-coach-backend \
  --source . \
  --region us-east4 \
  --allow-unauthenticated \
  --set-env-vars "DB_PASS=<your-new-password>" \
  --set-env-vars "GOOGLE_OAUTH_CLIENT_ID=<client-id-from-step-4>" \
  --set-env-vars "GOOGLE_OAUTH_CLIENT_SECRET=<client-secret-from-step-4>" \
  --set-env-vars "OAUTH_REDIRECT_URI=https://<YOUR_CLOUD_RUN_URL>/api/auth/callback" \
  --set-env-vars "FRONTEND_URL=https://<YOUR_VERCEL_URL>"
```

After deployment, note the Cloud Run URL (e.g., `https://helix-coach-backend-xxxxx.run.app`).

Go back to **Step 4** and add this URL + `/api/auth/callback` to authorized redirect URIs.

---

### Step 6: Deploy the Frontend to Vercel

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com) → **New Project** → Import your repo
3. Set **Root Directory** to `frontend`
4. Add environment variables:
   - All `NEXT_PUBLIC_FIREBASE_*` values from Step 2
   - `NEXT_PUBLIC_API_URL` = your Cloud Run URL from Step 5
5. Deploy

---

### Step 7: Clean Up the Database (Fresh Start)

Connect to your AlloyDB instance and drop the old tables:

```sql
-- Connect via Cloud Shell or psql
DROP TABLE IF EXISTS workouts;
DROP TABLE IF EXISTS users;
```

The new tables (`users`, `user_tokens`, `workout_routines`, `workout_logs`, `readiness_logs`) will be auto-created on the first backend boot.

---

### Step 8: Verify End-to-End

1. Open your Vercel deployment
2. Click **Log In** → Sign in with Google
3. You should be redirected to the Dashboard
4. Click **Connect Google Calendar** in the weekly calendar widget
5. Grant calendar permissions
6. Try a quick action in the chat: "What is my workout today?"

---

## 📁 Environment Variables Reference

### Backend (Cloud Run)

| Variable | Description |
|----------|-------------|
| `DB_PASS` | AlloyDB postgres password |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID (auto-set on Cloud Run) |
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth client ID for Calendar |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth client secret for Calendar |
| `OAUTH_REDIRECT_URI` | Full callback URL for Calendar OAuth |
| `FRONTEND_URL` | Your Vercel frontend URL (for CORS + redirects) |

### Frontend (Vercel / `.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase Web API Key |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase Auth Domain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase Project ID |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Firebase Storage Bucket |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase Sender ID |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Firebase App ID |
| `NEXT_PUBLIC_API_URL` | Backend Cloud Run URL |
