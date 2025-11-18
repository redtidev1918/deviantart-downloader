#!/usr/bin/env python3
"""
Setup script for DeviantArt Downloader
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="deviantart-downloader",
    version="3.0.0",
    author="DeviantArt Downloader Team",
    author_email="",
    description="专业的 DeviantArt 作品批量下载工具，支持多种下载模式和防封策略",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/deviantart-downloader",
    packages=find_packages(exclude=["tests*", "docs*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Graphics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    keywords="deviantart downloader scraper art gallery download batch",
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.12.0",
            "mypy>=1.7.1",
            "ruff>=0.1.7",
        ],
        "async": [
            "httpx>=0.25.0",
            "aiofiles>=23.2.1",
            "pydantic>=2.5.0",
            "pydantic-settings>=2.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "devart-dl=deviantart_downloader_cli:main",
            "deviantart-dl=deviantart_downloader_cli:main",
            "da-dl=deviantart_downloader_cli:main",
        ],
    },
    scripts=[
        "devart-dl",
    ],
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/yourusername/deviantart-downloader/issues",
        "Source": "https://github.com/yourusername/deviantart-downloader",
        "Documentation": "https://github.com/yourusername/deviantart-downloader#readme",
    },
)
