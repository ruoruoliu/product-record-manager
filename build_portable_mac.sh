#!/bin/bash
set -e

# Configuration
PYTHON_VER="3.10.11"
PYTHON_URL="https://www.python.org/ftp/python/$PYTHON_VER/python-$PYTHON_VER-embed-amd64.zip"
DIST_DIR="dist_portable"
APP_NAME="ProductManager"
FULL_APP_PATH="$DIST_DIR/$APP_NAME"
LIB_DIR="$FULL_APP_PATH/lib"

echo "========================================"
echo "   Building Portable Windows Package    "
echo "========================================"

# 1. Clean up
echo "[1/6] Cleaning up previous build..."
rm -rf "$DIST_DIR"
mkdir -p "$FULL_APP_PATH"
mkdir -p "$LIB_DIR"

# 2. Download Windows Embeddable Python
echo "[2/6] Downloading Windows Embeddable Python..."
curl -o python_embed.zip "$PYTHON_URL"
unzip -q python_embed.zip -d "$FULL_APP_PATH/python"
rm python_embed.zip

# 3. Download Windows Dependencies (Wheels)
echo "[3/6] Downloading dependencies for Windows..."
mkdir -p temp_wheels
# Explicitly add colorama because it's a Windows-specific dependency for Click/Flask
# that sometimes gets skipped when downloading from macOS
pip download Flask Flask-SQLAlchemy colorama \
    --dest temp_wheels \
    --platform win_amd64 \
    --python-version 3.10 \
    --only-binary=:all: \
    --implementation cp \
    --abi cp310

# 4. Install Dependencies (Unzip Wheels)
echo "[4/6] Installing dependencies..."
for whl in temp_wheels/*.whl; do
    echo "Processing $whl..."
    unzip -q -o "$whl" -d "$LIB_DIR"
done
rm -rf temp_wheels

# 5. Configure Python Environment
echo "[5/6] Configuration..."
# Find the ._pth file (e.g. python310._pth)
PTH_FILE=$(find "$FULL_APP_PATH/python" -name "*._pth")
# Enable imports from our local folders
# Add ".." (project root) and "../lib" (dependencies) to the path file
echo ".." >> "$PTH_FILE"
echo "../lib" >> "$PTH_FILE"
# Enable site module (often needed for deeper dependencies)
sed -i '' 's/#import site/import site/g' "$PTH_FILE"

# 6. Copy App Files
echo "[6/6] Copying application files..."
cp app.py "$FULL_APP_PATH/"
if [ -d "templates" ]; then cp -r templates "$FULL_APP_PATH/"; fi
if [ -d "static" ]; then cp -r static "$FULL_APP_PATH/"; fi

# 7. Create Startup Script
echo "Creating startup script..."
cat > "$FULL_APP_PATH/管理系统.bat" << EOL
@echo off
echo Starting Product Manager...
REM We pass --production to tell app.py to handle browser opening and auto-shutdown
"python\python.exe" app.py --production
pause
EOL

echo "========================================"
echo "Build Success!"
echo "The portable folder is here: $FULL_APP_PATH"
echo "You can zip this '$APP_NAME' folder and send it to your user."
echo "They just need to double-click '管理系统.bat'."
echo "========================================"
