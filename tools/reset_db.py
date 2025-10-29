from app import app, db
import os

# Check if we're using PostgreSQL
database_url = os.environ.get('DATABASE_URL', 'sqlite:///ar_interior.db')
is_postgresql = database_url.startswith('postgresql')

with app.app_context():
    if is_postgresql:
        print("🗄️  PostgreSQL detected - using migrations...")
        print("To reset PostgreSQL database, run:")
        print("flask db downgrade base")
        print("flask db upgrade")
        print("Or use: flask db stamp head")
    else:
        print("📁 SQLite detected - resetting database...")
        print("Dropping all tables...")
        db.drop_all()
        print("Creating new tables...")
        db.create_all()
        print("✅ Database reset complete!")

    print(f"📊 Current database: {database_url.split('://')[0] if '://' in database_url else 'sqlite'}")
