import sqlite3

def init_db():
    db_file = 'C:\\cadastro de vendas\\database.db'
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    with open('init_db.sql', 'r') as f:
        sql_script = f.read()
    
    c.executescript(sql_script)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Banco de dados inicializado com sucesso.")
