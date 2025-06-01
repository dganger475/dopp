# Deployment Guide

## Overview
This guide will help you deploy the Doppleganger Social Network using a cost-effective stack that can be free or very low cost.

## Stack Components

### Frontend (Vercel - Free)
1. Create a Vercel account at https://vercel.com
2. Install Vercel CLI: `npm i -g vercel`
3. In the frontend directory:
   ```bash
   vercel login
   vercel
   ```
4. Configure environment variables in Vercel dashboard:
   - `REACT_APP_API_BASE_URL`: Your backend URL

### Backend (Render - Free)
1. Create a Render account at https://render.com
2. Create a new Web Service
3. Connect your GitHub repository
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Add environment variables in Render dashboard (from .env)

### Database (Supabase - Free)
1. Create a Supabase account at https://supabase.com
2. Create a new project
3. Get the connection string from Settings > Database
4. Update your .env with the DATABASE_URL
5. Run migrations:
   ```bash
   flask db upgrade
   ```

### Image Storage (Cloudinary - Free)
1. Create a Cloudinary account at https://cloudinary.com
2. Get your credentials from the dashboard
3. Update your .env with Cloudinary credentials
4. Install the Cloudinary package:
   ```bash
   pip install cloudinary
   ```

## Required Changes

### 1. Update Database Configuration
Replace SQLite with PostgreSQL:
```python
# config.py
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
```

### 2. Update Image Storage
Replace local storage with Cloudinary:
```python
# services/image_service.py
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def upload_image(file):
    result = cloudinary.uploader.upload(file)
    return result['secure_url']
```

### 3. Update Frontend Configuration
```javascript
// frontend/src/config/api.js
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';
```

## Deployment Steps

1. **Prepare the Codebase**
   - Remove any hardcoded credentials
   - Update all file paths to use environment variables
   - Test locally with the new configuration

2. **Set Up Version Control**
   - Ensure .gitignore includes:
     ```
     .env
     __pycache__/
     *.pyc
     venv/
     ```

3. **Deploy Backend**
   - Push to GitHub
   - Connect to Render
   - Set environment variables
   - Deploy

4. **Deploy Frontend**
   - Push to GitHub
   - Connect to Vercel
   - Set environment variables
   - Deploy

5. **Set Up Database**
   - Create Supabase project
   - Run migrations
   - Import initial data if needed

6. **Configure Image Storage**
   - Set up Cloudinary
   - Test image uploads
   - Update existing image paths

## Monitoring and Maintenance

1. **Set Up Logging**
   - Use Render's built-in logging
   - Set up error tracking (e.g., Sentry)

2. **Performance Monitoring**
   - Use Vercel Analytics
   - Monitor database performance in Supabase

3. **Backup Strategy**
   - Regular database backups in Supabase
   - Image backups in Cloudinary

## Scaling Considerations

1. **Database**
   - Supabase free tier can handle up to 500MB
   - Plan for upgrade when approaching limits

2. **Image Storage**
   - Cloudinary free tier: 25GB
   - Consider compression for large images

3. **Backend**
   - Render free tier: 750 hours/month
   - Monitor usage and plan for upgrade

4. **Frontend**
   - Vercel free tier is generous
   - Monitor bandwidth usage

## Security Considerations

1. **Environment Variables**
   - Never commit .env files
   - Use secure secrets management

2. **CORS**
   - Configure properly for production domains
   - Use secure headers

3. **Authentication**
   - Use secure session management
   - Implement rate limiting

## Cost Management

The free tier stack should be sufficient for initial deployment:
- Vercel: Free
- Render: Free
- Supabase: Free
- Cloudinary: Free

Monitor usage and upgrade only when necessary.

## Support and Resources

- Vercel Documentation: https://vercel.com/docs
- Render Documentation: https://render.com/docs
- Supabase Documentation: https://supabase.com/docs
- Cloudinary Documentation: https://cloudinary.com/documentation 