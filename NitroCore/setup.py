"""
Setup script for compiling and distributing the NitroCore Windows System Optimizer.
Features optimized file-stream configuration parsers and proper folder alignment mapping.
"""

import sys
from pathlib import Path
from setuptools import setup, find_packages

# Base folder location mapping
BASE_DIR = Path(__file__).resolve().parent

# 1. Read version from file smoothly with a safe string fallback
VERSION_FILE = BASE_DIR / "VERSION"
VERSION = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "1.0.0"

# 2. Robust parsing pipeline for requirements.txt (cleans comments and white space)
INSTALL_REQUIRES = []
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"
if REQUIREMENTS_FILE.exists():
    for line in REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        # Only parse actual packages, dropping comments or blank spacing lines
        if line and not line.startswith("#"):
            INSTALL_REQUIRES.append(line)

# 3. Fetch distribution payload description details safely
README_FILE = BASE_DIR / "README.md"
LONG_DESCRIPTION = README_FILE.read_text(encoding="utf-8") if README_FILE.exists() else ""

setup(
    name="nitrocore-optimizer",
    version=VERSION,
    author="NitroCore Team",
    author_email="sentinelsafeguard@outlook.com",
    description="Professional, thread-safe Windows system optimization utility framework.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/TheRealJesusTheHacker/NitroCore",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        # Explicitly targets Windows due to heavy win32/winreg API dependencies
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    # Automatically tells setuptools that all source logic lives in 'source/'
    # (M-5: was incorrectly pointed at a nonexistent 'src/' layout, which
    # built empty packages)
    packages=find_packages(where="source"),
    package_dir={"": "source"},
    
    # Bundle core manifest text parameters alongside binary wheels
    package_data={
        "": ["LICENSE", "README.md", "VERSION"],
    },
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    python_requires=">=3.9",
    keywords=["windows", "optimizer", "performance", "cleanup", "registry", "services"],
    project_urls={
        "GitHub": "https://github.com/TheRealJesusTheHacker/NitroCore",
        "Bug Reports": "https://github.com/TheRealJesusTheHacker/NitroCore/issues",
    },
)
