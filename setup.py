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
    name="devart-dl",  # 更简短独特的包名
    version="3.0.1",
    author="zoidberg-xgd",
    author_email="",
    description="Professional DeviantArt batch downloader with multiple login methods and anti-ban protection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zoidberg-xgd/deviantart-downloader",
    packages=find_packages(exclude=["tests*", "docs*"]),
    py_modules=["deviantart_downloader_cli"],
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
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: English",
    ],
    keywords="deviantart downloader scraper art gallery download batch cli anti-ban i18n",
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "browser": [
            "selenium>=4.0.0",
            "webdriver-manager>=3.8.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "black>=22.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "devart-dl=deviantart_downloader_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/zoidberg-xgd/deviantart-downloader/issues",
        "Source": "https://github.com/zoidberg-xgd/deviantart-downloader",
        "Documentation": "https://github.com/zoidberg-xgd/deviantart-downloader#readme",
        "Changelog": "https://github.com/zoidberg-xgd/deviantart-downloader/blob/main/CHANGELOG.md",
    },
)
