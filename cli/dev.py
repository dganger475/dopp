"""
Development CLI Commands
=====================

CLI commands to assist in development.
"""

import click
from flask import current_app
from flask.cli import with_appcontext
import os
import sys
import logging
from datetime import datetime

from utils.dev.testing import create_test_data
from utils.dev.debug import debug_info

logger = logging.getLogger(__name__)

@click.group()
def dev():
    """Development commands."""
    pass

@dev.command()
@with_appcontext
def setup_dev():
    """Set up development environment."""
    click.echo("Setting up development environment...")
    
    # Create necessary directories
    dirs = [
        'instance',
        'logs',
        'static/uploads',
        'static/profile_pics',
        'instance/flask_session'
    ]
    
    for dir_path in dirs:
        full_path = os.path.join(current_app.root_path, dir_path)
        os.makedirs(full_path, exist_ok=True)
        click.echo(f"Created directory: {dir_path}")
    
    # Initialize database
    from extensions import db
    db.create_all()
    click.echo("Initialized database")
    
    click.echo("Development environment setup complete!")

@dev.command()
@with_appcontext
def create_mock_data():
    """Create mock data for development."""
    click.echo("Creating mock data...")
    
    try:
        from utils.db.database import db
        data = create_test_data(db)
        
        click.echo(f"Created {len(data['users'])} users")
        click.echo(f"Created {len(data['posts'])} posts")
        click.echo(f"Created {len(data['comments'])} comments")
    except Exception as e:
        click.echo(f"Error creating mock data: {e}", err=True)
        sys.exit(1)

@dev.command()
@with_appcontext
def show_routes():
    """Show all registered routes."""
    click.echo("Registered routes:")
    click.echo("-" * 80)
    
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ', '.join(rule.methods),
            'path': str(rule)
        })
    
    # Sort routes by endpoint
    routes.sort(key=lambda x: x['endpoint'])
    
    for route in routes:
        click.echo(f"Endpoint: {route['endpoint']}")
        click.echo(f"Methods:  {route['methods']}")
        click.echo(f"Path:     {route['path']}")
        click.echo("-" * 80)

@dev.command()
@with_appcontext
def show_config():
    """Show current configuration."""
    click.echo("Current configuration:")
    click.echo("-" * 80)
    
    # Get config excluding sensitive values
    config = {
        k: v for k, v in current_app.config.items()
        if not k.startswith('_') 
        and not any(sensitive in k.lower() for sensitive in ['key', 'password', 'secret'])
        and isinstance(v, (str, int, float, bool, list, dict))
    }
    
    for key, value in sorted(config.items()):
        click.echo(f"{key}: {value}")

@dev.command()
@with_appcontext
def clear_logs():
    """Clear log files."""
    log_dir = os.path.join(current_app.root_path, 'logs')
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                file_path = os.path.join(log_dir, filename)
                try:
                    os.remove(file_path)
                    click.echo(f"Deleted: {filename}")
                except Exception as e:
                    click.echo(f"Error deleting {filename}: {e}", err=True)
    click.echo("Log files cleared!")

@dev.command()
@with_appcontext
def debug_check():
    """Run debug checks and show system info."""
    info = debug_info()
    
    click.echo("Debug Information:")
    click.echo("-" * 80)
    
    for key, value in info.items():
        if isinstance(value, dict):
            click.echo(f"\n{key}:")
            for k, v in value.items():
                click.echo(f"  {k}: {v}")
        else:
            click.echo(f"{key}: {value}")

def init_app(app):
    """Register development CLI commands with the app."""
    app.cli.add_command(dev) 