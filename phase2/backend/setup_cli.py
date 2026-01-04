"""
Setup script for CLI installation
"""
from setuptools import setup, find_packages

setup(
    name='climate-ews-cli',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click>=8.0.0',
        'tabulate>=0.9.0',
    ],
    entry_points={
        'console_scripts': [
            'climate-cli=cli:cli',
            'pipeline=app.cli.pipeline_cli:pipeline',
        ],
    },
    author='Climate EWS Team',
    description='CLI for Climate Early Warning System',
    python_requires='>=3.8',
)
