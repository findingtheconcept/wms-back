from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import datetime
import os
import io

from fpdf import FPDF
from fpdf.fonts import FontFace

import bd_work as db #псевдоним для удобства

app = Flask(__name__)
app.secret_key = os.urandom(24) 
app.config['STATIC_FOLDER'] = 'static'

# --- Маршруты для HTML страниц (без изменений, кроме проверки сессии) ---
def check_auth():
    """Проверяет, залогинен ли пользователь."""
    if 'user' not in session:
        return False
    return True

@app.route('/')
def home_redirect():
    if check_auth():
        return redirect(url_for('product_list_page'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == "admin" and password == "123": # Заглушка
            session['user'] = username
            return redirect(url_for('product_list_page'))
        else:
            return render_template('login.html', error="Неверный логин или пароль")
    if check_auth():
        return redirect(url_for('product_list_page'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login_page'))

@app.route('/products')
def product_list_page():
    if not check_auth(): return redirect(url_for('login_page'))
    return render_template('index.html', username=session['user'])

@app.route('/operations')
def operations_log_page():
    if not check_auth(): return redirect(url_for('login_page'))
    return render_template('operations_log.html', username=session['user'])

@app.route('/reports')
def reports_page():
    if not check_auth(): return redirect(url_for('login_page'))
    return render_template('reports.html', username=session['user'])

@app.route('/categories-management')
def categories_management_page():
    if not check_auth(): return redirect(url_for('login_page'))
    return render_template('categories.html', username=session['user'])


# --- API эндпоинты ---

# Категории
@app.route('/api/categories', methods=['GET'])
def get_categories_api():
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    categories, message = db.db_get_all_categories()
    if "failed" in message or "Ошибка" in message:
        return jsonify({"error": message}), 500
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
def add_category_api():
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    data = request.json
    if not data or 'name' not in data or not data['name'].strip():
        return jsonify({"error": "Название категории не может быть пустым"}), 400
    
    name = data['name'].strip()
    description = data.get("description", "").strip()

    new_category, message = db.db_add_category(name, description)
    if new_category:
        return jsonify(new_category), 201
    elif "уже существует" in message:
         return jsonify({"error": message}), 409 # Conflict
    else:
        return jsonify({"error": message}), 500

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category_api(category_id):
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    data = request.json
    if not data or 'name' not in data or not data['name'].strip():
        return jsonify({"error": "Название категории не может быть пустым"}), 400

    name = data['name'].strip()
    description = data.get("description", "").strip()

    updated_category, message = db.db_update_category(category_id, name, description)
    if updated_category:
        return jsonify(updated_category)
    elif "уже существует" in message:
        return jsonify({"error": message}), 409
    elif "не найдена" in message:
        return jsonify({"error": message}), 404
    else:
        return jsonify({"error": message}), 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category_api(category_id):
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    success, message = db.db_delete_category(category_id)
    if success:
        return jsonify({"message": message}), 200
    elif "используется товарами" in message:
        return jsonify({"error": message}), 400
    elif "не найдена" in message:
        return jsonify({"error": message}), 404
    else:
        return jsonify({"error": message}), 500

# Товары
@app.route('/api/products', methods=['GET'])
def get_products_api():
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    products, message = db.db_get_all_products()
    if "failed" in message or "Ошибка" in message:
        return jsonify({"error": message}), 500
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_api(product_id):
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    product, message = db.db_get_product_by_id(product_id)
    if product:
        return jsonify(product)
    elif "не найден" in message:
        return jsonify({"error": message}), 404
    else:
        return jsonify({"error": message}), 500
    
@app.route('/api/products', methods=['POST'])
def add_product_api():
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    data = request.json
    required_fields = ['name', 'category_id', 'unit', 'min_stock']
    for field in required_fields:
         if field not in data or \
           (isinstance(data[field], str) and not data[field].strip()) or \
           (field == 'category_id' and (data[field] is None or str(data[field]).strip() == "")) or \
           (field == 'min_stock' and (data[field] is None or str(data[field]).strip() == "")): 
             return jsonify({"error": f"Поле '{field}' обязательно для заполнения и не может быть пустым"}), 400
    try:
        name = data["name"].strip()
        category_id = int(data["category_id"]) 
        unit = data["unit"].strip()
        description = data.get("description", "").strip()
        location = data.get("location", "").strip()
        min_stock = int(data["min_stock"])
        current_stock = int(data.get("current_stock", 0)) # По умолчанию 0 при создании
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Неверный формат данных для одного из полей: {e}"}), 400

    new_product, message = db.db_add_product(name, category_id, unit, description, location, min_stock, current_stock)
    
    if new_product:
        return jsonify(new_product), 201
    elif "уже существует" in message:
        return jsonify({"error": message}), 409
    elif "не найдена" in message:
        return jsonify({"error": message}), 400
    else:
        return jsonify({"error": message}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product_api(product_id):
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    data = request.json
    # Проверка наличия хотя бы одного поля для обновления
    if not data:
        return jsonify({"error": "Нет данных для обновления"}), 400
    
    # Загружаем текущие данные товара, чтобы частично обновлять
    current_product, _ = db.db_get_product_by_id(product_id)
    if not current_product:
        return jsonify({"error": "Товар не найден"}), 404

    try:
        name = data.get("name", current_product["name"]).strip()
        category_id = int(data.get("category_id", current_product["category_id"]))
        unit = data.get("unit", current_product["unit"]).strip()
        description = data.get("description", current_product["description"]).strip()
        location = data.get("location", current_product["location"]).strip()
        min_stock = int(data.get("min_stock", current_product["min_stock"]))
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Неверный формат данных для одного из полей: {e}"}), 400
    
    if not name or not unit: 
         return jsonify({"error": "Поля 'name' и 'unit' не могут быть пустыми"}), 400


    updated_product, message = db.db_update_product(product_id, name, category_id, unit, description, location, min_stock)
    
    if updated_product:
        return jsonify(updated_product)
    elif "уже существует" in message: 
        return jsonify({"error": message}), 409
    elif "не найдена" in message: 
        return jsonify({"error": message}), 404 if "Товар" in message else 400
    else:
        return jsonify({"error": message}), 500


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product_api(product_id):
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    success, message = db.db_delete_product(product_id)
    if success:
        return jsonify({"message": message}), 200
    elif "не найден" in message:
        return jsonify({"error": message}), 404
    else:
        return jsonify({"error": message}), 500


# Операции
@app.route('/api/operations', methods=['GET'])
def get_operations_api():
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    operations, message = db.db_get_all_operations() 
    if "failed" in message or "Ошибка" in message:
        return jsonify({"error": message}), 500
    return jsonify(operations)


@app.route('/api/operations/register', methods=['POST'])
def register_operation_api():
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    data = request.json
    required_fields = ['type', 'product_id', 'quantity']
    for field in required_fields:
         if field not in data or (isinstance(data[field], str) and not str(data[field]).strip()):
             return jsonify({"error": f"Поле '{field}' обязательно для заполнения"}), 400

    op_type = data.get('type')
    product_id_str = data.get('product_id')
    quantity_str = data.get('quantity')

    if op_type not in ["Поступление", "Отгрузка"]:
         return jsonify({"error": "Неверный тип операции. Должен быть 'Поступление' или 'Отгрузка'"}), 400

    try:
        product_id = int(product_id_str)
        quantity = int(quantity_str)
        if quantity <= 0:
            return jsonify({"error": "Количество товара должно быть положительным числом"}), 400
    except (ValueError, TypeError):
         return jsonify({"error": "ID товара и количество должны быть числами"}), 400

    op_date_str = data.get("date") 
    invoice_number = data.get("invoice_number", "")
    party = data.get("party", "") # Поставщик или получатель
    comment = data.get("comment", "")

    new_operation, message = db.db_register_operation(
        op_type, product_id, quantity, op_date_str, invoice_number, party, comment
    )

    if new_operation:
        return jsonify(new_operation), 201
    elif "Недостаточно товара" in message:
        return jsonify({"error": message}), 400
    elif "Товар не найден" in message:
        return jsonify({"error": message}), 404
    elif "Неверный формат даты" in message:
        return jsonify({"error": message}), 400
    else:
        return jsonify({"error": message}), 500
    

@app.route('/api/operations/clear', methods=['DELETE'])
def clear_operations_log_api():
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    
    # Дополнительная проверка, например, роли администратора
    # if session.get('role') != 'admin':
    #     return jsonify({"error": "Недостаточно прав для выполнения этой операции"}), 403

    success, message = db.db_clear_operations_log()
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500

# Отчеты
def _fetch_report_data(report_type_param, request_args):
    """Вспомогательная функция для получения данных отчета."""
    data_list = []
    columns_list = []
    report_title_str = ""
    message_str = ""
    status_code_int = 500

    if report_type_param == "current_stock_all":
        data_list, columns_list, message_str = db.db_report_current_stock_all()
        report_title_str = "Текущие остатки всех товаров"
        status_code_int = 200
    elif report_type_param == "low_stock":
        data_list, columns_list, message_str = db.db_report_low_stock()
        report_title_str = "Товары с остатком ниже минимального"
        status_code_int = 200
    elif report_type_param == "operations_period":
        start_date_str = request_args.get('start_date')
        end_date_str = request_args.get('end_date')
        if not start_date_str or not end_date_str:
            return None, None, None, "Необходимо указать начальную и конечную дату", 400
        data_list, columns_list, message_str = db.db_report_operations_period(start_date_str, end_date_str)
        if "Неверный формат даты" in message_str:
            return None, None, None, message_str, 400
        report_title_str = f"Операции за период с {start_date_str} по {end_date_str}"
        status_code_int = 200
    elif report_type_param == "product_movement_period":
        product_id_str = request_args.get('product_id')
        start_date_str = request_args.get('start_date')
        end_date_str = request_args.get('end_date')
        if not product_id_str or not start_date_str or not end_date_str:
            return None, None, None, "Необходимо указать товар, начальную и конечную дату", 400
        try:
            product_id = int(product_id_str)
        except ValueError:
            return None, None, None, "ID товара должен быть числом", 400
        
        data_list, columns_list, product_name, message_str = db.db_report_product_movement_period(product_id, start_date_str, end_date_str)
        if "Неверный формат даты" in message_str:
            return None, None, None, message_str, 400
        if "Товар не найден" in message_str:
            return None, None, None, message_str, 404
        report_title_str = f"Движение товара '{product_name}' за период с {start_date_str} по {end_date_str}"
        status_code_int = 200
    else:
        return None, None, None, "Тип отчета не найден или не реализован", 404

    if "Ошибка отчета" in message_str or "failed" in message_str : # Проверяем ошибки из DB функций
         return data_list, columns_list, report_title_str, message_str, 500

    return data_list, columns_list, report_title_str, message_str, status_code_int


@app.route('/api/reports/<report_type>', methods=['GET'])
def get_report_api(report_type):
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401
    
    data_list, columns_list, report_title_str, message_str, status_code_int = _fetch_report_data(report_type, request.args)

    if status_code_int != 200:
        return jsonify({"error": message_str}), status_code_int
    
    return jsonify({"title": report_title_str, "data": data_list, "columns": columns_list, "message": message_str}), 200

@app.route('/api/reports/<report_type>/pdf', methods=['GET'])
def get_report_pdf_api(report_type):
    if not check_auth(): return jsonify({"error": "Требуется авторизация"}), 401

    data_list, columns_list, report_title_str, message_str, status_code_int = _fetch_report_data(report_type, request.args)

    if status_code_int != 200:
        return jsonify({"error": message_str}), status_code_int

    if not data_list: # Проверяем, есть ли вообще данные для отчета
        if status_code_int == 200:
            return jsonify({"error": "Нет данных для формирования PDF отчета (отчет пуст)."}), 404
        else:
             return jsonify({"error": message_str}), status_code_int


    pdf = ReportPDF(orientation="L", unit="mm", format="A4")
    pdf.report_title = report_title_str
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.alias_nb_pages() 

    if data_list and not columns_list:
        columns_list = list(data_list[0].keys()) if data_list else []
        if not columns_list: # Если все еще нет колонок
             return jsonify({"error": "Не удалось определить колонки для PDF отчета."}), 500


    pdf.table_header(columns_list)
    pdf.table_body(data_list, columns_list)

    pdf_buffer = io.BytesIO()
    try:
        # pdf.output() с объектом BytesIO в качестве первого аргумента
        # запишет бинарные данные PDF напрямую в этот буфер.
        pdf.output(pdf_buffer) 
    except Exception as e_pdf_output:
        print(f"Ошибка при выводе PDF в BytesIO: {e_pdf_output}")
        return jsonify({"error": f"Ошибка сервера при генерации PDF: {e_pdf_output}"}), 500
    
    pdf_buffer.seek(0)

    safe_title = "".join([c if c.isalnum() else "_" for c in report_title_str])
    if not safe_title:
        safe_title = "report"

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{safe_title}_{report_type}.pdf'
    )

class ReportPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cyrillic_font_loaded = False
        try:
            self.add_font("DejaVu", "", "DejaVuSansCondensed.ttf", uni=True)
            self.add_font("DejaVu", "B", "DejaVuSansCondensed-Bold.ttf", uni=True)
            self.set_font("DejaVu", "", 10) # Устанавливаем шрифт по умолчанию сразу
            self.current_font_family = "DejaVu" # Сохраняем имя семейства
            self.cyrillic_font_loaded = True
            print("Шрифт DejaVu успешно загружен.")
        except RuntimeError as e:
            print(f"Ошибка добавления шрифта DejaVu: {e}. Попытка использовать Arial.")
            try:
                 self.add_font("Arial", "", "arial.ttf", uni=True) 
                 self.add_font("Arial", "B", "arialbd.ttf", uni=True)
                 self.set_font("Arial", "", 10)
                 self.current_font_family = "Arial"
                 self.cyrillic_font_loaded = True 
                 print("Шрифт Arial успешно загружен.")
            except RuntimeError as e_arial:
                print(f"Ошибка добавления шрифта Arial: {e_arial}. PDF может некорректно отображать кириллицу.")
                self.set_font("Helvetica", "", 10)
                self.current_font_family = "Helvetica"
                self.cyrillic_font_loaded = False
                print("Используется стандартный шрифт Helvetica. Кириллица не будет отображаться корректно.")

    def header(self):
        if hasattr(self, 'report_title') and self.report_title:
            self.set_font(self.current_font_family, "B", 14) # Используем сохраненное семейство
            self.cell(0, 10, self.report_title, 0, 1, "C")
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.current_font_family, "", 8) 
        self.cell(0, 10, f"Страница {self.page_no()}/{{nb}}", 0, 0, "C")

    def table_header(self, columns):
        self.set_font(self.current_font_family, "B", 9) 
        self.set_fill_color(230, 230, 230)
        effective_page_width = self.w - 2 * self.l_margin
        num_columns = len(columns)
        col_width = effective_page_width / num_columns if num_columns > 0 else effective_page_width

        for col_name in columns:
            self.multi_cell(col_width, 7, str(col_name), border=1, align="C", fill=True, new_x="RIGHT", new_y="TOP", max_line_height=7)
        self.ln()


    def table_body(self, data, columns_data_keys):
        self.set_font(self.current_font_family, "", 8)
        effective_page_width = self.w - 2 * self.l_margin
        num_columns = len(columns_data_keys)
        col_width = effective_page_width / num_columns if num_columns > 0 else effective_page_width

        for row_dict in data:
            for data_key in columns_data_keys: # data_key это ключ из словаря row_dict
                cell_value_raw = row_dict.get(data_key) # Получаем значение по ключу
                
                cell_value_str = str(cell_value_raw) if cell_value_raw is not None else ''

                if isinstance(data_key, str) and "дата" in data_key.lower():
                    if isinstance(cell_value_raw, datetime.datetime):
                        cell_value_str = cell_value_raw.strftime('%d.%m.%Y %H:%M')
                    elif isinstance(cell_value_raw, str) and 'T' in cell_value_raw:
                        try:
                            dt_obj = datetime.datetime.fromisoformat(cell_value_raw.split('.')[0].replace('Z', '').replace(' ', 'T'))
                            cell_value_str = dt_obj.strftime('%d.%m.%Y %H:%M')
                        except ValueError:
                            try:
                                dt_obj_fallback = datetime.datetime.strptime(cell_value_raw, '%Y-%m-%d %H:%M:%S')
                                cell_value_str = dt_obj_fallback.strftime('%d.%m.%Y %H:%M')
                            except ValueError:
                                pass
                
                self.multi_cell(col_width, 6, cell_value_str, border=1, align="L", new_x="RIGHT", new_y="TOP", max_line_height=6)
            self.ln()


if __name__ == '__main__':
    #debug=True только для разработки!
    app.run(debug=True)