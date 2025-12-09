# Deployment Files

This directory contains all deployment-related files for the Farmers Portal application.

## 📁 Files in this Directory

- **`DEPLOYMENT.md`** - Complete step-by-step deployment guide for Render
- **`render.yaml`** - Render configuration file (optional, for blueprint deployment)
- **`.renderignore`** - Files to exclude from deployment
- **`README.md`** - This file

## 🚀 Quick Start

1. **Read the guide**: Open `DEPLOYMENT.md` for detailed step-by-step instructions
2. **Choose deployment method**:
   - **Option 1** (Recommended): Manual setup via Render dashboard - no file copying needed
   - **Option 2**: Use `render.yaml` blueprint - copy files to root first
3. **Follow the guide**: All instructions are in `DEPLOYMENT.md`

## 📝 Important Notes

- ✅ All deployment files are organized here for cleanliness
- ✅ For **Option 1** (Manual): No need to copy files - configure in Render dashboard
- ✅ For **Option 2** (Blueprint): Copy `render.yaml` and `.renderignore` to project root
- ✅ The `.renderignore` file helps exclude unnecessary files from deployment

## 🔧 File Usage

### `render.yaml`
- Defines web service and database configuration
- Used for automated blueprint deployment
- Only needed if using Option 2

### `.renderignore`
- Similar to `.gitignore` but for Render builds
- Excludes files/folders from deployment package
- Reduces build size and time

### `DEPLOYMENT.md`
- Complete deployment guide with troubleshooting
- Step-by-step instructions for both options
- Post-deployment tips and best practices
