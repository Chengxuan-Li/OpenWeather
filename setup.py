from setuptools import setup, find_packages

setup(
    name="openweather",
    version="0.1.0",
    description="NSRDB to EPW web application",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "jinja2==3.1.2",
        "python-multipart==0.0.6",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "requests==2.31.0",
        "pandas==2.1.4",
        "numpy==1.26.2",
        "shapely==2.0.2",
    ],
    python_requires=">=3.11",
)
