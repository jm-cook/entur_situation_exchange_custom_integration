res# PowerShell script to resize Entur app logo PNG to required sizes
# Uses the official EN-app-logo-512x512.png as source

$sourcePng = "EN-app-logo-512x512.png"

if (-not (Test-Path $sourcePng)) {
    Write-Host "❌ Source file $sourcePng not found!" -ForegroundColor Red
    exit 1
}

Write-Host "Resizing Entur app logo to required dimensions..." -ForegroundColor Cyan
Write-Host ""

# Check if ImageMagick is available
$magickPath = Get-Command "magick" -ErrorAction SilentlyContinue
if (-not $magickPath) {
    Write-Host "❌ ImageMagick 'magick' command not found!" -ForegroundColor Red
    Write-Host "Please install ImageMagick from https://imagemagick.org/script/download.php" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternatively, you can manually resize $sourcePng to:" -ForegroundColor Yellow
    Write-Host "  - icon.png (256x256)" -ForegroundColor Yellow
    Write-Host "  - dark_icon.png (256x256)" -ForegroundColor Yellow
    Write-Host "  - logo.png (256x128, centered)" -ForegroundColor Yellow
    Write-Host "  - dark_logo.png (256x128, centered)" -ForegroundColor Yellow
    exit 1
}

# Create icon.png (256x256) - just resize
Write-Host "Creating icon.png (256x256)..." -NoNewline
& magick $sourcePng -resize 256x256 icon.png
if ($?) {
    $size = (Get-Item icon.png).Length / 1KB
    Write-Host " ✓ ($([math]::Round($size, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host " ✗ Failed" -ForegroundColor Red
}

# Create dark_icon.png (256x256) - same as light mode for Entur
Write-Host "Creating dark_icon.png (256x256)..." -NoNewline
Copy-Item icon.png dark_icon.png -Force
if ($?) {
    $size = (Get-Item dark_icon.png).Length / 1KB
    Write-Host " ✓ ($([math]::Round($size, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host " ✗ Failed" -ForegroundColor Red
}

# Create logo.png (256x128) - resize to 128x128 and center on 256x128 canvas
Write-Host "Creating logo.png (256x128, centered)..." -NoNewline
& magick $sourcePng -resize 128x128 -background none -gravity center -extent 256x128 logo.png
if ($?) {
    $size = (Get-Item logo.png).Length / 1KB
    Write-Host " ✓ ($([math]::Round($size, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host " ✗ Failed" -ForegroundColor Red
}

# Create dark_logo.png (256x128) - same as light mode for Entur
Write-Host "Creating dark_logo.png (256x128, centered)..." -NoNewline
Copy-Item logo.png dark_logo.png -Force
if ($?) {
    $size = (Get-Item dark_logo.png).Length / 1KB
    Write-Host " ✓ ($([math]::Round($size, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host " ✗ Failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ All PNG files created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Entur uses the same logo design for light and dark modes," -ForegroundColor Cyan
Write-Host "so dark_icon.png and dark_logo.png are identical to their light counterparts." -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Verify PNG files look correct"
Write-Host "2. Optionally optimize with: magick mogrify -strip -define png:compression-level=9 *.png"
Write-Host "3. Follow README.md for submission to Home Assistant brands repository"
