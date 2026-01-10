# Fix "Invalid email or password" Error

## Your Setup Status ✅
- ✅ `.env` file exists and is configured
- ✅ Supabase URL and Anon Key are set
- ❌ User may not exist in Supabase Auth

## Quick Fix Steps

### Step 1: Verify User Exists in Supabase

1. **Go to Supabase Dashboard:**
   - Visit: https://app.supabase.com
   - Select your project: `qrkzdaviyehvsingqtjy`

2. **Check Authentication > Users:**
   - Navigate to **Authentication** → **Users**
   - Look for `resolvergrievance@gmail.com`
   - Check if user status is **"Confirmed"** (green checkmark)

### Step 2: Create User (If Missing)

If the user doesn't exist:

1. **Click "Add User"** or **"Invite User"**
2. **Fill in the form:**
   - **Email**: `resolvergrievance@gmail.com`
   - **Password**: `123456789`
   - **Auto Confirm User**: ✅ **Yes** (IMPORTANT!)
   - **Send Invite Email**: ❌ No (not needed if auto-confirmed)
3. **Click "Create User"**

### Step 3: Confirm User (If Not Confirmed)

If user exists but shows "Unconfirmed":

1. **Click on the user** in the list
2. **Click "Confirm"** button
3. **Or delete and recreate** with "Auto Confirm" enabled

### Step 4: Verify Email Authentication is Enabled

1. Go to **Authentication** → **Providers**
2. Find **"Email"** provider
3. Ensure it's **enabled** (toggle should be ON)

### Step 5: Restart Dev Server

After creating/confirming the user:

```bash
cd dev/frontend
# Stop current server (Ctrl+C if running)
npm run dev
```

### Step 6: Try Login Again

- **Email**: `resolvergrievance@gmail.com`
- **Password**: `123456789`

## Still Not Working?

### Check Browser Console
1. Open DevTools (F12)
2. Go to **Console** tab
3. Look for errors when logging in
4. Check **Network** tab for failed requests

### Common Issues

**"User not found"**
- User doesn't exist → Create user (Step 2)

**"Email not confirmed"**
- User exists but not confirmed → Confirm user (Step 3)

**"Invalid login credentials"**
- Wrong password → Reset password in Supabase Dashboard
- Or delete and recreate user with correct password

**"Failed to fetch"**
- Check internet connection
- Verify Supabase project is active (not paused)
- Check browser console for CORS errors

### Reset Password (If Needed)

1. In Supabase Dashboard → **Authentication** → **Users**
2. Click on `resolvergrievance@gmail.com`
3. Click **"Reset Password"** or **"Update Password"**
4. Set password to: `123456789`
5. Save changes

### Delete and Recreate User

If nothing works:

1. In Supabase Dashboard → **Authentication** → **Users**
2. Find `resolvergrievance@gmail.com`
3. Click **"Delete"** (trash icon)
4. Create new user following **Step 2** above

## Verification Checklist

- [ ] User exists in Supabase Auth
- [ ] User status is "Confirmed"
- [ ] Email authentication provider is enabled
- [ ] Password is exactly `123456789`
- [ ] `.env` file has correct Supabase credentials
- [ ] Dev server restarted after changes
- [ ] Browser cache cleared (Ctrl+Shift+R or Cmd+Shift+R)

## Need More Help?

See `LOGIN_TROUBLESHOOTING.md` for detailed troubleshooting steps.
