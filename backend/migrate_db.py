"""
Database migration script to add new columns to existing tables
"""
import sqlite3
import os

db_path = 'instance/eucloud.db'

def migrate():
    """Add new columns to files table"""
    if not os.path.exists(db_path):
        print("Database doesn't exist yet, will be created on first run")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(files)")
    columns = [column[1] for column in cursor.fetchall()]
    
    migrations = []
    
    if 'is_deleted' not in columns:
        migrations.append("ALTER TABLE files ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
    
    if 'deleted_at' not in columns:
        migrations.append("ALTER TABLE files ADD COLUMN deleted_at DATETIME")
    
    if 'is_favorite' not in columns:
        migrations.append("ALTER TABLE files ADD COLUMN is_favorite BOOLEAN DEFAULT 0")
    
    # Execute migrations
    for migration in migrations:
        try:
            cursor.execute(migration)
            print(f"✓ Executed: {migration}")
        except Exception as e:
            print(f"✗ Failed: {migration}")
            print(f"  Error: {e}")
    
    conn.commit()
    conn.close()
    
    if migrations:
        print(f"\n✓ Migration complete! Added {len(migrations)} columns.")
    else:
        print("\n✓ Database is up to date!")

if __name__ == '__main__':
    migrate()
