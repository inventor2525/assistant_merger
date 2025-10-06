from setuptools import setup, find_packages

setup(
    name="assistant_merger",
    version="0.1.0",
    author="Charlie Mehlenbeck",
    author_email="charlie_inventor2003@yahoo.com",
    description="A tool that facilitates interaction with git diffs that can aid LLMs in reviewing their own code changes in detail.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/inventor2525/assistant_merger",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": ["unittest"],
    },
)