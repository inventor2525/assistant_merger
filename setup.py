from setuptools import setup, find_packages

setup(
    name="assistant_merger",
    version="0.1.0",
    packages=["assistant_merger"],
    install_requires=["gitpython>=3.1.0"],
    description="A tool to interact with git diffs for large language model review",
    author="Your Name",
    author_email="your.email@example.com",
    python_requires=">=3.8",
)