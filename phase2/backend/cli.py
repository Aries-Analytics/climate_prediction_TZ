#!/usr/bin/env python
"""
Climate Early Warning System - CLI

Main command-line interface for system operations.
"""
import click
from app.cli.pipeline_cli import pipeline


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    Climate Early Warning System CLI
    
    Command-line interface for managing the automated forecast pipeline.
    """
    pass


# Register command groups
cli.add_command(pipeline)


if __name__ == '__main__':
    cli()
