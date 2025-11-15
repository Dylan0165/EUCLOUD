#!/bin/bash
# Setup persistent storage directories on VM for EUCLOUD
# Similar to Nextcloud's persistent storage approach

echo "🔧 Setting up EUCLOUD persistent storage on VM..."

# Create base directory
sudo mkdir -p /var/eucloud

# Create storage directories
sudo mkdir -p /var/eucloud/database
sudo mkdir -p /var/eucloud/uploads
sudo mkdir -p /var/eucloud/thumbnails

# Set proper permissions (allow K3s to write)
sudo chown -R 1000:1000 /var/eucloud/database
sudo chown -R 1000:1000 /var/eucloud/uploads
sudo chown -R 1000:1000 /var/eucloud/thumbnails

# Set proper permissions
sudo chmod -R 755 /var/eucloud

echo "✅ Storage directories created:"
echo "   📁 /var/eucloud/database    - SQLite database"
echo "   📁 /var/eucloud/uploads     - User uploaded files"
echo "   📁 /var/eucloud/thumbnails  - Image thumbnails"
echo ""
echo "💾 Total space allocated:"
du -sh /var/eucloud/* 2>/dev/null || echo "   (empty - no data yet)"
echo ""
echo "🎯 These directories will persist even if K3s pods crash or restart!"
echo "   Just like Nextcloud's data directory approach."
