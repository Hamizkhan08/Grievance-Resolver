# Quick Fix for "Failed to fetch" Login Error

## The Problem
The `.env` file is missing, so Supabase credentials are not configured.

## Quick Fix (2 minutes)

### Step 1: Create .env file
```bash
cd dev/frontend
cp .env.example .env
```

### Step 2: Get Supabase Credentials
1. Go to https://app.supabase.com
2. Select your project (or create one if you don't have one)
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → `VITE_SUPABASE_URL`
   - **anon/public** key → `VITE_SUPABASE_ANON_KEY`

### Step 3: Edit .env file
Open `.env` and replace the placeholders:
```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_URL=http://localhost:8000
```

### Step 4: Create Admin User
1. In Supabase Dashboard, go to **Authentication** → **Users**
2. Click **Add User**
3. Enter:
   - Email: `resolvergrievance@gmail.com`
   - Password: `123456789`
   - **Auto Confirm User**: ✅ Yes
4. Click **Create User**

### Step 5: Restart Dev Server
```bash
# Stop current server (Ctrl+C)
npm run dev
```

### Step 6: Try Login Again
- Email: `resolvergrievance@gmail.com`
- Password: `123456789`

## Still Not Working?

Check browser console (F12) for errors and see `LOGIN_TROUBLESHOOTING.md` for detailed help.
