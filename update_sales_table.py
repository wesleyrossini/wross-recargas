import sqlite3

def update_sales_table():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=off;")
        cursor.execute("BEGIN TRANSACTION;")
        
        cursor.execute("""
        CREATE TABLE sales_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER,
            buyer TEXT DEFAULT NULL,
            cliente_id INTEGER,
            sale_date TEXT
        );
        """)
        
        cursor.execute("""
        INSERT INTO sales_new (id, product_id, quantity, buyer, cliente_id, sale_date)
        SELECT id, product_id, quantity, buyer, cliente_id, sale_date
        FROM sales;
        """)
        
        cursor.execute("DROP TABLE sales;")
        cursor.execute("ALTER TABLE sales_new RENAME TO sales;")
        
        cursor.execute("COMMIT;")
        cursor.execute("PRAGMA foreign_keys=on;")
        
        print("Tabela 'sales' atualizada com sucesso.")
    except Exception as e:
        cursor.execute("ROLLBACK;")
        print(f"Erro ao atualizar a tabela 'sales': {e}")
    finally:
        conn.close()

# Execute a função para atualizar a tabela
update_sales_table()
