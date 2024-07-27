import sqlite3

def add_cliente_id_column():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        # Verificar se a coluna 'cliente_id' já existe
        cursor.execute("PRAGMA table_info(sales)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'cliente_id' not in columns:
            # Adicionar a coluna 'cliente_id' na tabela 'sales'
            cursor.execute('ALTER TABLE sales ADD COLUMN cliente_id INTEGER')
            conn.commit()
            print("Coluna 'cliente_id' adicionada com sucesso.")
        else:
            print("Coluna 'cliente_id' já existe.")
        conn.close()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# Execute a função para adicionar a coluna
add_cliente_id_column()
