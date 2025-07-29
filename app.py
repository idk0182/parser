from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for
from parser import Parser
from exporter import DataExporter
import json
import uuid
from flask_session import Session

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

app.secret_key = 'nothing_now'  

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        export = request.form.get('export')

        if not export:
            # Парсинг
            url = request.form.get('url')
            if not url:
                return "URL не указан", 400

            db_user = request.form.get('db_user', '')
            db_password = request.form.get('db_password', '')
            db_host = request.form.get('db_host', '')
            db_database = request.form.get('db_database', '')
            db_tablename = request.form.get('db_tablename', '')

            parser = Parser(url)
            try:
                html = parser.fetch()
                parser.parse(html)
                data = parser.get_data()

                # результат парсинга и параметры БД под уникальным ключом
                data_id = str(uuid.uuid4())
                session[data_id] = {
                    'data': data,
                    'url': url,
                    'db_user': db_user,
                    'db_password': db_password,
                    'db_host': db_host,
                    'db_database': db_database,
                    'db_tablename': db_tablename,
                }
                

                html_response = """
                <h1>Результаты парсинга</h1>
                <h3>Параметры MySQL для экспорта (можно изменить перед экспортом):</h3>
                <form method="post">
                    <input type="hidden" name="export" value="1">
                    <input type="hidden" name="data_id" value="{{ data_id }}">
                    <p>Примечание: запись в таблицу по умолчанию происходит по имени news_table</p>
                    <p>User: <input type="text" name="db_user" value="{{ db_user }}" required></p>
                    <p>Password: <input type="password" name="db_password" value="{{ db_password }}" required></p>
                    <p>Host: <input type="text" name="db_host" value="localhost" required></p>
                    <p>Database: <input type="text" name="db_database" value="{{ db_database }}" required></p>
                    <p>table_name: <input type="text" name="db_tablename" value="{{ db_tablename }}"></p>

                    <button type="submit">Экспортировать в базу данных</button>
                </form>
                <a href="/">Назад</a>
                <hr>

                {% for item in data %}
                <div style="border:1px solid #ccc; margin-bottom:10px; padding:10px;">
                    {% if item.author_name %}
                    <p><strong>Автор:</strong> {{ item.author_name }}</p>
                    {% endif %}
                    {% if item.title %}
                    <p><strong>Заголовок:</strong> {{ item.title }}</p>
                    {% endif %}
                    {% if item.link %}
                    <p><a href="{{ item.link }}" target="_blank">Ссылка</a></p>
                    {% endif %}
                    {% if item.date %}
                    <p><strong>Дата:</strong> {{ item.date }}</p>
                    {% endif %}
                    {% if item.text %}
                    <p>{{ item.text }}</p>
                    {% endif %}
                </div>
                {% endfor %}
                """

                return render_template_string(
                    html_response,
                    data=data,
                    data_id=data_id,
                    db_user=db_user,
                    db_password=db_password,
                    db_host=db_host,
                    db_database=db_database,
                    db_tablename=db_tablename
                )

            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"<h1>Ошибка</h1><p>{str(e)}</p><a href='/'>Назад</a>", 500

        else:
            # Экспорт
            data_id = request.form.get('data_id')
            if not data_id or data_id not in session:
                return "Данные для экспорта не найдены или сессия истекла", 400

            stored = session[data_id]
            data = stored.get('data')
            url = stored.get('url', '')

            db_user = request.form.get('db_user')
            db_password = request.form.get('db_password')
            db_host = request.form.get('db_host')
            db_database = request.form.get('db_database')
            db_tablename = request.form.get('db_tablename')

            if not all([db_user, db_password, db_host, db_database, db_tablename]):
                return "Все поля конфигурации базы данных обязательны", 400

            try:
                exporter = DataExporter(
                    user=db_user,
                    password=db_password,
                    host=db_host,
                    database=db_database,
                    tablename=db_tablename,
                )

                exporter.export_to_mysql(url, data, table_name=db_tablename)
                session.pop(data_id, None)
                return """
                <h1>Данные успешно экспортированы в Базу Данных</h1>
                <a href="/">Назад</a>
                """
            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"<h1>Ошибка экспорта</h1><p>{str(e)}</p><a href='/'>Назад</a>", 500

    return '''
        <h1>Ввод URL для парсинга и параметры MySQL</h1>
        <form method="post">
            <p>URL для парсинга:<br>
                <input type="text" name="url" placeholder="Введите URL" style="width:400px;" required />
            </p>
            <button type="submit">Парсить</button>
        </form>
    '''

# API маршруты
@app.route('/parse', methods=['POST'])
def parse_api():
    req_data = request.json
    url = req_data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    parser = Parser(url)
    try:
        html = parser.fetch()
        parser.parse(html)
        data = parser.get_data()
        return jsonify({'data': data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/export/mysql', methods=['POST'])
def export_mysql_api():
    req_data = request.json
    data = req_data.get('data')
    db_config = req_data.get('db_config')

    if not data or not db_config:
        return jsonify({'error': 'Data and db_config are required'}), 400

    try:
        exporter = DataExporter(
            user=db_config.get('user'),
            password=db_config.get('password'),
            host=db_config.get('host'),
            database=db_config.get('database')
        )
        exporter.export_to_mysql(data)
        return jsonify({'message': 'Data successfully exported to MySQL'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
