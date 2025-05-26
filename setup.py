from setuptools import setup, find_packages

setup(
    name="chariot_engine",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "streamlit",
    ],
    python_requires=">=3.8",
) 