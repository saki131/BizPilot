import psycopg2
import os

# Neon database connection
DATABASE_URL = "postgresql://neondb_owner:npg_I7YCoVX5ajmL@ep-young-fog-a1v5j4i7-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='delivery_notes' AND column_name='image_filename'
    """)
    
    if cursor.fetchone():
        print("Column 'image_filename' already exists")
    else:
        # Add the column
        cursor.execute("""
            ALTER TABLE delivery_notes 
            ADD COLUMN image_filename VARCHAR(500)
        """)
        conn.commit()
        print("Successfully added 'image_filename' column to delivery_notes table")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
