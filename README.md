# NormCode 规范码 - Coming Soon Website

**Psylens.AI 心镜智**

让专属逻辑驱动AI

A clean, minimalist "coming soon" page for NormCode / 规范码 by Psylens.AI.

## Features

- ✨ Clean, minimalist white background design
- 📐 Single-page layout - no scrolling required
- 📱 Fully responsive (mobile-friendly)
- ⚡ Fast and lightweight
- 🔗 Direct link to GitHub repository
- 🚀 No build process required - just open `index.html` in a browser

## Quick Start

Simply open `index.html` in any web browser. No installation or build process needed!

### Local Development

If you want to run it with a local server:

**Using Python:**
```bash
# Python 3
python -m http.server 8000

# Then open http://localhost:8000
```

**Using Node.js:**
```bash
npx serve .

# Follow the URL shown in terminal
```

## Customization

To customize the website:

1. **GitHub Link**: Currently set to https://github.com/GEOGUANSIN/normCode
2. **Colors**: Modify colors in the `<style>` section
3. **Update Text**: Edit the content in the HTML body section
4. **Logo**: Currently using `psylens_logo_caption.png` (includes company name)

## Deploy

### GitHub Pages (Automatic)

This website is automatically deployed to GitHub Pages when you push to the `main` branch. The deployment workflow is configured in `.github/workflows/deploy-website.yml`.

After pushing to `main`, your site will be available at:
`https://<username>.github.io/<repository-name>/`

### Manual Deployment

This is a static website that can also be deployed to:

- Netlify
- Vercel
- Any static hosting service

Just upload the HTML file and assets (images)!

## Notes

This is a simplified, single-page version designed to fit entirely within the viewport without scrolling. The full website (in the `../website` directory) is built with React + TypeScript + Vite and includes more features.

