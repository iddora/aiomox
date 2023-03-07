"""Setup module for aiomox."""
from pathlib import Path

from setuptools import find_packages, setup

PROJECT_DIR = Path(__file__).parent.resolve()
README_FILE = PROJECT_DIR / "README.md"
VERSION = "1.0.5"


setup(
    name="aiomox",
    version=VERSION,
    license="Apache License 2.0",
    url="https://github.com/iddora/aiomox",
    author="Iddo Rachlewski",
    author_email="github@rachlewski.com",
    description="Asynchronous library to control MOX devices.",
    long_description=README_FILE.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    package_data={"aiomox": ["py.typed"], "aiomox.device": ["py.typed"]},
    zip_safe=True,
    platforms="any",
    install_requires=["setuptools==65.5.0"],
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)