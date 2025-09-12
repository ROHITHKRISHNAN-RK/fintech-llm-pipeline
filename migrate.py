import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables for local testing.
load_dotenv()

# Get the database connection string from environment variables.
DATABASE_URL = os.getenv("DATABASE_URL")

def run_migrations():
    """
    Connects to the database and runs the SQL schema script.
    """
    if not DATABASE_URL:
        print("DATABASE_URL environment variable is not set.")
        return

    try:
        # Connect to the PostgreSQL database using the DATABASE_URL.
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        print("Successfully connected to the database. Running schema script...")
        
        # Read the SQL from the schema.sql file.
        with open('schema.sql', 'r') as f:
            sql_script = f.read()
        
        # Execute the SQL script.
        cursor.execute(sql_script)
        
        # Commit the changes to the database.
        conn.commit()
        print("Schema created successfully!")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        # Rollback the transaction if there was an error.
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close the connection.
        if conn:
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    run_migrations()
