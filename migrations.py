"""
Flask-Migrate migration script for database version control
Run this script to initialize migrations for your project
"""

from flask_migrate import Migrate
from app import app, db

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Use Flask CLI for migration commands
@app.cli.command()
def init_db():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        print("Database initialized!")

if __name__ == '__main__':
    with app.app_context():
        migrate.init_app(app, db)
        print("Migration system ready. Use 'flask db init' to start migrations.")
