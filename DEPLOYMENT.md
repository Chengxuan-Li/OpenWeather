# Deployment Guide

## Quick Deploy to Render

### Option 1: Automatic Deployment (Recommended)

1. **Fork this repository** to your GitHub account
2. **Create a Render account** at [render.com](https://render.com)
3. **Connect your repository** - Render will automatically detect the `render.yaml` file
4. **Deploy** - The service will be created automatically with optimized settings

### Option 2: Manual Deployment

1. **Create a new Web Service** in Render
2. **Connect your GitHub repository**
3. **Configure the service**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn openweather.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `PORT`: `10000`
     - `PYTHON_VERSION`: `3.11.7`

## Build Optimization

The project is optimized for fast deployment:

### ✅ What's Optimized

- **Fixed dependency versions** in `requirements.txt` for faster resolution
- **No editable installs** (`pip install -r requirements.txt` instead of `pip install -e .`)
- **render.yaml** for automatic configuration
- **setup.py** as fallback for platforms that don't handle `pyproject.toml` well
- **Compatible Python version** (3.11.7) specified in `runtime.txt`

### 🚀 Build Process

1. **Dependency Installation**: `pip install -r requirements.txt`
2. **Application Start**: `uvicorn openweather.main:app --host 0.0.0.0 --port $PORT`

## Troubleshooting

### "Getting requirements to build editable: started" Takes Forever

**Problem**: Render is trying to install the project in editable mode, which is slow.

**Solution**: Use `pip install -r requirements.txt` instead of `pip install -e .`

### Python Version Issues

**Problem**: Compatibility issues with Python 3.12 and older numpy versions.

**Solution**: 
- Use Python 3.11.7 (specified in `runtime.txt`)
- Updated numpy to 1.26.2 for better compatibility

### Build Failures

**Problem**: Build fails due to dependency conflicts.

**Solutions**:
1. **Check Python version**: Ensure using Python 3.11
2. **Clear cache**: Render will automatically clear build cache on retry
3. **Use requirements.txt**: Avoid editable installs
4. **Check logs**: Look for specific error messages in build logs

## Alternative Platforms

### Railway

1. **Connect your GitHub repository**
2. **Railway will auto-detect** the Python app
3. **Set environment variables** as needed

### Heroku

1. **Install Heroku CLI**
2. **Create app**: `heroku create your-app-name`
3. **Deploy**: `git push heroku main`

### Vercel

1. **Import your GitHub repository**
2. **Configure build settings**:
   - Build Command: `pip install -r requirements.txt`
   - Output Directory: `openweather`
   - Install Command: `pip install -r requirements.txt`

## Environment Variables

### Required for Production

```bash
PORT=10000
PYTHON_VERSION=3.11.7
```

### Optional

```bash
DEBUG=false
LOG_LEVEL=INFO
OUTPUTS_DIR=outputs
```

## Performance Tips

1. **Use requirements.txt**: Faster than editable installs
2. **Fixed versions**: Avoid dependency resolution delays
3. **Python 3.11**: Better compatibility with scientific packages
4. **Clear build cache**: If builds get stuck, trigger a new deployment

## Monitoring

After deployment, monitor:
- **Build logs** for any errors
- **Application logs** for runtime issues
- **Performance metrics** for optimization opportunities

## Support

If you encounter issues:
1. Check the build logs in Render
2. Verify Python version compatibility
3. Ensure all dependencies are properly specified
4. Try clearing build cache and redeploying
