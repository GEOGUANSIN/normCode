# GitHub Pages Deployment Guide

## ✅ Setup Complete!

The simplified NormCode website is now configured to automatically deploy to GitHub Pages.

## How It Works

1. **Automatic Deployment**: When you push changes to the `main` branch, GitHub Actions will automatically deploy the website from the `website_temp` directory.

2. **Workflow Location**: `.github/workflows/deploy-website.yml`

3. **Published Site**: After deployment, your site will be available at:
   - `https://<your-github-username>.github.io/normCode/`
   - Or your custom domain if configured

## Files Deployed

The following files from `website_temp` will be deployed:
- `index.html` - Main website page
- `psylens_logo_caption.png` - Logo with caption
- `Psylensai_log_raw.png` - Favicon
- `.nojekyll` - Ensures GitHub Pages serves files correctly

Files **NOT** deployed (development only):
- `launch_dev.py`, `launch.bat`, `launch.ps1` - Local dev server scripts
- `README.md`, `DEPLOYMENT.md` - Documentation
- Other image assets not referenced in the HTML

## First Time Setup

### Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** > **Pages**
3. Under "Source", select:
   - **Deploy from a branch**
   - Branch: `gh-pages`
   - Folder: `/ (root)`
4. Click **Save**

### Trigger First Deployment

Option 1: Push to main branch
```powershell
git add .
git commit -m "Deploy simplified website to GitHub Pages"
git push origin main
```

Option 2: Manual trigger
1. Go to **Actions** tab in your GitHub repository
2. Click on "Deploy Simplified Website to GitHub Pages"
3. Click **Run workflow** > **Run workflow**

## Monitoring Deployment

1. Go to the **Actions** tab in your GitHub repository
2. You'll see the deployment workflow running
3. Once complete (green checkmark ✓), your site is live!
4. Click on the workflow run to see detailed logs

## Making Changes

1. Edit files in `website_temp/` locally
2. Test locally by opening `index.html` in your browser
3. Commit and push to `main` branch:
   ```powershell
   git add website_temp/
   git commit -m "Update website content"
   git push origin main
   ```
4. GitHub Actions will automatically redeploy (takes ~1-2 minutes)

## Troubleshooting

### Site not loading?
- Wait a few minutes after deployment completes
- Check if GitHub Pages is enabled in repository settings
- Verify the `gh-pages` branch exists and has content

### Images not showing?
- Ensure image files are committed to the repository
- Check file paths in `index.html` are correct
- Verify images are in `website_temp/` directory

### Need to rollback?
1. Go to the commit you want to restore
2. Revert or create a new commit with old content
3. Push to `main` branch

## Custom Domain (Optional)

To use a custom domain:
1. Add a `CNAME` file to `website_temp/` with your domain
2. Configure DNS with your domain provider
3. Update repository settings > Pages > Custom domain

## Support

- GitHub Pages Documentation: https://docs.github.com/pages
- GitHub Actions Documentation: https://docs.github.com/actions

