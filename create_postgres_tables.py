#!/usr/bin/env python3
"""
Create PostgreSQL tables and migrate data from SQLite
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

def create_tables_and_migrate():
    """Create tables in PostgreSQL and migrate data"""
    
    print("="*60)
    print("DATABASE MIGRATION: SQLite to PostgreSQL")
    print("="*60)
    
    # Get password from args or env
    pg_password = os.environ.get('PG_PASSWORD', '')
    if not pg_password and len(sys.argv) > 1:
        pg_password = sys.argv[1]
    if not pg_password:
        pg_password = "postgres"
    
    # Connection strings
    sqlite_uri = "sqlite:///D:/Projects/ar-interior-dashboard/instance/ar_interior.db"
    postgres_uri = f"postgresql://postgres:{pg_password}@localhost:5432/ar_interior_db"
    
    print(f"\nSource: {sqlite_uri}")
    print(f"Target: postgresql://postgres:****@localhost:5432/ar_interior_db")
    
    # Create engines
    sqlite_engine = create_engine(sqlite_uri)
    postgres_engine = create_engine(postgres_uri)
    
    sqlite_conn = sqlite_engine.connect()
    postgres_conn = postgres_engine.connect()
    
    # Create tables using raw SQL (matching Flask models)
    create_tables_sql = '''
    -- Drop existing tables
    DROP TABLE IF EXISTS image_generation_process CASCADE;
    DROP TABLE IF EXISTS generated_design_templates CASCADE;
    DROP TABLE IF EXISTS ar_placed_models CASCADE;
    DROP TABLE IF EXISTS ar_sessions CASCADE;
    DROP TABLE IF EXISTS ar_model_library CASCADE;
    DROP TABLE IF EXISTS feedback CASCADE;
    DROP TABLE IF EXISTS wishlist_item CASCADE;
    DROP TABLE IF EXISTS budget CASCADE;
    DROP TABLE IF EXISTS project CASCADE;
    DROP TABLE IF EXISTS "user" CASCADE;
    
    -- Create user table
    CREATE TABLE "user" (
        id SERIAL PRIMARY KEY,
        username VARCHAR(80) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(200) NOT NULL,
        is_verified BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        otp VARCHAR(6),
        otp_created_at TIMESTAMP,
        bio TEXT,
        company VARCHAR(200),
        website VARCHAR(200),
        location VARCHAR(200),
        avatar VARCHAR(500),
        email_notifications BOOLEAN DEFAULT TRUE
    );
    
    -- Create project table
    CREATE TABLE project (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        client VARCHAR(100) NOT NULL,
        due_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'In Progress',
        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create budget table
    CREATE TABLE budget (
        id SERIAL PRIMARY KEY,
        project_name VARCHAR(100) NOT NULL,
        amount FLOAT NOT NULL,
        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create wishlist_item table
    CREATE TABLE wishlist_item (
        id SERIAL PRIMARY KEY,
        item_name VARCHAR(100) NOT NULL,
        item_url VARCHAR(500),
        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create feedback table
    CREATE TABLE feedback (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create ar_sessions table
    CREATE TABLE ar_sessions (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(100) UNIQUE NOT NULL,
        room_type VARCHAR(50) NOT NULL,
        user_id INTEGER REFERENCES "user"(id) ON DELETE SET NULL,
        lighting_config TEXT,
        environment_config TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        is_saved BOOLEAN DEFAULT FALSE
    );
    
    -- Create ar_placed_models table
    CREATE TABLE ar_placed_models (
        id SERIAL PRIMARY KEY,
        instance_id VARCHAR(100) UNIQUE NOT NULL,
        session_id VARCHAR(100) REFERENCES ar_sessions(session_id) ON DELETE CASCADE,
        model_id VARCHAR(100) NOT NULL,
        model_name VARCHAR(200),
        category VARCHAR(50),
        glb_url VARCHAR(500),
        position_x FLOAT DEFAULT 0.0,
        position_y FLOAT DEFAULT 0.0,
        position_z FLOAT DEFAULT 0.0,
        rotation_x FLOAT DEFAULT 0.0,
        rotation_y FLOAT DEFAULT 0.0,
        rotation_z FLOAT DEFAULT 0.0,
        scale_x FLOAT DEFAULT 1.0,
        scale_y FLOAT DEFAULT 1.0,
        scale_z FLOAT DEFAULT 1.0,
        width FLOAT,
        height FLOAT,
        depth FLOAT,
        placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create ar_model_library table
    CREATE TABLE ar_model_library (
        id SERIAL PRIMARY KEY,
        model_id VARCHAR(100) UNIQUE NOT NULL,
        name VARCHAR(200) NOT NULL,
        category VARCHAR(50) NOT NULL,
        glb_url VARCHAR(500) NOT NULL,
        thumbnail_url VARCHAR(500),
        width FLOAT,
        height FLOAT,
        depth FLOAT,
        description TEXT,
        tags TEXT,
        style VARCHAR(50),
        usage_count INTEGER DEFAULT 0,
        rating FLOAT DEFAULT 0.0,
        is_active BOOLEAN DEFAULT TRUE,
        is_premium BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create generated_design_templates table
    CREATE TABLE generated_design_templates (
        id SERIAL PRIMARY KEY,
        template_id VARCHAR(100) UNIQUE NOT NULL,
        design_name VARCHAR(200) NOT NULL,
        design_style VARCHAR(50) NOT NULL,
        room_type VARCHAR(50) NOT NULL,
        room_size VARCHAR(20),
        room_shape VARCHAR(20),
        color_palette TEXT,
        key_elements TEXT,
        design_concept TEXT,
        image_data TEXT NOT NULL,
        image_format VARCHAR(10) DEFAULT 'png',
        image_width INTEGER DEFAULT 800,
        image_height INTEGER DEFAULT 600,
        generated_by VARCHAR(20) DEFAULT 'gemini',
        api_key_status VARCHAR(20) DEFAULT 'working',
        generation_prompt TEXT,
        usage_count INTEGER DEFAULT 0,
        last_used TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        is_fallback BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create image_generation_process table
    CREATE TABLE image_generation_process (
        id SERIAL PRIMARY KEY,
        process_id VARCHAR(36) UNIQUE NOT NULL,
        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
        original_image_url VARCHAR(500) NOT NULL,
        room_analysis TEXT NOT NULL,
        design_suggestions TEXT NOT NULL,
        generated_images TEXT NOT NULL,
        base64_images TEXT,
        status VARCHAR(20) DEFAULT 'processing',
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    
    -- Create indexes
    CREATE INDEX idx_user_username ON "user"(username);
    CREATE INDEX idx_user_email ON "user"(email);
    CREATE INDEX idx_project_user ON project(user_id);
    CREATE INDEX idx_budget_user ON budget(user_id);
    CREATE INDEX idx_wishlist_user ON wishlist_item(user_id);
    CREATE INDEX idx_feedback_user ON feedback(user_id);
    CREATE INDEX idx_ar_session_id ON ar_sessions(session_id);
    CREATE INDEX idx_ar_placed_session ON ar_placed_models(session_id);
    CREATE INDEX idx_ar_model_lib ON ar_model_library(model_id);
    CREATE INDEX idx_ar_model_category ON ar_model_library(category);
    '''
    
    print("\n[1/2] Creating tables in PostgreSQL...")
    try:
        postgres_conn.execute(text(create_tables_sql))
        postgres_conn.commit()
        print("   Tables created successfully")
    except Exception as e:
        print(f"   Error creating tables: {e}")
        return False
    
    # Tables to migrate with boolean columns
    tables_data = [
        ('"user"', 'user', ['is_verified', 'email_notifications']),
        ('project', 'project', []),
        ('budget', 'budget', []),
        ('wishlist_item', 'wishlist_item', []),
        ('feedback', 'feedback', []),
        ('ar_sessions', 'ar_sessions', ['is_active', 'is_saved']),
        ('ar_placed_models', 'ar_placed_models', []),
        ('ar_model_library', 'ar_model_library', ['is_active', 'is_premium']),
        ('generated_design_templates', 'generated_design_templates', ['is_active', 'is_fallback']),
        ('image_generation_process', 'image_generation_process', [])
    ]
    
    print("\n[2/2] Migrating data...")
    total_migrated = 0
    
    for pg_table, sqlite_table, bool_columns in tables_data:
        result = sqlite_conn.execute(text(f"SELECT * FROM {sqlite_table}"))
        rows = result.fetchall()
        columns = result.keys()
        
        print(f"   {sqlite_table}: {len(rows)} records")
        
        if not rows:
            continue
        
        for row in rows:
            placeholders = ', '.join([f':{col}' for col in columns])
            column_list = ', '.join(columns)
            
            insert_stmt = text(f"INSERT INTO {pg_table} ({column_list}) VALUES ({placeholders})")
            row_dict = dict(zip(columns, row))
            
            # Convert types - integers to booleans for specific columns
            for key, value in row_dict.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
                elif key in bool_columns:
                    # Convert 0/1 to False/True
                    row_dict[key] = bool(value) if value is not None else None
                elif value is None:
                    row_dict[key] = None
            
            try:
                postgres_conn.execute(insert_stmt, row_dict)
            except Exception as e:
                print(f"      Warning: {e}")
        
        postgres_conn.commit()
        total_migrated += len(rows)
    
    print("\n" + "="*60)
    print(f"MIGRATION COMPLETE! Total records: {total_migrated}")
    print("="*60)
    
    sqlite_conn.close()
    postgres_conn.close()
    return True

if __name__ == '__main__':
    success = create_tables_and_migrate()
    sys.exit(0 if success else 1)
