#!/usr/bin/env python3
"""Setup script for PAI - Personal AI Infrastructure"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme = Path("README.md")
long_description = readme.read_text() if readme.exists() else ""

setup(
    name="pai-python",
    version="0.1.0",
    description="Personal AI Infrastructure - Minimal Python implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Personal AI Infrastructure Team",
    author_email="",
    url="https://github.com/lampts/Personal_AI_Infrastructure",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "click>=8.1.7",
        "pyyaml>=6.0.1",
        "anthropic>=0.18.0",
    ],
    extras_require={
        "voice": ["elevenlabs>=0.2.27"],
        "dev": [
            "pytest>=7.4.4",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "mypy>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pai=pai:cli",
            "pai-hooks=hooks:cli",
            "pai-history=history:cli",
            "pai-voice=voice:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="ai cli anthropic claude personal-ai-infrastructure unix",
)
