#!/bin/bash

# Set the source and destination paths
WEB_DIR="."
DIST_DIR="$WEB_DIR/dist"
DESTINATION="../../docs/ai"

# Navigate to web directory
cd "$WEB_DIR" || { echo "Error: Could not navigate to web directory"; exit 1; }

# Run npm build command
echo "Running npm build..."
npm run build || { echo "Error: npm build failed"; exit 1; }

# Check if dist directory exists
if [ ! -d "$DIST_DIR" ]; then
    echo "Error: dist directory not found after build"
    exit 1
fi

# Create destination directory if it doesn't exist
mkdir -p "$DESTINATION"
rm -rfv "$DESTINATION/assets"

# Copy dist folder to the destination
echo "Copying dist folder to $DESTINATION..."
cp -rv "$DIST_DIR"/* "$DESTINATION"/ || { echo "Error: Failed to copy dist folder"; exit 1; }

echo "Build and copy completed successfully!"