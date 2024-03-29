import telebot, os, sqlite3, re
from random import *

"""
Список команд бота:
start - Запуск бота
view - Просмотр телефонной книги
search - Поиск учётной записи в телефонной книге
delete - Удаление учётной записи из телефонной книги
edit - Изменение данных учётной записи в телефонной книге
add - Добавление учётной записи в телефонную книгу

#save - Сохранение телефонной книги - упразднена после появления БД
#import - Импорт телефонной книги из файла book.json - упразднена после появления БД
"""

# Тут был мой Джейсон. RIP
# def get_project_dir():
#     project_dir = os.path.dirname(__file__)
#     json_file_path = os.path.join(project_dir, 'book.json')
#     return json_file_path

# @bot.message_handler(commands=['import'])
# def load_all(message):
#     with open(get_project_dir(),'r',encoding='utf-8') as bk:
#         book = json.load(bk)
#     bot.send_message(message.chat.id, 'Книга успешно загружена из файла "book.json"!')

nums = "0123456789"
greetings = ['привет', 'здрасте', 'ку']
API_TOKEN='7114595238:AAHVftqYIsGx4VyDhwckunC3tusjcQCqZEA'
bot = telebot.TeleBot(API_TOKEN)

"""
Инициализация бота и БД
"""
@bot.message_handler(commands=['start'])
def start_message(message):
    # Подключаемся к базе данных SQLite
    database_path = get_database_path
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    # Создаём таблицу "persons", если она ещё не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ФИО TEXT,
            телефоны TEXT,
            дата_рождения TEXT,
            эл_почта TEXT
        )
    ''')
    # Проверяем, есть ли уже записи в таблице, и если нет, добавляем начальные данные
    cursor.execute("SELECT COUNT(*) FROM persons")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO persons (ФИО, телефоны, дата_рождения, эл_почта)
            VALUES (?, ?, ?, ?)
        ''', ('Иванов Иван Иванович', '123456, 654321', '02.02.1990', 'ivanov@example.com'))
    # Сохраняем изменения и закрываем соединение с базой данных
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, 'Телефонная книга была загружена по умолчанию!')

def get_database_path():
    # Проверяем, чтобы БД сохранялась в корень проекта
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, 'book.db')

"""
Просмотр записей
"""
@bot.message_handler(commands=['view'])
def view_all(message):
    database_path = get_database_path
    conn = sqlite3.connect(database_path())
    # Создаём курсор с помощью менеджера контекста, на случай, если нам понадобиться не разрывать подключение к БД каждый раз
    with conn:
        cursor = conn.cursor()
        # Выполняем операции с базой данных
        cursor.execute("SELECT * FROM persons")
        records = cursor.fetchall()
    # Проверяем, есть ли записи в таблице
    if records:
        response = "\n".join([f'{record[1]}: {record[2]}, {record[3]}, {record[4]}' for record in records])
        bot.send_message(message.chat.id, 'Список записей в телефонной книге:\n' + response)
    else:
        bot.send_message(message.chat.id, 'В книге нет записей!')
    conn.close()
    
"""
Поиск учётной записи
"""
@bot.message_handler(commands=['search'])
def search(message):
    bot.send_message(message.chat.id, 'Введите фамилию или номер телефона для поиска: ')
    bot.register_next_step_handler(message, process_search)

def process_search(message):
    query = message.text.strip()  # Получаем запрос пользователя и удаляем лишние пробелы
    database_path = get_database_path
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM persons WHERE ФИО LIKE ? OR телефоны LIKE ?", ('%'+query+'%', '%'+query+'%'))
    found_records = cursor.fetchall()
    conn.close()

    if found_records:
        response = "Найденные учётные записи:\n"
        for record in found_records:
            response += f"ФИО: {record[1]}, Телефоны: {record[2]}, Дата рождения: {record[3]}, Эл. почта: {record[4]}\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "По вашему запросу ничего не найдено.")

"""
Добавление учётной записи
"""
@bot.message_handler(commands=['add'])
def append_rec(message):
    bot.send_message(message.chat.id, 'Введите Ф.И.О.: ')
    bot.register_next_step_handler(message, process_surname)

def process_surname(message):
    if all(char.isalpha() or char.isspace() for char in message.text):
        surname = message.text
        bot.send_message(message.chat.id, 'Введите номер телефона. Если номеров несколько, введите список номеров в строку, разделяя их ", " (ЗПТ + пробел): ')
        bot.register_next_step_handler(message, lambda m: process_phone_number(m, surname))
    else:
        bot.send_message(message.chat.id, 'Фамилия не должна содержать цифры!')

def process_phone_number(message, surname):
    phone_nums = message.text.split(',')  # Разделяем строку на отдельные номера
    formatted_phone_nums = []
    for phone_num in phone_nums:
        phone_num = phone_num.strip()  # Удаляем лишние пробелы в начале и в конце
        if phone_num.isdigit():
            formatted_phone_nums.append(phone_num)
        else:
            bot.send_message(message.chat.id, 'Некорректный номер телефона: {}'.format(phone_num))
            return
    if not formatted_phone_nums:
        bot.send_message(message.chat.id, 'Введены некорректные номера телефона!')
        return
    formatted_phone_nums_str = ', '.join(formatted_phone_nums)
    bot.send_message(message.chat.id, 'Введите дату рождения, если, конечно, знаете: ')
    bot.register_next_step_handler(message, lambda m: process_birthday(m, surname, formatted_phone_nums_str))

def process_birthday(message, surname, numbers):
    birthday = message.text
    bot.send_message(message.chat.id, 'Введите адрес электронной почты: ')
    bot.register_next_step_handler(message, lambda m: process_email(m, surname, numbers, birthday))

