from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
import random
from werkzeug.utils import secure_filename
from typing import List, Tuple

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

# Добавьте конфигурацию для загрузки файлов
UPLOAD_FOLDER = 'static/card_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Создаем директорию для загрузки изображений, если её нет
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Добавьте функцию проверки расширения файла
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Создайте список сложных слов (можно разместить перед функцией init_db)
ADVANCED_WORDS: List[Tuple[str, str, str, str, str]] = [
    ('ubiquitous', 'вездесущий', 
     'Присутствующий или находящийся повсюду одновременно. Пример: "Smartphones have become ubiquitous in modern society."',
     '/juːˈbɪkwɪtəs/',
     'https://dictionary.cambridge.org/dictionary/english-russian/ubiquitous'),
    ('ephemeral', 'мимолётный', 
     'Существующий очень короткое время. Пример: "The ephemeral nature of social media trends."',
     '/ɪˈfem.ər.əl/',
     'https://dictionary.cambridge.org/dictionary/english-russian/ephemeral'),
    ('paradigm', 'парадигма', 
     'Типичный пример или модель чего-либо. Пример: "This discovery represents a paradigm shift in our understanding."',
     '/ˈpær.ə.daɪm/',
     'https://dictionary.cambridge.org/dictionary/english-russian/paradigm'),
    ('eloquent', 'красноречивый',
     'Способный выражать мысли чётко и убедительно. Пример: "Her eloquent speech moved the audience."',
     '/ˈel.ə.kwənt/',
     'https://dictionary.cambridge.org/dictionary/english-russian/eloquent'),
    ('meticulous', 'скрупулёзный',
     'Проявляющий чрезвычайное внимание к деталям. Пример: "He is meticulous in his research."',
     '/məˈtɪk.jə.ləs/',
     'https://dictionary.cambridge.org/dictionary/english-russian/meticulous'),
    ('ambiguous', 'двусмысленный',
     'Имеющий более одного возможного значения. Пример: "The contract contained several ambiguous clauses."',
     '/æmˈbɪɡ.ju.əs/',
     'https://dictionary.cambridge.org/dictionary/english-russian/ambiguous'),
    ('enigmatic', 'загадочный',
     'Трудный для понимания, таинственный. Пример: "She gave an enigmatic smile."',
     '/ˌen.ɪɡˈmæt.ɪk/',
     'https://dictionary.cambridge.org/dictionary/english-russian/enigmatic'),
    ('cognizant', 'осведомлённый',
     'Имеющий знание или осознание чего-либо. Пример: "We are cognizant of the risks involved."',
     '/ˈkɒɡ.nɪ.zənt/',
     'https://dictionary.cambridge.org/dictionary/english-russian/cognizant'),
    ('ethereal', 'неземной',
     'Крайне деликатный и лёгкий, неземной. Пример: "The ethereal beauty of the northern lights."',
     '/ɪˈθɪə.ri.əl/',
     'https://dictionary.cambridge.org/dictionary/english-russian/ethereal'),
    ('fastidious', 'привередливый',
     'Уделяющий большое внимание точности и деталям. Пример: "He is fastidious about his appearance."',
     '/fæˈstɪd.i.əs/',
     'https://dictionary.cambridge.org/dictionary/english-russian/fastidious')
]

# Инициализация таблицы карточек
def init_db():
    try:
        with get_db_connection() as conn:
            # Создаем таблицу cards
            conn.execute('''CREATE TABLE IF NOT EXISTS cards (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            english_word TEXT NOT NULL,
                            russian_word TEXT NOT NULL,
                            description TEXT,
                            transcription TEXT,
                            pronunciation_url TEXT,
                            image_path TEXT,
                            is_hidden INTEGER DEFAULT 0
                            )''')
            
            # Создаем таблицу highscores
            conn.execute('''CREATE TABLE IF NOT EXISTS highscores (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            player_name TEXT NOT NULL,
                            score INTEGER NOT NULL,
                            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )''')
            
            # Очищаем существующие карточки по умолчанию
            conn.execute('DELETE FROM cards WHERE id IN (SELECT id FROM cards LIMIT 8)')
            
            # Выбираем 8 случайных карточек из списка ADVANCED_WORDS
            selected_cards = random.sample(ADVANCED_WORDS, 8)
            
            # Добавляем выбранные карточки с транскрипцией
            conn.executemany('''INSERT INTO cards 
                              (english_word, russian_word, description, transcription, pronunciation_url) 
                              VALUES (?, ?, ?, ?, ?)''',
                           [(word[0], word[1], word[2], word[3], word[4]) for word in selected_cards])
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
        description = request.form['description']
        transcription = request.form['transcription']
        pronunciation_url = request.form['pronunciation_url']
        
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f"card_images/{filename}"

        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO cards (english_word, russian_word, description, transcription, 
                                 pronunciation_url, image_path) 
                VALUES (?, ?, ?, ?, ?, ?)''',
                (english_word, russian_word, description, transcription, 
                 pronunciation_url, image_path)
            )
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

# Добавьте список случайных имен
RANDOM_NAMES = [
    "Александр", "Мария", "Дмитрий", "Анна", "Иван", "Елена", "Сергей", 
    "Ольга", "Андрей", "Наталья", "Михаил", "Екатерина", "Владимир",
    "Татьяна", "Алексей", "Светлана", "Николай", "Юлия"
]

# Измените функцию save_score
@app.route('/save_score', methods=['POST'])
def save_score():
    score = request.form.get('score')
    if score:
        # Генерируем случайное имя
        player_name = random.choice(RANDOM_NAMES)
        # Получаем текущую дату и время
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO highscores (player_name, score, date) VALUES (?, ?, ?)',
                (player_name, score, current_time)
            )
            conn.commit()
    return redirect(url_for('highscores'))

# Добавьте после других маршрутов
DEFAULT_PAIRS = [
    {'english_word': 'resilient', 'russian_word': 'стойкий'},
    {'english_word': 'arbitrary', 'russian_word': 'произвольный'},
    {'english_word': 'profound', 'russian_word': 'глубокий'},
    {'english_word': 'intricate', 'russian_word': 'сложный'},
    {'english_word': 'adamant', 'russian_word': 'непреклонный'},
    {'english_word': 'peculiar', 'russian_word': 'своеобразный'},
    {'english_word': 'eloquent', 'russian_word': 'красноречивый'},
    {'english_word': 'tenacious', 'russian_word': 'упорный'}
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

# Добавьте новый маршрут для получения описания карточки
@app.route('/get_card_description/<int:card_id>')
def get_card_description(card_id):
    with get_db_connection() as conn:
        card = conn.execute('SELECT * FROM cards WHERE id = ?', (card_id,)).fetchone()
    if card:
        return {
            'english_word': card['english_word'],
            'russian_word': card['russian_word'],
            'description': card['description'],
            'transcription': card['transcription'],
            'pronunciation_url': card['pronunciation_url'],
            'image_path': card['image_path']
        }
    return {'error': 'Card not found'}, 404

if __name__ == '__main__':
    init_db()  # Инициализируем базу данных при запуске
    app.run(debug=True)
