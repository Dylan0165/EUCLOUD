"""
Database migration script to add app_type column to files table
and migrate existing files to user-based directory structure.

Run this script ONCE after deploying the updated backend.
"""
import os
import sys
import shutil
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from models import engine, get_db, File
from config import Config

def add_app_type_column():
    """Add app_type column to files table if it doesn't exist"""
    print("Checking for app_type column...")
    
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('files')]
    
    if 'app_type' not in columns:
        print("Adding app_type column to files table...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE files ADD COLUMN app_type VARCHAR(50) DEFAULT 'generic'"))
            conn.commit()
        print("✅ app_type column added successfully")
    else:
        print("✅ app_type column already exists")

def migrate_file_storage():
    """
    Migrate existing files from old structure (uploads/{uuid}_{filename})
    to new structure (uploads/{owner_id}/{uuid}.ext)
    """
    print("\nMigrating file storage structure...")
    
    db = next(get_db())
    files = db.query(File).filter_by(is_deleted=False).all()
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for file in files:
        try:
            # Check if already migrated (path contains owner_id directory)
            if '/' in file.file_path and file.file_path.split('/')[0].isdigit():
                print(f"⏭️  Skipping {file.filename} (already migrated)")
                skipped_count += 1
                continue
            
            # Old path format: uploads/{uuid}_{filename}
            old_path = os.path.join(Config.UPLOAD_FOLDER, file.file_path)
            
            if not os.path.exists(old_path):
                print(f"⚠️  File not found on disk: {file.filename}")
                error_count += 1
                continue
            
            # Extract extension from original filename
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            
            # Generate new path: uploads/{owner_id}/{uuid}.ext
            file_id = file.file_path.split('_')[0]  # Extract UUID from old format
            new_filename = f"{file_id}.{ext}" if ext else file_id
            
            # Create user directory
            user_dir = os.path.join(Config.UPLOAD_FOLDER, str(file.owner_id))
            os.makedirs(user_dir, exist_ok=True)
            
            new_path = os.path.join(user_dir, new_filename)
            relative_path = f"{file.owner_id}/{new_filename}"
            
            # Move file
            shutil.move(old_path, new_path)
            
            # Update database
            file.file_path = relative_path
            
            print(f"✅ Migrated: {file.filename}")
            print(f"   Old: {old_path}")
            print(f"   New: {new_path}")
            
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ Error migrating {file.filename}: {str(e)}")
            error_count += 1
    
    # Commit all changes
    try:
        db.commit()
        print(f"\n✅ Database updated successfully")
    except Exception as e:
        print(f"❌ Error committing changes: {str(e)}")
        db.rollback()
    
    print(f"\n📊 Migration Summary:")
    print(f"   Migrated: {migrated_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Errors: {error_count}")
    print(f"   Total: {len(files)}")

def set_default_app_types():
    """Set app_type based on file extension for existing files"""
    print("\nSetting default app_types...")
    
    db = next(get_db())
    files = db.query(File).all()
    
    updated_count = 0
    
    for file in files:
        if file.filename.endswith('.ty'):
            file.app_type = 'eutype'
            updated_count += 1
        elif not file.app_type or file.app_type == 'generic':
            file.app_type = 'generic'
    
    db.commit()
    print(f"✅ Updated app_type for {updated_count} files")

def main():
    print("=" * 60)
    print("EU-CORE-BACKEND Database Migration")
    print("=" * 60)
    
    try:
        # Step 1: Add app_type column
        add_app_type_column()
        
        # Step 2: Migrate file storage structure
        migrate_file_storage()
        
        # Step 3: Set default app types
        set_default_app_types()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Test file upload/download/content endpoints")
        print("2. Verify CORS settings for EuType (port 30081)")
        print("3. Restart the backend service")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
