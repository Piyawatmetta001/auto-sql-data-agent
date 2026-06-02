import sqlite3
import pandas as pd

def init_mock_db():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    
    # Create a sample table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            sales_date DATE NOT NULL
        )
    ''')
    
    # Insert sample data
    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] == 0:  # Only insert data if the table is empty
        sample_data = [
            ('Laptop', 'Electronics', 1200.00, '2024-01-15'),
            ('Smartphone', 'Electronics', 800.00, '2024-01-20'),
            ('Headphones', 'Accessories', 150.00, '2024-01-25'),
            ('Coffee Maker', 'Home Appliances', 100.00, '2024-02-01'),
            ('Blender', 'Home Appliances', 80.00, '2024-02-05')
        ]
        cursor.executemany('''
            INSERT INTO transactions (product_name, category, amount, sales_date)
            VALUES (?, ?, ?, ?)
        ''', sample_data)
        conn.commit()
    conn.close()