#!/usr/bin/env python3
"""
Migrate SQLite database to PostgreSQL
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

def migrate_sqlite_to_postgres():
    """Migrate data from SQLite to PostgreSQL"""
    
    print("="*60)
    print("DATABASE MIGRATION: SQLite to PostgreSQL")
    print("="*60)
    
    # Try to get password from .env or args
    pg_password = os.environ.get('PG_PASSWORD', '')
    
    if not pg_password and len(sys.argv) > 1:
        pg_password = sys.argv[1]
    
    if not pg_password:
        pg_password = "postgres"  # default
    
    # SQLite connection (current)
    sqlite_uri = "sqlite:///D:/Projects/ar-interior-dashboard/instance/ar_interior.db"
    
    # PostgreSQL connection (target)
    postgres_uri = f"postgresql://postgres:{pg_password}@localhost:5432/ar_interior_db"
    
    print(f"\nSource: {sqlite_uri}")
    print(f"Target: postgresql://postgres:****@localhost:5432/ar_interior_db")
    
    # Create engines
    sqlite_engine = create_engine(sqlite_uri)
    postgres_engine = create_engine(postgres_uri)
    
    # Connect to both databases
    sqlite_conn = sqlite_engine.connect()
    postgres_conn = postgres_engine.connect()
    
    # Get list of tables - use quoted names for PostgreSQL reserved words
    tables = ['"user"', 'project', 'budget', 'wishlist_item', 'feedback', 
             'ar_sessions', 'ar_placed_models', 'ar_model_library', 
             'generated_design_templates', 'image_generation_process']
    
    # SQLite table name mapping (actual name -> quoted name)
    table_mapping = {
        '"user"': 'user'
    }
    
    try:
        total_migrated = 0
        
        for quoted_table in tables:
            sqlite_table = table_mapping.get(quoted_table, quoted_table)
            
            print(f"\n[2/2] Migrating table: {sqlite_table}")
            
            # Read data from SQLite
            result = sqlite_conn.execute(text(f"SELECT * FROM {sqlite_table}"))
            rows = result.fetchall()
            columns = result.keys()
            
            print(f"   Found {len(rows)} records")
            
            if not rows:
                continue
            
            # Insert into PostgreSQL
            for row in rows:
                placeholders = ', '.join([f':{col}' for col in columns])
                column_list = ', '.join(columns)
                
                insert_stmt = text(f"INSERT INTO {quoted_table} ({column_list}) VALUES ({placeholders})")
                row_dict = dict(zip(columns, row))
                
                # Convert non-serializable types
                for key, value in row_dict.items():
                    if hasattr(value, 'isoformat'):
                        row_dict[key] = value.isoformat()
                    elif isinstance(value, bytes):
                        row_dict[key] = value.decode('utf-8')
                
                try:
                    postgres_conn.execute(insert_stmt, row_dict)
                except Exception as e:
                    print(f"   Warning: {e}")
            
            postgres_conn.commit()
            total_migrated += len(rows)
            print(f"   Migrated {len(rows)} records")
        
        print("\n" + "="*60)
        print(f"MIGRATION COMPLETE! Total records: {total_migrated}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\nMigration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == '__main__':
    success = migrate_sqlite_to_postgres()
    sys.exit(0 if success else 1)
