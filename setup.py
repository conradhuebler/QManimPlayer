"""Setup configuration for QManimPlayer."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README if it exists
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="qmanimplayer",
    version="0.1.0",
    description="PyQt6 Parameter Editor for manim-gl Scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Conrad Hübler",
    author_email="Conrad.Huebler@gmx.net",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "qmanimplayer=qmanimplayer.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
