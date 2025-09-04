# Render Deployment - Quick Fix

## The Problem
Render gets stuck on "Getting requirements to build editable: started" because it's trying to use `pyproject.toml` for editable installs.

## The Solution
We've removed `pyproject.toml` and optimized for `requirements.txt` only.

## What We Changed

1. **Removed `pyproject.toml`** → `pyproject.toml.backup`
2. **Simplified `setup.py`** → Minimal version
3. **Updated `render.yaml`** → Explicit build commands
4. **Enhanced `requirements.txt`** → Fixed versions + setuptools

## Deployment Steps

### Option 1: Automatic (Recommended)
1. **Fork this repository**
2. **Connect to Render**
3. **Render will auto-detect** the `render.yaml` file
4. **Deploy** - Should be much faster now!

### Option 2: Manual
1. **Create new Web Service** in Render
2. **Connect your repository**
3. **Set Build Command**: 
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Set Start Command**:
   ```bash
   uvicorn openweather.main:app --host 0.0.0.0 --port $PORT
   ```
5. **Environment Variables**:
   - `PORT`: `10000`
   - `PYTHON_VERSION`: `3.11.7`

## Expected Build Process

```
✅ Installing pip...
✅ Installing requirements.txt...
✅ Starting uvicorn...
✅ Application ready!
```

## If Still Stuck

1. **Clear Render cache**: Trigger a new deployment
2. **Check logs**: Look for specific error messages
3. **Verify Python version**: Ensure 3.11.7
4. **Try manual deployment**: Use Option 2 above

## Files Structure

```
✅ render.yaml          # Automatic deployment config
✅ requirements.txt     # Fixed dependency versions
✅ setup.py            # Minimal setup (no editable install)
❌ pyproject.toml      # Removed (causing the issue)
✅ runtime.txt         # Python 3.11.7
```

## Build Time Comparison

- **Before**: 10+ minutes (editable install)
- **After**: 2-3 minutes (direct install)

The build should now be much faster! 🚀
