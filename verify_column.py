import sqlite3

def verify_cliente_id_column():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Verificar a estrutura da tabela 'sales'
    cursor.execute('PRAGMA table_info(sales)')
    columns = cursor.fetchall()
    conn.close()

    # Verificar se a coluna 'cliente_id' existe
    for column in columns:
        if column[1] == 'cliente_id':
            print("A coluna 'cliente_id' foi adicionada com sucesso.")
            return

    print("A coluna 'cliente_id' não foi encontrada.")

# Execute a função para verificar a coluna
verify_cliente_id_column()
