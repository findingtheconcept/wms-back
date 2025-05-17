from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import datetime
import os
import mysql.connector
from mysql.connector import Error
from bd_work import insert_user_data

app = Flask(__name__)
app.secret_key = os.urandom(24) # Для использования сессий (например, для состояния входа)

# --- Database Connection ---
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='warehouse',
            user='root',
            password='0000'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# --- Маршруты для HTML страниц ---
@app.route('/')
def home_redirect():
    if 'user' in session:
        return redirect(url_for('product_list_page'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        # Временная заглушка для логина (можно заменить на проверку в БД пользователей)
        username = request.form.get('username')
        password = request.form.get('password')
        # Simple hardcoded user for demonstration
        if username == "admin" and password == "123":
            session['user'] = username
            return redirect(url_for('product_list_page'))
        else:
            return render_template('login.html', error="Неверный логин или пароль")
    if 'user' in session: # Если уже залогинен, редирект на главную
        return redirect(url_for('product_list_page'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login_page'))

@app.route('/products')
def product_list_page():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', username=session['user'])

@app.route('/operations')
def operations_log_page():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return render_template('operations_log.html', username=session['user'])

@app.route('/reports')
def reports_page():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return render_template('reports.html', username=session['user'])

@app.route('/categories-management')
def categories_management_page():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return render_template('categories.html', username=session['user'])


# --- API эндпоинты ---

# Категории
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, description, num FROM categories")
        categories = cursor.fetchall()
        return jsonify(categories)
    except mysql.connector.Error as e:
        print(f"Error fetching categories: {e}")
        return jsonify({"error": "Error fetching categories"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.json
    if not data or 'name' not in data or not data['name'].strip():
        return jsonify({"error": "Название категории не может быть пустым"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if category already exists
        cursor.execute("SELECT id FROM categories WHERE name = %s", (data["name"].strip(),))
        if cursor.fetchone():
             return jsonify({"error": "Категория с таким названием уже существует"}), 409 # Conflict

        insert_query = "INSERT INTO categories (name, description, num) VALUES (%s, %s, %s)"
        # Assuming description is optional and num starts at 0
        description = data.get("description", "")
        cursor.execute(insert_query, (data["name"].strip(), description, 0))
        conn.commit()
        # Get the ID of the newly inserted category
        new_category_id = cursor.lastrowid
        # Fetch the newly created category to return it
        cursor.execute("SELECT id, name, description, num FROM categories WHERE id = %s", (new_category_id,))
        new_category = cursor.fetchone()
        return jsonify(new_category), 201
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error adding category: {e}")
        return jsonify({"error": "Error adding category"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.json
    if not data or 'name' not in data or not data['name'].strip():
        return jsonify({"error": "Название категории не может быть пустым"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if category exists
        cursor.execute("SELECT id, name, description, num FROM categories WHERE id = %s", (category_id,))
        category = cursor.fetchone()
        if not category:
            return jsonify({"error": "Категория не найдена"}), 404

        # Check for duplicate name (if changing name)
        if data['name'].strip() != category['name']:
             cursor.execute("SELECT id FROM categories WHERE name = %s AND id != %s", (data["name"].strip(), category_id))
             if cursor.fetchone():
                return jsonify({"error": "Категория с таким названием уже существует"}), 409 # Conflict

        # Assuming description can also be updated
        description = data.get("description", category.get("description", ""))

        update_query = "UPDATE categories SET name = %s, description = %s WHERE id = %s"
        cursor.execute(update_query, (data["name"].strip(), description, category_id))
        conn.commit()

        # Fetch the updated category to return it
        cursor.execute("SELECT id, name, description, num FROM categories WHERE id = %s", (category_id,))
        updated_category = cursor.fetchone()

        return jsonify(updated_category)
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error updating category: {e}")
        return jsonify({"error": "Error updating category"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        # Check if category exists
        cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Категория не найдена"}), 404

        # Check for associated products
        cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = %s", (category_id,))
        product_count = cursor.fetchone()[0]
        if product_count > 0:
            return jsonify({"error": "Нельзя удалить категорию, так как она используется товарами"}), 400

        delete_query = "DELETE FROM categories WHERE id = %s"
        cursor.execute(delete_query, (category_id,))
        conn.commit()
        return jsonify({"message": "Категория удалена"}), 200
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error deleting category: {e}")
        return jsonify({"error": "Error deleting category"}), 500
    finally:
        cursor.close()
        conn.close()

# Товары
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                p.id, p.name, p.category_id, c.name as category_name,
                p.unit, p.location, p.min_stock, p.current_stock, p.description
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
        """)
        products = cursor.fetchall()
        return jsonify(products)
    except mysql.connector.Error as e:
        print(f"Error fetching products: {e}")
        return jsonify({"error": "Error fetching products"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    required_fields = ['name', 'category_id', 'unit', 'min_stock', 'description', 'location']
    for field in required_fields:
         if field not in data or (isinstance(data[field], str) and not data[field].strip()):
             return jsonify({"error": f"Поле '{field}' обязательно для заполнения"}), 400

    # Получаем данные от json объекта, разделяем на парметры
    insert_name =  data["name"].strip() # имя товара
    insert_category = data["category_id"].strip() # категория
    insert_measure = data["unit"].strip() # единицы измерения
    insert_description = data["description"].strip() # описание (может быть пустым)
    insert_position = data["location"].strip() # расположение
    insert_minimum_to_warn = data["min_stock"].strip() # минимальный остаток для уведомления
    # insert_current_stock = data.get("current_stock", 0) # пока что нигде не хранится
    
    # Добавляем в базу данных
    message = insert_user_data(insert_name, insert_category, insert_measure, insert_description, insert_position, insert_minimum_to_warn)
    if message == "Данные успешно добавлены.":
        return jsonify({"id": 201})
    else:
        return jsonify({"error": message})

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                p.id, p.name, p.category_id, c.name as category_name,
                p.unit, p.location, p.min_stock, p.current_stock, p.description
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        """, (product_id,))
        product = cursor.fetchone()
        if product:
            return jsonify(product)
        return jsonify({"error": "Товар не найден"}), 404
    except mysql.connector.Error as e:
        print(f"Error fetching product: {e}")
        return jsonify({"error": "Error fetching product"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if product exists
        cursor.execute("SELECT id, category_id FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({"error": "Товар не найден"}), 404

        # Check if category_id is valid if provided
        if 'category_id' in data:
            cursor.execute("SELECT id FROM categories WHERE id = %s", (data["category_id"],))
            if not cursor.fetchone():
                return jsonify({"error": "Указанная категория не найдена"}), 400

        update_fields = []
        update_values = []
        # Build update query dynamically based on provided data
        if 'name' in data:
            update_fields.append("name = %s")
            update_values.append(data['name'].strip())
        if 'category_id' in data:
            update_fields.append("category_id = %s")
            update_values.append(data['category_id'])
        if 'unit' in data:
            update_fields.append("unit = %s")
            update_values.append(data['unit'].strip())
        if 'location' in data:
            update_fields.append("location = %s")
            update_values.append(data['location'].strip())
        if 'min_stock' in data:
            update_fields.append("min_stock = %s")
            update_values.append(int(data['min_stock']))
        if 'current_stock' in data:
             update_fields.append("current_stock = %s")
             update_values.append(int(data['current_stock']))
        if 'description' in data:
            update_fields.append("description = %s")
            update_values.append(data['description'].strip())


        if not update_fields:
            return jsonify({"message": "Нет данных для обновления"}), 200

        update_query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(product_id)

        cursor.execute(update_query, tuple(update_values))
        conn.commit()

        # Fetch the updated product with category name to return it
        cursor.execute("""
            SELECT
                p.id, p.name, p.category_id, c.name as category_name,
                p.unit, p.location, p.min_stock, p.current_stock, p.description
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        """, (product_id,))
        updated_product = cursor.fetchone()

        return jsonify(updated_product)
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error updating product: {e}")
        return jsonify({"error": "Error updating product"}), 500
    except ValueError:
         return jsonify({"error": "Неверный формат числового поля"}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Товар не найден"}), 404

        # Optional: Check for related operations before deleting (depends on desired behavior)
        # cursor.execute("SELECT COUNT(*) FROM operations WHERE product_id = %s", (product_id,))
        # operation_count = cursor.fetchone()[0]
        # if operation_count > 0:
        #     return jsonify({"error": "Нельзя удалить товар, так как есть связанные операции"}), 400


        delete_query = "DELETE FROM products WHERE id = %s"
        cursor.execute(delete_query, (product_id,))
        conn.commit()
        return jsonify({"message": "Товар удален"}), 200
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error deleting product: {e}")
        return jsonify({"error": "Error deleting product"}), 500
    finally:
        cursor.close()
        conn.close()

# Операции
@app.route('/api/operations', methods=['GET'])
def get_operations():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch operations with product name, ordered by date
        cursor.execute("""
            SELECT
                o.id, o.date, o.type, o.product_id, p.name as product_name,
                o.quantity, o.invoice_number, o.party, o.comment
            FROM operations o
            LEFT JOIN products p ON o.product_id = p.id
            ORDER BY o.date DESC
        """)
        operations = cursor.fetchall()
        return jsonify(operations)
    except mysql.connector.Error as e:
        print(f"Error fetching operations: {e}")
        return jsonify({"error": "Error fetching operations"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/operations/register', methods=['POST'])
def register_operation():
    data = request.json
    required_fields = ['type', 'product_id', 'quantity']
    for field in required_fields:
         if field not in data or (isinstance(data[field], str) and not data[field].strip()):
             return jsonify({"error": f"Поле '{field}' обязательно для заполнения"}), 400

    op_type = data.get('type') # "Поступление" or "Отгрузка"
    product_id = data.get('product_id')
    quantity = int(data.get('quantity'))

    if op_type not in ["Поступление", "Отгрузка"]:
         return jsonify({"error": "Неверный тип операции. Должен быть 'Поступление' или 'Отгрузка'"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if product exists and get current stock
        cursor.execute("SELECT id, name, current_stock FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({"error": "Товар не найден"}), 404

        if op_type == "Отгрузка" and product["current_stock"] < quantity:
            return jsonify({"error": f"Недостаточно товара '{product['name']}' на складе. В наличии: {product['current_stock']}"}), 400

        # Insert operation
        insert_operation_query = """
            INSERT INTO operations (date, type, product_id, quantity, invoice_number, party, comment)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        # Use provided date or current time
        op_date = data.get("date", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        invoice_number = data.get("invoice_number", "")
        party = data.get("party", "")
        comment = data.get("comment", "")

        operation_data = (
            op_date,
            op_type,
            product_id,
            quantity,
            invoice_number.strip(),
            party.strip(),
            comment.strip()
        )
        cursor.execute(insert_operation_query, operation_data)

        # Update product stock
        new_stock = product["current_stock"] + quantity if op_type == "Поступление" else product["current_stock"] - quantity
        update_stock_query = "UPDATE products SET current_stock = %s WHERE id = %s"
        cursor.execute(update_stock_query, (new_stock, product_id))

        conn.commit()

        # Fetch the newly created operation with product name to return it
        new_operation_id = cursor.lastrowid
        cursor.execute("""
            SELECT
                o.id, o.date, o.type, o.product_id, p.name as product_name,
                o.quantity, o.invoice_number, o.party, o.comment
            FROM operations o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.id = %s
        """, (new_operation_id,))
        new_operation_with_details = cursor.fetchone()


        return jsonify(new_operation_with_details), 201
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error registering operation: {e}")
        return jsonify({"error": "Error registering operation"}), 500
    except ValueError:
         return jsonify({"error": "Количество товара должно быть числом"}), 400
    finally:
        cursor.close()
        conn.close()

# Отчеты
@app.route('/api/reports/<report_type>', methods=['GET'])
def get_report(report_type):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        if report_type == "current_stock_all":
            cursor.execute("""
                SELECT
                    p.name as Наименование, c.name as Категория, p.unit as `Ед. изм.`,
                    p.location as `Место хранения`, p.min_stock as `Мин. остаток`,
                    p.current_stock as `Текущий остаток`
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
            """)
            data = cursor.fetchall()
            columns = list(data[0].keys()) if data else []
            return jsonify({"title": "Текущие остатки всех товаров", "data": data, "columns": columns})

        elif report_type == "low_stock":
            cursor.execute("""
                SELECT
                    p.name as Наименование, c.name as Категория,
                    p.min_stock as `Мин. остаток`, p.current_stock as `Текущий остаток`,
                    (p.min_stock - p.current_stock) as `Требуется закупка`
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.current_stock < p.min_stock
            """)
            data = cursor.fetchall()
            columns = list(data[0].keys()) if data else []
            return jsonify({"title": "Товары с остатком ниже минимального", "data": data, "columns": columns})

        elif report_type == "operations_period":
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')

            if not start_date_str or not end_date_str:
                 return jsonify({"error": "Необходимо указать начальную и конечную дату"}), 400

            try:
                start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
                end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                 return jsonify({"error": "Неверный формат даты. Используйте ГГГГ-ММ-ДД."}), 400

            cursor.execute("""
                SELECT
                    o.date as Дата, o.type as Тип, p.name as Товар,
                    o.quantity as Количество, o.invoice_number as `Номер накладной`,
                    o.party as `Поставщик/Получатель`, o.comment as Комментарий
                FROM operations o
                LEFT JOIN products p ON o.product_id = p.id
                WHERE o.date BETWEEN %s AND %s
                ORDER BY o.date DESC
            """, (start_date, end_date))
            data = cursor.fetchall()
            columns = list(data[0].keys()) if data else []
            return jsonify({"title": f"Операции за период с {start_date_str} по {end_date_str}", "data": data, "columns": columns})

        elif report_type == "product_movement_period":
            product_id = request.args.get('product_id', type=int)
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')

            if not product_id or not start_date_str or not end_date_str:
                 return jsonify({"error": "Необходимо указать товар, начальную и конечную дату"}), 400

            try:
                start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
                end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                 return jsonify({"error": "Неверный формат даты. Используйте ГГГГ-ММ-ДД."}), 400

            # Check if product exists
            cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            if not product:
                return jsonify({"error": "Товар не найден"}), 404

            cursor.execute("""
                SELECT
                    o.date as Дата, o.type as Тип, o.quantity as Количество,
                    o.invoice_number as `Номер накладной`, o.party as `Поставщик/Получатель`, o.comment as Комментарий
                FROM operations o
                WHERE o.product_id = %s AND o.date BETWEEN %s AND %s
                ORDER BY o.date DESC
            """, (product_id, start_date, end_date))
            data = cursor.fetchall()
            columns = list(data[0].keys()) if data else []
            return jsonify({"title": f"Движение товара '{product['name']}' за период с {start_date_str} по {end_date_str}", "data": data, "columns": columns})


        return jsonify({"error": "Тип отчета не найден или не реализован"}), 404
    except mysql.connector.Error as e:
        print(f"Error generating report: {e}")
        return jsonify({"error": "Error generating report"}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)