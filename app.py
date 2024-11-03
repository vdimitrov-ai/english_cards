from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# Создаем директорию для базы данных, если её нет
DB_DIR = 'db'
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Путь к базе данных
DATABASE = os.path.join(DB_DIR, 'cards.db')

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Инициализация таблицы карточек
def init_db():
    try:
        with get_db_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS cards (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            english_word TEXT NOT NULL,
                            russian_word TEXT NOT NULL,
                            is_hidden INTEGER DEFAULT 0
                            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS highscores (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            player_name TEXT NOT NULL,
                            score INTEGER NOT NULL,
                            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )''')
            
            # Проверяем, есть ли карточки в базе
            cards_count = conn.execute('SELECT COUNT(*) FROM cards').fetchone()[0]
            if cards_count == 0:
                # Добавляем начальные карточки
                default_cards = [
                    ('hello', 'привет'),
                    ('world', 'мир'),
                    ('cat', 'кошка'),
                    ('dog', 'собака'),
                    ('house', 'дом'),
                    ('tree', 'дерево'),
                    ('sun', 'солнце'),
                    ('moon', 'луна')
                ]
                conn.executemany('INSERT INTO cards (english_word, russian_word) VALUES (?, ?)',
                               default_cards)
            conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

# Добавляем обработчик ошибок
@app.errorhandler(Exception)
def handle_error(e):
    print(f"Error: {e}")
    return render_template('error.html', error=str(e)), 500

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Добавление новой карточки
@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        english_word = request.form['english_word']
        russian_word = request.form['russian_word']
        with get_db_connection() as conn:
            conn.execute('INSERT INTO cards (english_word, russian_word) VALUES (?, ?)',
                         (english_word, russian_word))
            conn.commit()
        return redirect(url_for('study'))
    return render_template('add_card.html')

# Обучение карточкам (только видимые карточки)
@app.route('/study')
def study():
    with get_db_connection() as conn:
        cards = conn.execute('SELECT * FROM cards WHERE is_hidden = 0').fetchall()
    return render_template('study.html', cards=cards)

# Скрытие одной карточки
@app.route('/hide_card/<int:card_id>', methods=['POST'])
def hide_card(card_id):
    with get_db_connection() as conn:
        conn.execute('UPDATE cards SET is_hidden = 1 WHERE id = ?', (card_id,))
        conn.commit()
    return redirect(url_for('study'))

# Восстановление всех скрытых карточек
@app.route('/restore_all', methods=['POST'])
def restore_all():
    with get_db_connection() as conn:
        conn.execute('UPDATE cards SET is_hidden = 0')
        conn.commit()
    return redirect(url_for('study'))

# Добавьте новый маршрут после существующих
@app.route('/game')
def game():
    with get_db_connection() as conn:
        # Получаем все видимые карточки и преобразуем их в список словарей
        cards = conn.execute('SELECT * FROM cards WHERE is_hidden = 0').fetchall()
        cards_list = []
        for card in cards:
            cards_list.append({
                'id': card['id'],
                'english_word': card['english_word'],
                'russian_word': card['russian_word'],
                'is_hidden': card['is_hidden']
            })
    return render_template('game.html', cards=cards_list)

# Добавим новые маршруты для рекордов
@app.route('/highscores')
def highscores():
    with get_db_connection() as conn:
        scores = conn.execute('''
            SELECT player_name, score, date 
            FROM highscores 
            ORDER BY score DESC 
            LIMIT 10
        ''').fetchall()
    return render_template('highscores.html', scores=scores)

@app.route('/save_score', methods=['POST'])
def save_score():
    player_name = request.form.get('player_name')
    score = request.form.get('score')
    if player_name and score:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO highscores (player_name, score) VALUES (?, ?)',
                        (player_name, score))
            conn.commit()
    return redirect(url_for('highscores'))

# Добавьте после других маршрутов
DEFAULT_PAIRS = [
    {'english_word': 'hello', 'russian_word': 'привет'},
    {'english_word': 'world', 'russian_word': 'мир'},
    {'english_word': 'cat', 'russian_word': 'кошка'},
    {'english_word': 'dog', 'russian_word': 'собака'},
    {'english_word': 'house', 'russian_word': 'дом'},
    {'english_word': 'tree', 'russian_word': 'дерево'},
    {'english_word': 'sun', 'russian_word': 'солнце'},
    {'english_word': 'moon', 'russian_word': 'луна'},
]

@app.route('/memory_game')
def memory_game():
    with get_db_connection() as conn:
        cards = conn.execute('SELECT * FROM cards WHERE is_hidden = 0').fetchall()
        cards_list = []
        for card in cards:
            cards_list.append({
                'english_word': card['english_word'],
                'russian_word': card['russian_word']
            })
        
        # Если карточек меньше 8 пар, добавляем карточки по умолчанию
        while len(cards_list) < 8:
            default_card = DEFAULT_PAIRS[len(cards_list)]
            if default_card not in cards_list:
                cards_list.append(default_card)
                
    return render_template('memory_game.html', cards=cards_list[:8])  # Берем только первые 8 пар

if __name__ == '__main__':
    init_db()  # Инициализируем базу данных при запуске
    app.run(debug=True)