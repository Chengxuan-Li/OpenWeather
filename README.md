# OpenWeather

A web-based interface for the NSRDB to EPW pipeline, replicating the workflow from [NSRDB2EPW.ipynb](https://github.com/kastnerp/NREL-PSB3-2-EPW).

## 🌟 Features

- **Web Interface**: User-friendly browser-based form with interactive map
- **Interactive Map**: Click to place points or draw polygons to generate WKT geometry
- **Multiple Datasets**: Support for CONUS, full-disc, aggregated, and TMY datasets
- **Automatic EPW Conversion**: Convert CSV outputs to EPW files automatically
- **REST API**: Programmatic access to all functionality
- **URL Query Interface**: Direct URL-based job execution
- **File Management**: Organized output storage with job summaries
- **Real-time Validation**: Input validation and error handling

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- NSRDB API key (get one from [NREL](https://developer.nrel.gov/signup/))

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/openweather.git
   cd openweather
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   ```

3. **Run the development server**
   ```bash
   uvicorn openweather.main:app --reload --host 0.0.0.0 --port 8080
   ```

4. **Open your browser**
   - Main app: http://localhost:8080
   - API docs: http://localhost:8080/docs
   - Health check: http://localhost:8080/health

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run in development mode
docker-compose --profile dev up --build
```

### Using the Development Script

```bash
# Make the script executable
chmod +x scripts/run_dev.sh

# Run the development server
./scripts/run_dev.sh
```

## 📖 Usage

### Web Interface

1. **Navigate to the main page** (http://localhost:8080)
2. **Enter WKT geometry** or use the interactive map
3. **Select dataset** and temporal resolution
4. **Enter years** (comma-separated)
5. **Provide your NSRDB API key** and email
6. **Submit** to start the download and conversion process

### URL Query Interface

Execute jobs directly via URL:

```
http://localhost:8080/q?wkt=POINT(-76.5+42.4)&dataset=nsrdb-GOES-full-disc-v4-0-0&years=2021&interval=60&apikey=YOUR_KEY&email=you@mail.com&as_epw=true
```

### REST API

```bash
# Run a job
curl -X POST "http://localhost:8080/api/download" \
  -H "Content-Type: application/json" \
  -d '{
    "wkt": "POINT(-76.5 42.4)",
    "dataset": "nsrdb-GOES-full-disc-v4-0-0",
    "interval": "60",
    "years": ["2021"],
    "api_key": "YOUR_API_KEY",
    "email": "your@email.com",
    "convert_to_epw": true
  }'

# Get available datasets
curl "http://localhost:8080/api/datasets"

# Validate WKT
curl "http://localhost:8080/api/validate-wkt?wkt=POINT(-76.5+42.4)"
```

## 📊 Available Datasets

| Dataset | Coverage | Temporal Resolution | Years |
|---------|----------|-------------------|-------|
| **CONUS** | USA Continental and Mexico | 5, 30, 60 min | 2021-2023 |
| **Full-disc** | USA and Americas | 10, 30, 60 min | 2018-2023 |
| **Aggregated** | USA and Americas | 30, 60 min | 1998-2023 |
| **TMY** | USA and Americas | 60 min | 2022-2023 |

## 🏗️ Architecture

```
OpenWeather/
├── openweather/                 # Main application
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings and configuration
│   ├── deps.py                  # FastAPI dependencies
│   ├── routers/                 # API and UI routes
│   │   ├── ui.py               # Web interface routes
│   │   └── api.py              # REST API routes
│   ├── services/               # Business logic
│   │   ├── nsrdb_wrapper.py   # NSRDB pipeline wrapper
│   │   ├── geometry.py        # WKT handling utilities
│   │   └── storage.py         # File management
│   ├── templates/              # HTML templates
│   └── static/                 # CSS, JS, and assets
├── imported/                   # Reference files (read-only)
│   ├── nsrdb2epw.py           # Original NSRDB pipeline
│   ├── epw.py                 # EPW file handling
│   └── NSRDB2EPW.ipynb        # Reference notebook
├── tests/                     # Test suite
├── scripts/                   # Utility scripts
└── outputs/                   # Generated files (created at runtime)
```

## 🔧 Configuration

Environment variables (optional):

```bash
# Server settings
HOST=0.0.0.0
PORT=8080
DEBUG=false

# Logging
LOG_LEVEL=INFO

# File paths
OUTPUTS_DIR=outputs
STATIC_DIR=openweather/static
TEMPLATES_DIR=openweather/templates

# Security
SECRET_KEY=your-secret-key-change-in-production
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=openweather --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run linting
ruff check .
black --check .
mypy openweather/
```

## 🚀 Deployment

### GitHub Actions

The repository includes GitHub Actions workflows for:
- **CI**: Automated testing and linting on pull requests
- **Deploy**: Automated deployment preparation

### Deploy to Render

1. **Fork this repository** to your GitHub account
2. **Create a Render account** at [render.com](https://render.com)
3. **Create a new Web Service**:
   - Connect your GitHub repository
   - Set build command: `pip install -e .`
   - Set start command: `uvicorn openweather.main:app --host 0.0.0.0 --port $PORT`
   - Set environment variable: `PORT=10000`

### Deploy to Railway

1. **Fork this repository** to your GitHub account
2. **Create a Railway account** at [railway.app](https://railway.app)
3. **Deploy from GitHub**:
   - Connect your repository
   - Railway will auto-detect the Python app
   - Set environment variables as needed

### Deploy to Heroku

1. **Create a `Procfile`**:
   ```
   web: uvicorn openweather.main:app --host 0.0.0.0 --port $PORT
   ```

2. **Deploy using Heroku CLI**:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Environment Variables for Production

```bash
# Required for production
HOST=0.0.0.0
PORT=8080
DEBUG=false

# Optional
LOG_LEVEL=INFO
OUTPUTS_DIR=outputs
SECRET_KEY=your-secret-key-here
```

## 🐳 Docker

### Production Build

```bash
# Build the image
docker build -t openweather .

# Run the container
docker run -p 8080:8080 openweather
```

### Development with Docker Compose

```bash
# Start development environment
docker-compose --profile dev up --build

# Start production environment
docker-compose up --build
```

## 📝 API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### Key Endpoints

- `GET /` - Main web interface
- `GET /q` - URL query interface
- `POST /run` - Form submission handler
- `POST /api/download` - Run NSRDB job
- `POST /api/convert-to-epw` - Convert CSV to EPW
- `GET /api/datasets` - Get available datasets
- `GET /api/validate-wkt` - Validate WKT geometry
- `GET /health` - Health check

## 🔒 Security

- Input validation for all parameters
- Path traversal protection for file downloads
- CORS configuration for web security
- Environment-based configuration
- Secure file handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Run tests before committing
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [NSRDB2EPW.ipynb](https://github.com/kastnerp/NREL-PSB3-2-EPW) - Original workflow
- [NREL NSRDB](https://nsrdb.nrel.gov/) - Data source
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Leaflet](https://leafletjs.com/) - Interactive maps
- [Tailwind CSS](https://tailwindcss.com/) - Styling

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/openweather/issues)
- **Documentation**: [Wiki](https://github.com/your-org/openweather/wiki)
- **Email**: team@openweather.com

## 🔄 Changelog

### v0.1.0 (2024-01-01)
- Initial release
- Web interface with interactive map
- NSRDB to EPW pipeline integration
- REST API with full documentation
- Docker support
- Comprehensive test suite

---

**Note**: This application replicates the exact workflow from NSRDB2EPW.ipynb. The imported files are reference-only and should not be modified. All functionality is implemented through the web interface and API endpoints.