def process_email(message, surname, numbers, birthday):
    email = message.text
    # Добавляем учётную запись в базу данных
    add_record_to_database(surname, numbers, birthday, email)
    bot.send_message(message.chat.id, 'Учётная запись успешно добавлена в книгу!')

def add_record_to_database(surname, phone_num, birthday, email):
    database_path = get_database_path
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    # Находим первый доступный ID в порядке возрастания
    cursor.execute("SELECT id + 1 FROM persons t1 WHERE NOT EXISTS (SELECT 1 FROM persons t2 WHERE t2.id = t1.id + 1) ORDER BY id LIMIT 1")
    available_id = cursor.fetchone()[0]
    # Если есть доступный ID, вставляем запись с этим ID
    if available_id is not None:
        cursor.execute("INSERT INTO persons (id, ФИО, телефоны, дата_рождения, эл_почта) VALUES (?, ?, ?, ?, ?)", (available_id, surname, phone_num, birthday, email))
    else:
        # Если доступных ID нет, вставляем запись с максимальным ID + 1
        cursor.execute("SELECT MAX(id) FROM persons")
        max_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO persons (id, ФИО, телефоны, дата_рождения, эл_почта) VALUES (?, ?, ?, ?, ?)", (max_id + 1, surname, phone_num, birthday, email))
    conn.commit()
    conn.close()
    
"""
Удаление учётной записи
"""
@bot.message_handler(commands=['delete'])
def delete(message):
    database_path = get_database_path
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    cursor.execute("SELECT id, ФИО, телефоны FROM persons")
    records = cursor.fetchall()
    if records:
        response = "Список учётных записей:\n"
        for record in records:
            response += f"{record[0]}. {record[1]} ({record[2]})\n"
        bot.send_message(message.chat.id, response)
        bot.send_message(message.chat.id, 'Введите номер учётной записи, которую хотите удалить:')
        bot.register_next_step_handler(message, process_delete)
    else:
        bot.send_message(message.chat.id, "В книге уже не осталось записей.")

def process_delete(message):
    try:
        record_id = int(message.text)
        database_path = get_database_path
        conn = sqlite3.connect(database_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM persons")
        existing_ids = [row[0] for row in cursor.fetchall()]
        if record_id not in existing_ids:
            bot.send_message(message.chat.id, "Учётной записи с таким ID номером не существует.")
            return
        cursor.execute("DELETE FROM persons WHERE id=?", (record_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"Учётная запись с номером {record_id} успешно удалена.")
    except ValueError:
        bot.send_message(message.chat.id, "Некорректный номер учётной записи.")
    
"""
Редактирование учётной записи
"""
@bot.message_handler(commands=['edit'])
def edit_rec(message):
    database_path = get_database_path
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    cursor.execute("SELECT id, ФИО, телефоны, дата_рождения, эл_почта FROM persons")        
    records = cursor.fetchall()
    if records:
        response = "Список учётных записей:\n"
        for record in records:
            response += f"{record[0]}. {record[1]}, {record[2]}, {record[3]}, {record[4]}\n"
        bot.send_message(message.chat.id, response)
        bot.send_message(message.chat.id, 'Введите номер учётной записи, которую хотите редактировать:')
        bot.register_next_step_handler(message, process_edit)
    else:
        bot.send_message(message.chat.id, "В книге нет записей.")

def process_edit(message):
    selected_id = message.text.strip()  # Получаем номер выбранной записи
    bot.send_message(message.chat.id, 'Выберите поле для редактирования: ФИО, Телефоны, Дата, Почта')
    bot.register_next_step_handler(message, lambda m: process_field_selection(m, selected_id))

def process_field_selection(message, selected_id):
    selected_field = message.text.strip().lower()  # Получаем выбранное поле и приводим его к нижнему регистру
    match selected_field:
        case 'фио':
            bot.send_message(message.chat.id, 'Введите новое значение ФИО:')
            bot.register_next_step_handler(message, lambda m: process_edit_field(m, selected_id, 'ФИО'))
        case 'телефоны':
            bot.send_message(message.chat.id, 'Введите новые телефоны, разделяя их запятой и пробелом:')
            bot.register_next_step_handler(message, lambda m: process_edit_field(m, selected_id, 'телефоны'))
        case 'дата':
            bot.send_message(message.chat.id, 'Введите новую дату рождения:')
            bot.register_next_step_handler(message, lambda m: process_edit_field(m, selected_id, 'дата_рождения'))
        case 'почта':
            bot.send_message(message.chat.id, 'Введите новую электронную почту:')
            bot.register_next_step_handler(message, lambda m: process_edit_field(m, selected_id, 'эл_почта'))
        case _:
            bot.send_message(message.chat.id, 'Некорректный выбор. Пожалуйста, выберите одно из предложенных полей для редактирования.')

def process_edit_field(message, selected_id, field_name):
    new_value = message.text.strip()
    database_path = get_database_path
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    try:
        # Выполняем SQL-запрос UPDATE для обновления поля выбранной записи
        cursor.execute(f"UPDATE persons SET {field_name} = ? WHERE id = ?", (new_value, selected_id))
        conn.commit()
        bot.send_message(message.chat.id, f'Поле {field_name} у записи с ID {selected_id} успешно обновлено на значение {new_value}.')
    except sqlite3.Error as e:
        bot.send_message(message.chat.id, f'Ошибка при обновлении поля {field_name}: {e}')
    finally:
        conn.close()

"""
Обработка реплик
"""
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    txt = message.text.lower()
    if any(word in txt for word in greetings):
        bot.send_message(message.chat.id, 'Всегда искренне рад приветствовать Вас, дорогой друг!')


bot.polling()