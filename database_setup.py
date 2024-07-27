import sqlite3

# Conectando ao banco de dados
conn = sqlite3.connect('database.db')

# Criando um cursor
cursor = conn.cursor()

# Criando a tabela de produtos
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    logo TEXT
)
''')

# Criando a tabela de vendas
cursor.execute('''
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    buyer TEXT NOT NULL,
    sale_date TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products (id)
)
''')

# Commitando as mudanças e fechando a conexão
conn.commit()
conn.close()
