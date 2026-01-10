# Quick Fix for White Screen

If you're seeing a white screen, it's likely because Supabase environment variables are missing.

## Quick Fix

1. **Create `.env` file in `dev/frontend/` directory:**

```bash
cd dev/frontend
touch .env
```

2. **Add these lines to `.env`:**

```env
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

3. **Get your Supabase credentials:**
   - Go to https://app.supabase.com
   - Select your project
   - Go to **Settings** > **API**
   - Copy **Project URL** → `VITE_SUPABASE_URL`
   - Copy **anon/public** key → `VITE_SUPABASE_ANON_KEY`

4. **Restart the dev server:**
   ```bash
   # Stop the server (Ctrl+C)
   npm run dev
   ```

## If You Don't Have Supabase Yet

The app should still work without Supabase configured (authentication will be disabled), but if you see a white screen:

1. **Check browser console** (F12) for errors
2. **Check terminal** for build errors
3. **Try clearing browser cache** and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

## Common Issues

### "Cannot read property of undefined"
- Make sure `.env` file exists
- Restart dev server after creating `.env`

### "Supabase client error"
- Check that URLs and keys are correct
- Make sure there are no extra spaces in `.env` file

### Still white screen?
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab to see if files are loading
