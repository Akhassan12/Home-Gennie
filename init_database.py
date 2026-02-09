#!/usr/bin/env python3
"""
Database Initialization Script
Creates database tables and deletes old user entries
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app import app, db, User

def init_database():
    """Initialize the database and clean up old data"""
    print("\n" + "="*60)
    print("DATABASE INITIALIZATION")
    print("="*60 + "\n")
    
    with app.app_context():
        try:
            # Create all tables
            print("[1] Creating database tables...")
            db.create_all()
            print("✅ Database tables created\n")
            
            # Delete all existing users
            print("[2] Cleaning up old user entries...")
            user_count = User.query.count()
            if user_count > 0:
                User.query.delete()
                db.session.commit()
                print(f"✅ Deleted {user_count} old user entries\n")
            else:
                print("✅ No old users found\n")
            
            # Create a default test user
            print("[3] Creating default test user...")
            test_user = User(
                username='testuser',
                email='test@example.com'
            )
            test_user.set_password('SecureTest@2026')
            
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test user created:")
            print(f"   Username: testuser")
            print(f"   Password: SecureTest@2026")
            print(f"   Email: test@example.com\n")
            
            print("="*60)
            print("DATABASE INITIALIZATION SUCCESSFUL!")
            print("="*60)
            print("\nDatabase Configuration:")
            print(f"Type: {'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}")
            print(f"URI: {app.config['SQLALCHEMY_DATABASE_URI']}\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error initializing database: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
