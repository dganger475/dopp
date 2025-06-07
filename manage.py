"""Database management script for DoppleGänger."""
from flask.cli import FlaskGroup
from app import create_app
from flask_migrate import Migrate, MigrateCommand
from extensions import db, migrate

app = create_app()
cli = FlaskGroup(app)

@cli.command("init_db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized.")

@cli.command("migrate_db")
def migrate_db():
    """Initialize migrations."""
    from flask_migrate import init, migrate, upgrade
    init()
    migrate()
    upgrade()
    print("Database migrations initialized and applied.")

if __name__ == "__main__":
    cli() 