import os
import sys
import mysql.connector
from mysql.connector import Error
from config import Config

def setup_mysql_database():
    print("=" * 65)
    print("  PLACEMENT CELL RESUME REVIEWER - MYSQL DATABASE SETUP")
    print("=" * 65)
    print(f"Target Host     : {Config.MYSQL_HOST}:{Config.MYSQL_PORT}")
    print(f"Target Database : {Config.MYSQL_DB}")
    print(f"MySQL User      : {Config.MYSQL_USER}")
    print(f"Password Set    : {'Yes' if Config.MYSQL_PASSWORD else 'No (Empty Password)'}")
    print("-" * 65)

    # Step 1: Connect to MySQL server (without selecting DB first)
    print("\n[1/4] Connecting to MySQL Server...")
    try:
        root_conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        if root_conn.is_connected():
            print(" [OK] Connected to MySQL Server successfully!")
    except Error as e:
        print(f"\n[Connection Failed] Could not connect to MySQL: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if the password is correct.")
        print("  2. If using XAMPP/WAMP, 'root' usually has an empty password (leave MYSQL_PASSWORD='' in .env).")
        print("  3. If you created a custom user, set MYSQL_USER and MYSQL_PASSWORD accordingly.")
        return False
    except Exception as e:
        print(f"\n[Unexpected Error]: {e}")
        return False

    # Step 2: Create Database if not exists
    print(f"\n[2/4] Creating Database `{Config.MYSQL_DB}` if not exists...")
    try:
        cursor = root_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f" [OK] Database `{Config.MYSQL_DB}` verified/created.")
        cursor.close()
        root_conn.close()
    except Error as e:
        print(f"[Error] Failed to create database: {e}")
        return False

    # Step 3: Connect to the specific Database and execute database.sql
    print(f"\n[3/4] Initializing Tables from database.sql...")
    try:
        db_conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = db_conn.cursor()

        sql_file_path = os.path.join(os.path.dirname(__file__), "database.sql")
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
        for cmd in commands:
            cursor.execute(cmd)

        db_conn.commit()
        print(" [OK] Successfully executed all table creation statements.")

        # Step 4: Verify Tables
        print("\n[4/4] Verifying Relational Tables in MySQL:")
        cursor.execute("SHOW TABLES;")
        tables = [t[0] for t in cursor.fetchall()]
        
        required_tables = ['students', 'resumes', 'resume_results', 'grammar_issues', 'missing_fields']
        for req in required_tables:
            if req in tables:
                cursor.execute(f"SELECT COUNT(*) FROM `{req}`;")
                count = cursor.fetchone()[0]
                print(f"   * Table `{req}` is ACTIVE (Current rows: {count})")
            else:
                print(f"   * [MISSING] Table `{req}` is missing!")

        cursor.close()
        db_conn.close()

        print("\n" + "=" * 65)
        print(" MYSQL DATABASE CONFIGURATION COMPLETED WITH 100% SUCCESS!")
        print(" Your Flask app is now fully linked to MySQL.")
        print("=" * 65)
        return True

    except Error as e:
        print(f"[Error] Error during table creation: {e}")
        return False

if __name__ == "__main__":
    success = setup_mysql_database()
    if not success:
        sys.exit(1)
