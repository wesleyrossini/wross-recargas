from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'wross123'  # Chave secreta para mensagens flash

# Função para obter conexão com o banco de dados
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Rota para a página inicial
@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template('index.html', products=products)

# Rota para a página de produtos
@app.route('/produtos')
def produtos():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template('produtos.html', products=products)

# Rota para adicionar um novo produto
@app.route('/add_product', methods=['POST'])
def add_product():
    if request.method == 'POST':
        product_name = request.form['product_name']
        price = request.form['price']
        logo = request.form['logo']

        conn = get_db_connection()
        conn.execute("INSERT INTO products (name, price, logo) VALUES (?, ?, ?)", (product_name, price, logo))
        conn.commit()
        conn.close()

        flash(f'O produto "{product_name}" foi adicionado com sucesso!', 'success')
    return redirect(url_for('produtos'))

# Rota para deletar um produto
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    flash('Produto deletado com sucesso!', 'success')
    return redirect(url_for('produtos'))

# Rota para editar um produto
@app.route('/edit_product/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    if request.method == 'POST':
        product_name = request.form['product_name']
        price = request.form['price']
        logo = request.form['logo']

        conn = get_db_connection()
        conn.execute('UPDATE products SET name = ?, price = ?, logo = ? WHERE id = ?', (product_name, price, logo, product_id))
        conn.commit()
        conn.close()

        flash(f'O produto "{product_name}" foi atualizado com sucesso!', 'success')
    return redirect(url_for('produtos'))

# Rota para a página de vendas (GET)
@app.route('/vendas', methods=['GET'])
def vendas():
    conn = get_db_connection()
    sales_data = conn.execute(
        "SELECT sales.id, products.name AS product_name, products.logo AS logo, sales.quantity, revendedores.nome AS revendedor, sales.sale_date "
        "FROM sales "
        "INNER JOIN products ON sales.product_id = products.id "
        "INNER JOIN revendedores ON sales.revendedor_id = revendedores.id"
    ).fetchall()
    products = conn.execute("SELECT * FROM products").fetchall()
    revendedores = conn.execute("SELECT * FROM revendedores").fetchall()
    conn.close()
    return render_template('vendas.html', sales=sales_data, products=products, revendedores=revendedores)

# Rota para adicionar uma nova venda (POST)
@app.route('/add_sale', methods=['POST'])
def add_sale():
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = request.form['quantity']
        revendedor_id = request.form['revendedor_id']
        sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        conn.execute("INSERT INTO sales (product_id, quantity, revendedor_id, sale_date) VALUES (?, ?, ?, ?)",
                     (product_id, quantity, revendedor_id, sale_date))
        conn.commit()
        conn.close()

        flash('Venda adicionada com sucesso!', 'success')
    return redirect(url_for('vendas'))

# Rota para deletar uma venda
@app.route('/delete_sale/<int:sale_id>', methods=['POST'])
def delete_sale(sale_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM sales WHERE id = ?', (sale_id,))
    conn.commit()
    conn.close()
    flash('Venda deletada com sucesso!', 'success')
    return redirect(url_for('relatorios'))

@app.route('/relatorios', methods=['GET'])
def relatorios():
    product_filter = request.args.get('product_filter', type=int)
    revendedor_filter = request.args.get('revendedor_filter', type=int)
    
    query = """
        SELECT sales.id, products.name AS product_name, sales.quantity, revendedores.nome AS revendedor, sales.sale_date, 
               (sales.quantity * products.price) AS total_value
        FROM sales 
        INNER JOIN products ON sales.product_id = products.id 
        INNER JOIN revendedores ON sales.revendedor_id = revendedores.id
    """
    conditions = []
    params = []
    
    if product_filter:
        conditions.append("sales.product_id = ?")
        params.append(product_filter)
    
    if revendedor_filter:
        conditions.append("sales.revendedor_id = ?")
        params.append(revendedor_filter)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    conn = get_db_connection()
    sales_data = conn.execute(query, params).fetchall()
    products = conn.execute("SELECT * FROM products").fetchall()
    revendedores = conn.execute("SELECT * FROM revendedores").fetchall()
    conn.close()
    
    total_quantities = sum([sale['quantity'] for sale in sales_data])
    total_values = sum([sale['total_value'] for sale in sales_data])
    
    return render_template('relatorios.html', sales=sales_data, products=products, revendedores=revendedores, total_quantities=total_quantities, total_values=total_values)

# Rota para exportar vendas para um arquivo de texto
@app.route('/export_text')
def export_text():
    try:
        conn = get_db_connection()
        sales_data = conn.execute(
            '''SELECT sales.id, products.name AS product_name, sales.quantity, revendedores.nome AS revendedor, sales.sale_date, products.price
               FROM sales
               INNER JOIN products ON sales.product_id = products.id
               INNER JOIN revendedores ON sales.revendedor_id = revendedores.id'''
        ).fetchall()
        conn.close()

        total_sales = sum([sale['quantity'] * float(sale['price'].replace(',', '.')) for sale in sales_data])

        # Organizar dados por revendedor
        revendedores = {}
        for sale in sales_data:
            revendedor = sale['revendedor']
            if revendedor not in revendedores:
                revendedores[revendedor] = {}
            product_name = sale['product_name']
            if product_name not in revendedores[revendedor]:
                revendedores[revendedor][product_name] = 0
            revendedores[revendedor][product_name] += sale['quantity']

        export_file = 'sales_report.txt'
        with open(export_file, 'w', encoding='utf-8') as f:
            f.write("Relatório de Vendas\n\n")
            export_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"Data de Exportação: {export_date}\n\n")

            # Escrever os dados por revendedor
            for revendedor, products in revendedores.items():
                f.write(f"Revendedor: {revendedor}\n")
                f.write("Produto, Quantidade\n")
                for product, quantity in products.items():
                    f.write(f"{product}, {quantity}\n")
                f.write("\n")

            f.write("\n\nDetalhes de Todas as Vendas:\n")
            f.write("Produto, Quantidade, Revendedor, Data da Venda, Valor Total\n")
            for sale in sales_data:
                total_value = float(sale['quantity']) * float(sale['price'].replace(',', '.'))
                f.write(f"{sale['product_name']}, {sale['quantity']}, {sale['revendedor']}, {sale['sale_date']}, R$ {total_value:.2f}\n")

            f.write(f"\nTotal Geral das Vendas: R$ {total_sales:.2f}\n")

        return send_file(export_file, as_attachment=True)

    except Exception as e:
        flash(f"Ocorreu um erro ao exportar os dados: {str(e)}", 'error')
        return redirect(url_for('relatorios'))

# Rota para a página de revendedores
@app.route('/revendedores', methods=['GET', 'POST'])
def revendedores():
    conn = get_db_connection()
    
    if request.method == 'POST':
        revendedor_name = request.form['revendedor_name']
        conn.execute("INSERT INTO revendedores (nome) VALUES (?)", (revendedor_name,))
        conn.commit()
        flash(f'Revendedor "{revendedor_name}" adicionado com sucesso!', 'success')
    
    revendedores = conn.execute("SELECT * FROM revendedores").fetchall()
    conn.close()
    return render_template('revendedores.html', revendedores=revendedores)

# Rota para exibir o histórico de compras de um revendedor
@app.route('/revendedor/<int:revendedor_id>')
def revendedor(revendedor_id):
    conn = get_db_connection()
    revendedor = conn.execute("SELECT * FROM revendedores WHERE id = ?", (revendedor_id,)).fetchone()
    sales = conn.execute(
        "SELECT sales.id, products.name AS product_name, sales.quantity, sales.sale_date, "
        "(sales.quantity * products.price) AS total_value "
        "FROM sales "
        "INNER JOIN products ON sales.product_id = products.id "
        "WHERE sales.revendedor_id = ?", (revendedor_id,)
    ).fetchall()
    conn.close()
    return render_template('revendedor_detalhes.html', revendedor=revendedor, sales=sales)

# Rota para exportar vendas para um arquivo Excel
@app.route('/export_excel')
def export_excel():
    try:
        conn = get_db_connection()
        sales_data = conn.execute(
            '''SELECT sales.id, products.name AS product_name, sales.quantity, revendedores.nome AS revendedor, sales.sale_date, products.price
               FROM sales
               INNER JOIN products ON sales.product_id = products.id
               INNER JOIN revendedores ON sales.revendedor_id = revendedores.id'''
        ).fetchall()
        conn.close()

        # Preparar dados para exportação
        data = {
            "Produto": [sale['product_name'] for sale in sales_data],
            "Quantidade": [sale['quantity'] for sale in sales_data],
            "Revendedor": [sale['revendedor'] for sale in sales_data],
            "Data da Venda": [sale['sale_date'] for sale in sales_data],
            "Valor Total": [float(sale['quantity']) * float(sale['price'].replace(',', '.')) for sale in sales_data]
        }
        
        df = pd.DataFrame(data)
        total_sales = df['Valor Total'].sum()

        # Exportar para Excel
        with pd.ExcelWriter('sales_report.xlsx', engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Detalhes de Vendas', index=False)
            # Adiciona uma célula com o total geral no final do documento Excel
            writer.sheets['Detalhes de Vendas'].cell(row=len(df)+2, column=5, value=f"Total Geral das Vendas: R$ {total_sales:.2f}")

        return send_file('sales_report.xlsx', as_attachment=True)

    except Exception as e:
        flash(f"Erro ao exportar para Excel: {str(e)}", 'error')
        return redirect(url_for('relatorios'))

# Rota para gerar gráficos
@app.route('/graficos')
def graficos():
    conn = get_db_connection()

    # Calcular a média de vendas por produto
    product_sales = conn.execute(
        "SELECT products.name, SUM(sales.quantity) AS total_quantity "
        "FROM sales "
        "INNER JOIN products ON sales.product_id = products.id "
        "GROUP BY products.name"
    ).fetchall()

    # Calcular a média de vendas por revendedor
    revendedor_sales = conn.execute(
        "SELECT revendedores.nome, SUM(sales.quantity) AS total_quantity "
        "FROM sales "
        "INNER JOIN revendedores ON sales.revendedor_id = revendedores.id "
        "GROUP BY revendedores.nome"
    ).fetchall()

    conn.close()

    # Criar gráficos
    product_names = [row['name'] for row in product_sales]
    product_quantities = [row['total_quantity'] for row in product_sales]

    revendedor_names = [row['nome'] for row in revendedor_sales]
    revendedor_quantities = [row['total_quantity'] for row in revendedor_sales]

    # Gráfico de produtos mais vendidos
    plt.figure(figsize=(10, 5))
    plt.bar(product_names, product_quantities, color='blue')
    plt.xlabel('Produtos')
    plt.ylabel('Quantidade Vendida')
    plt.title('Produtos Mais Vendidos')
    plt.xticks(rotation=90)
    plt.tight_layout()  # Ajusta o layout para evitar cortes
    for i, v in enumerate(product_quantities):
        plt.text(i, v + 10, str(v), ha='center', va='bottom')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    product_graph = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    # Gráfico de revendedores que mais compram
    plt.figure(figsize=(10, 5))
    plt.bar(revendedor_names, revendedor_quantities, color='green')
    plt.xlabel('Revendedores')
    plt.ylabel('Quantidade Comprada')
    plt.title('Revendedores que Mais Compram')
    plt.xticks(rotation=90)
    plt.tight_layout()  # Ajusta o layout para evitar cortes
    for i, v in enumerate(revendedor_quantities):
        plt.text(i, v + 10, str(v), ha='center', va='bottom')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    revendedor_graph = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return render_template('graficos.html', product_graph=product_graph, revendedor_graph=revendedor_graph)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
