# Quick Start: Creating Entur SX Brand PNGs

## Automated Method (Recommended)

From the `brands/entur_sx` folder, run:

```powershell
.\resize_png.ps1
```

**Requirements**: ImageMagick must be installed  
Download from: https://imagemagick.org/script/download.php

## Manual with ImageMagick

```powershell
cd brands\entur_sx

# Create icon (256x256)
magick EN-app-logo-512x512.png -resize 256x256 icon.png
Copy-Item icon.png dark_icon.png

# Create logo (256x128 with centered 128x128 logo)
magick EN-app-logo-512x512.png -resize 128x128 -background none -gravity center -extent 256x128 logo.png
Copy-Item logo.png dark_logo.png
```

## Online Resize (No Installation Required)

1. Go to https://www.resizepixel.com/
2. Upload `EN-app-logo-512x512.png`
3. Resize to 256x256 → Save as `icon.png`
4. Copy `icon.png` → `dark_icon.png`
5. For logo: Resize to 128x128, add transparent borders to 256x128 (centered)
6. Copy `logo.png` → `dark_logo.png`

## Submission to Home Assistant

1. Fork: https://github.com/home-assistant/brands
2. Create: `brands/custom_integrations/entur_sx/`
3. Copy PNG files to that folder
4. Create PR with title: "Add Entur SX integration logos"

## File Checklist

- [ ] icon.png (256x256px)
- [ ] dark_icon.png (256x256px)
- [ ] logo.png (256x128px, optional)
- [ ] dark_logo.png (256x128px, optional)
- [ ] All files under 10KB
- [ ] Transparent backgrounds maintained

For detailed instructions, see [README.md](README.md)
