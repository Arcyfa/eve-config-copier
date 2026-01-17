#!/bin/bash

# EVE Config Copier Cleanup Script
# This script removes all files from cache, logs, and backups directories
# while preserving the directory structure

set -e  # Exit on any error

echo "Starting cleanup..."

# Function to safely remove files from a directory
cleanup_directory() {
    local dir="$1"
    if [ -d "$dir" ]; then
        echo "Cleaning up $dir..."
        find "$dir" -type f -delete
        echo "  ✓ Removed all files from $dir"
    else
        echo "  ⚠ Directory $dir does not exist, skipping"
    fi
}

# Clean cache directories
echo "Cleaning cache directories..."
cleanup_directory "cache/char"
cleanup_directory "cache/corp" 
cleanup_directory "cache/img/char"
cleanup_directory "cache/img/corp"

# Clean logs directory
echo "Cleaning logs directory..."
cleanup_directory "logs"

# Clean backups directory
echo "Cleaning backups directory..."
cleanup_directory "backups"

echo "Cleanup completed successfully!"
echo ""
echo "Directory structure preserved:"
echo "- cache/char/, cache/corp/, cache/img/char/, cache/img/corp/ (empty)"
echo "- logs/ (empty)"
echo "- backups/ (empty)"