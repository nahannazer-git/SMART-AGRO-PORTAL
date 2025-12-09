# Deployment Guide for Render

> **📁 Note**: All deployment files are organized in the `deployment/` folder.  
> For Render to auto-detect `render.yaml`, copy it to project root (only if using Option 2).  
> **Recommended**: Use Option 1 (Manual setup) - no file copying needed!

## Prerequisites
- GitHub repository with your code
- Render account (logged in with same GitHub account)

## Step-by-Step Deployment

### Option 1: Using Render Dashboard (Recommended)

1. **Go to Render Dashboard**
   - Visit https://dashboard.render.com
   - Click "New +" button
   - Select "Web Service"

2. **Connect Repository**
   - Select "Build and deploy from a Git repository"
   - Connect your GitHub account if not already connected
   - Select your repository: `FARMERS PORTAL` (or your repo name)

3. **Configure Web Service**
   - **Name**: `farmers-portal` (or any name you prefer)
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty (root of repo)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`

4. **Add Environment Variables**
   Click "Advanced" and add:
   - `SECRET_KEY`: Generate a random secret key (you can use: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `PYTHON_VERSION`: `3.11.0`
   - `WEATHER_API_KEY`: (Optional) Your OpenWeatherMap API key if you have one

5. **Create PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - **Name**: `farmers-portal-db`
   - **Database**: `farmers_portal`
   - **User**: `farmers_portal_user`
   - **Plan**: Free (or paid if you need more)
   - Copy the **Internal Database URL**

6. **Link Database to Web Service**
   - Go back to your Web Service settings
   - Under "Environment Variables", add:
     - `DATABASE_URL`: Paste the Internal Database URL from step 5
   - **Important**: Use the **Internal Database URL** (not External) for better performance

7. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - Wait for build to complete (usually 2-5 minutes)

8. **Access Your App**
   - Once deployed, your app will be available at: `https://farmers-portal.onrender.com` (or your custom name)

### Option 2: Using render.yaml Blueprint (Alternative)

If you prefer using the `render.yaml` file for automated setup:

1. **Copy files to root** (Render needs them in root to auto-detect)
   ```bash
   # On Windows (PowerShell)
   Copy-Item deployment\render.yaml render.yaml
   Copy-Item deployment\.renderignore .renderignore
   
   # On Linux/Mac
   cp deployment/render.yaml render.yaml
   cp deployment/.renderignore .renderignore
   ```

2. **Push to GitHub**
   ```bash
   git add render.yaml .renderignore
   git commit -m "Add Render configuration files"
   git push origin main
   ```

3. **Create Blueprint**
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Select your repository
   - Render will automatically detect `render.yaml` in root
   - Review and apply the blueprint
   - This will create both the web service and database automatically

### Post-Deployment Steps

1. **Initialize Database**
   - Your app will automatically create tables on first run (via `db.create_all()` in `app/__init__.py`)
   - Or you can manually run migrations if needed

2. **Create Admin User** (Optional)
   - You may need to create an admin user manually
   - You can add a script or use the admin registration page

3. **Test Your Deployment**
   - Visit your app URL
   - Test login/registration
   - Verify database operations work

### Important Notes

- **Free Tier Limitations**:
  - Apps spin down after 15 minutes of inactivity
  - First request after spin-down takes ~30 seconds
  - Consider upgrading to paid plan for production

- **File Uploads**:
  - Uploaded files are stored in `/app/static/uploads/`
  - On Render, these are ephemeral (lost on redeploy)
  - Consider using cloud storage (AWS S3, Cloudinary) for production

- **Database**:
  - PostgreSQL is used in production
   - SQLite is used locally
   - The config automatically handles both

- **Environment Variables**:
   - Never commit secrets to GitHub
   - Always use Render's environment variables

### Troubleshooting

1. **Build Fails**:
   - Check build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`
   - Verify Python version compatibility

2. **Database Connection Issues**:
   - Ensure `DATABASE_URL` is set correctly
   - Use Internal Database URL (not External)
   - Check database is running

3. **App Crashes**:
   - Check logs in Render dashboard
   - Verify all environment variables are set
   - Ensure `SECRET_KEY` is set

4. **Static Files Not Loading**:
   - Check file paths in templates
   - Ensure `url_for('static', ...)` is used correctly

### Updating Your App

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Your update message"
   git push origin main
   ```

2. **Auto-Deploy**:
   - Render automatically detects changes
   - Triggers new build and deployment
   - Usually takes 2-5 minutes

### Custom Domain (Optional)

1. Go to your Web Service settings
2. Click "Custom Domains"
3. Add your domain
4. Follow DNS configuration instructions

---

**Need Help?**
- Render Docs: https://render.com/docs
- Render Support: support@render.com

