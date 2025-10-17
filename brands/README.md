# Entur SX Brand Assets for Home Assistant

This folder contains the brand assets for the Entur Situation Exchange integration, prepared according to [Home Assistant Brands Guidelines](https://github.com/home-assistant/brands).

## Source File

- `EN-app-logo-512x512.png` - Official Entur app logo (512x512) - **DO NOT MODIFY**

## PNG Files to Generate

Run `resize_png.ps1` to create:
- `icon.png` - Square icon (256x256)
- `dark_icon.png` - Square icon (256x256) - identical to icon.png for Entur
- `logo.png` - Horizontal logo (256x128, centered)
- `dark_logo.png` - Horizontal logo (256x128, centered) - identical to logo.png for Entur

**Note**: Entur uses the same logo design for both light and dark modes.

## Design Attribution

This integration uses Entur's official app logo design. All Entur branding, colors, and visual elements are © Entur AS and used according to their brand guidelines:

- **Primary Source**: https://linje.entur.no/identitet/verktoykassen/logo
- **Original App Icon**: https://cdn.sanity.io/images/npa0lfls/production/340d04b37ddf6287ab9dd9fedf383bb0d128a491-192x192.png

### Entur Brand Colors

**Light Mode:**
- Background: #181c56 (Entur Blue)
- Text: #ffffff (White)
- Underline: #e5605e (Entur Coral/Red)

**Dark Mode:**
- Background: #2c3354 (Lighter Blue)
- Text: #ffffff (White)
- Underline: #ff7875 (Brighter Coral)

## Creating PNG Files for Submission

The Home Assistant brands repository requires PNG files at specific dimensions. We resize from the official Entur app logo.

### Automated Method (Recommended)

Run the PowerShell script from the `entur_sx` folder:

```powershell
cd brands\entur_sx
.\resize_png.ps1
```

This requires **ImageMagick** to be installed. Download from: https://imagemagick.org/script/download.php

### Manual Method with ImageMagick

```powershell
# Icon (256x256) - direct resize
magick EN-app-logo-512x512.png -resize 256x256 icon.png

# Dark icon (256x256) - same as light for Entur
Copy-Item icon.png dark_icon.png

# Logo (256x128) - resize to 128x128 and center on 256x128 canvas
magick EN-app-logo-512x512.png -resize 128x128 -background none -gravity center -extent 256x128 logo.png

# Dark logo (256x128) - same as light for Entur
Copy-Item logo.png dark_logo.png
```

### Manual Method with Online Tools

1. Go to https://www.resizepixel.com/ or https://www.iloveimg.com/resize-image
2. Upload `EN-app-logo-512x512.png`
3. Resize to:
   - **icon.png**: 256x256px
   - **logo.png**: First resize to 128x128, then add transparent borders to make 256x128 with logo centered
4. Copy icon.png → dark_icon.png
5. Copy logo.png → dark_logo.png

## Optimizing PNGs

After resizing, optimize the PNG files to reduce file size:

**Using ImageMagick (recommended):**
```powershell
magick mogrify -strip -define png:compression-level=9 icon.png dark_icon.png logo.png dark_logo.png
```

**Using optipng:**
```bash
optipng -o7 icon.png dark_icon.png logo.png dark_logo.png
```

**Using pngquant:**
```bash
pngquant --quality=85-95 --ext .png --force icon.png dark_icon.png logo.png dark_logo.png
```

## Submitting to Home Assistant Brands

1. **Fork the repository**: https://github.com/home-assistant/brands

2. **Create the folder structure**:
   ```
   brands/
   └── custom_integrations/
       └── entur_sx/
           ├── icon.png (required)
           ├── dark_icon.png (optional, for dark mode)
           ├── logo.png (optional)
           └── dark_logo.png (optional, for dark mode)
   ```

3. **Copy your PNG files** to the appropriate folder

4. **Verify requirements**:
   - ✅ `icon.png` is 256x256px with transparent background
   - ✅ `dark_icon.png` is 256x256px with transparent background (if included)
   - ✅ `logo.png` is 256x128px with transparent background (if included)
   - ✅ `dark_logo.png` is 256x128px with transparent background (if included)
   - ✅ All PNGs are optimized (preferably under 10KB each)

5. **Create a Pull Request** with the title: `Add Entur SX integration logos`

## Design Notes

- **Icon Design**: Official Entur app logo (unmodified)
- **Source**: 512x512px PNG from Entur's official resources
- **Content**: White "EN" letters with red/coral underline on Entur blue rounded square background
- **Light/Dark Modes**: Entur uses the same logo design for both modes (no separate dark variant needed)
- **Resizing**: 
  - Icons: Simple resize to 256x256
  - Logos: Resize to 128x128 and center on 256x128 transparent canvas
- **Branding Compliance**: Uses official unmodified Entur app logo, respecting their brand guidelines

## Legal & Attribution

The Entur logo and brand elements are property of Entur AS. This integration is for use with Entur's public APIs and respects their branding guidelines. For official Entur branding information, visit: https://linje.entur.no/

## Python Resize Script (Alternative)

If you have Python with Pillow installed:

```python
from PIL import Image

# Load source
source = Image.open("EN-app-logo-512x512.png")

# Create icon (256x256)
icon = source.resize((256, 256), Image.Resampling.LANCZOS)
icon.save("icon.png", optimize=True)
icon.save("dark_icon.png", optimize=True)

# Create logo (128x128 centered on 256x128)
logo_resized = source.resize((128, 128), Image.Resampling.LANCZOS)
logo = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
logo.paste(logo_resized, (64, 0))
logo.save("logo.png", optimize=True)
logo.save("dark_logo.png", optimize=True)

print("✓ All PNG files created")
```

Install Pillow: `pip install Pillow`
