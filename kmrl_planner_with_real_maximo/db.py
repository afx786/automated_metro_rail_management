# add_bay_columns.py
import sqlite3
import os

def migrate_bays_table():
    db_path = 'kmrl_real_maximo.db'
    
    if not os.path.exists(db_path):
        print("Database doesn't exist yet. It will be created automatically.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Adding missing columns to cleaning_bays table...")
    
    # Check if specialization column exists
    cursor.execute("PRAGMA table_info(cleaning_bays)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    # Add missing columns
    columns_to_add = [
        ('specialization', 'TEXT DEFAULT "general"')
    ]
    
    for column_name, column_type in columns_to_add:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE cleaning_bays ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name}")
            except sqlite3.Error as e:
                print(f"❌ Failed to add {column_name}: {e}")
        else:
            print(f"✅ Column already exists: {column_name}")
    
    # Update existing bays with specialization
    try:
        cursor.execute("UPDATE cleaning_bays SET specialization = 'interior' WHERE bay_number = 'Bay-1'")
        cursor.execute("UPDATE cleaning_bays SET specialization = 'exterior' WHERE bay_number = 'Bay-2'") 
        cursor.execute("UPDATE cleaning_bays SET specialization = 'general' WHERE bay_number = 'Bay-3'")
        print("✅ Updated bay specializations")
    except sqlite3.Error as e:
        print(f"❌ Failed to update specializations: {e}")
    
    conn.commit()
    conn.close()
    print("🎉 Bay table migration completed!")

if __name__ == "__main__":
    migrate_bays_table()