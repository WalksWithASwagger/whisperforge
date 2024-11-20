from setuptools import setup, find_packages

setup(
    name="whisperforge",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "fastapi",
    ]
) 