from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ofs",
    version="0.1.0",
    author="OFS Development Team",
    author_email="",
    description="Offline File System - Local-first version control for air-gapped environments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/frag2win/OFS",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - stdlib only
    ],
    entry_points={
        "console_scripts": [
            "ofs=ofs.__main__:main",
        ],
    },
)
