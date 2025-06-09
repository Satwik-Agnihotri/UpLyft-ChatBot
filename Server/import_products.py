import pandas as pd
import sqlite3
import math # Import math to check for NaN values

# --- Configuration ---
DATABASE_NAME = "products.db"
CSV_FILE = "data.csv" # Make sure this file is in the same directory as this script

def import_products():
    conn = None # Initialize conn to None
    try:
        # Step 1: Read the CSV file using pandas
        # Keep 'latin-1' encoding as it seemed to work for the previous UnicodeDecodeError.
        df = pd.read_csv(CSV_FILE, encoding='latin-1')
        print(f"Successfully read {len(df)} rows from {CSV_FILE}")

        # --- DEBUG STEP: Print actual column names recognized by pandas ---
        print("\n--- CSV Columns detected by Pandas ---")
        print(df.columns.tolist()) # Convert to list for cleaner print
        print("--------------------------------------\n")

        # Step 2: Connect to SQLite database
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # Step 3: Create products table if it doesn't exist
        # Ensure column names here match your desired database schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                image_url TEXT
            )
        ''')
        print(f"Table 'products' ensured in {DATABASE_NAME}")

        # Step 4: Insert data into the products table
        imported_count = 0
        skipped_count = 0
        for index, row in df.iterrows():
            # --- IMPORTANT: Map CSV column names to DB schema names EXACTLY ---
            product_name_from_csv = row.get('Description') # Maps to DB's product_name
            price_from_csv = row.get('UnitPrice')        # Maps to DB's price

            # For other DB columns, they are not directly in your CSV, so we set them to None or a default
            # You might want to derive category from Description or StockCode later if needed.
            description_for_db = None # Not available as a separate long description in your CSV
            category_for_db = None    # Not available in your CSV
            image_url_for_db = None   # Not available in your CSV

            # --- Data Validation before insertion (Crucial for NOT NULL constraints) ---
            # Check for missing Description
            if pd.isna(product_name_from_csv) or str(product_name_from_csv).strip() == '':
                print(f"Skipping row {index}: 'Description' (product_name) is missing or empty.")
                skipped_count += 1
                continue # Skip this row

            # Check for missing or invalid UnitPrice
            if pd.isna(price_from_csv):
                print(f"Skipping row {index}: 'UnitPrice' (price) is missing.")
                skipped_count += 1
                continue # Skip this row

            try:
                # Convert price to float. If it's a string that can't be converted, it will raise ValueError.
                price_value = float(price_from_csv)
            except ValueError:
                print(f"Skipping row {index}: 'UnitPrice' ('{price_from_csv}') is not a valid number.")
                skipped_count += 1
                continue # Skip this row
            except TypeError: # Catches cases where price_from_csv might be a list or other unconvertible type
                print(f"Skipping row {index}: 'UnitPrice' has an unexpected type: {type(price_from_csv)}.")
                skipped_count += 1
                continue # Skip this row
            
            # --- Insert Validated Data ---
            cursor.execute('''
                INSERT INTO products (product_name, description, price, category, image_url)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                str(product_name_from_csv).strip(), # Ensure product name is a string and trimmed
                description_for_db,
                price_value,
                category_for_db,
                image_url_for_db
            ))
            imported_count += 1
        
        # Step 5: Commit changes and close connection
        conn.commit()
        print(f"\nImport process completed!")
        print(f"Successfully imported {imported_count} products into {DATABASE_NAME}.")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} rows due to missing/invalid data for NOT NULL columns.")

    except FileNotFoundError:
        print(f"Error: The file '{CSV_FILE}' was not found in the same directory as the script.")
        print("Please ensure 'data.csv' exists and is in the 'Server' folder.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{CSV_FILE}' is empty.")
    except Exception as e:
        print(f"An unexpected error occurred during import: {e}")
        print("Please review your CSV file for unexpected data formats or column issues.")
        if conn: # Attempt to rollback if an error occurs mid-transaction
            conn.rollback()
            print("Database transaction rolled back due to error.")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import_products()

