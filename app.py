import logging
import os
import random
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import (LoginManager, current_user, login_required, login_user,
                        logout_user)
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from configs import (ADVANCED_WORDS, ALLOWED_EXTENSIONS, DATABASE, DEFAULT_PAIRS,
                    RANDOM_NAMES, UPLOAD_FOLDER)
from groq_llm import GROQ_MODELS, _get_response_groq
from models import User
from yandex_gpt import _get_response_yandex_gpt

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# Добавляем секретный ключ для сессий
app.secret_key = os.urandom(24)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

@login_manager.user_loader
def load_user(user_id):
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            return User(
                id=user['id'],
                username=user['username'],
                email=user['email'],
                password_hash=user['password_hash']
            )
    return None

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        with open(DATABASE, 'w') as db_file:
            pass
    try:
        with get_db_connection() as conn:
            # Сохраняем существующие данные
            try:
                existing_cards = conn.execute('SELECT * FROM cards').fetchall()
            except sqlite3.OperationalError:
                existing_cards = []

            try:
                existing_highscores = conn.execute('SELECT * FROM highscores').fetchall()
            except sqlite3.OperationalError:
                existing_highscores = []

            try:
                existing_chat = conn.execute('SELECT * FROM chat_history').fetchall()
            except sqlite3.OperationalError:
                existing_chat = []

            # Удаляем существующие таблицы
            conn.executescript('''
                DROP TABLE IF EXISTS chat_history;
                DROP TABLE IF EXISTS cards;
                DROP TABLE IF EXISTS highscores;
                DROP TABLE IF EXISTS users;
            ''')

            # Создаем таблицы заново
            conn.executescript('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    english_word TEXT NOT NULL,
                    russian_word TEXT NOT NULL,
                    description TEXT,
                    transcription TEXT,
                    pronunciation_url TEXT,
                    image_path TEXT,
                    is_hidden INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE highscores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    player_name TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    model TEXT NOT NULL DEFAULT 'yandex',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            ''')

            # Создаем тестового пользователя, если нужно
            try:
                conn.execute('''
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                ''', ('admin', 'admin@example.com', generate_password_hash('Admin123')))
                admin_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                
                # Восстанавливаем существующие данные с привязкой к admin
                if existing_cards:
                    for card in existing_cards:
                        conn.execute('''
                            INSERT INTO cards (
                                user_id, english_word, russian_word, description,
                                transcription, pronunciation_url, image_path, is_hidden
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (admin_id, card['english_word'], card['russian_word'],
                              card['description'], card['transcription'],
                              card['pronunciation_url'], card['image_path'],
                              card['is_hidden']))

                if existing_highscores:
                    for score in existing_highscores:
                        conn.execute('''
                            INSERT INTO highscores (user_id, player_name, score, date)
                            VALUES (?, ?, ?, ?)
                        ''', (admin_id, score['player_name'], score['score'], score['date']))

                if existing_chat:
                    for chat in existing_chat:
                        conn.execute('''
                            INSERT INTO chat_history (user_id, role, message, model, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (admin_id, chat['role'], chat['message'],
                              chat.get('model', 'yandex'), chat['timestamp']))

            except sqlite3.IntegrityError:
                # Пользователь уже существует
                pass

            conn.commit()
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Проверка сложности пароля
        if len(password) < 8:
            flash('Пароль должен содержать минимум 8 символов')
            return redirect(url_for('register'))
        
        if not any(c.isupper() for c in password):
            flash('Пароль должен содержать хотя бы одну заглавную букву')
            return redirect(url_for('register'))
            
        if not any(c.isdigit() for c in password):
            flash('Пароль должен содержать хотя бы одну цифру')
            return redirect(url_for('register'))

        try:
            with get_db_connection() as conn:
                # Создаем пользователя
                conn.execute(
                    'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                    (username, email, generate_password_hash(password))
                )
                conn.commit()
                
                # Получаем ID нового пользователя
                user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                
                # Добавляем начальные карточки
                for word in ADVANCED_WORDS[:8]:
                    conn.execute(
                        '''INSERT INTO cards 
                        (user_id, english_word, russian_word, description, transcription, pronunciation_url) 
                        VALUES (?, ?, ?, ?, ?, ?)''',
                        (user_id, word[0], word[1], word[2], word[3], word[4])
                    )
                conn.commit()

                # Создаем объект пользователя и выполняем вход
                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password)
                )
                login_user(user)
                
                return redirect(url_for('index'))
                
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем или email уже существует')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db_connection() as conn:
            user_data = conn.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()
            
        if user_data:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash']
            )
            if user.check_password(password):
                login_user(user, remember=True)
                next_page = request.args.get('next')
                if next_page and url_parse(next_page).netloc == '':
                    return redirect(next_page)
                return redirect(url_for('index'))
        
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Обновляем существующие маршруты для работы с пользователями
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('welcome.html')
    return render_template('index.html', username=current_user.username)

@app.route('/study')
@login_required
def study():
    with get_db_connection() as conn:
        cards = conn.execute(
            'SELECT * FROM cards WHERE user_id = ? AND is_hidden = 0', 
            (current_user.id,)
        ).fetchall()
    return render_template('study.html', cards=cards)

@app.route('/add_card', methods=['GET', 'POST'])
@login_required
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
            conn.execute(
                '''INSERT INTO cards (
                    user_id, english_word, russian_word, description, 
                    transcription, pronunciation_url, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (current_user.id, english_word, russian_word, description,
                 transcription, pronunciation_url, image_path)
            )
            conn.commit()
        return redirect(url_for('study'))
    return render_template('add_card.html')

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    try:
        data = request.get_json()
        user_message = data.get('message')
        model_key = data.get('model', 'yandex')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2000))

        logger.info(f"Request from user {current_user.username} - Model: {model_key}")
        
        if not user_message:
            return jsonify({"response": "Message cannot be empty"}), 400

        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO chat_history (user_id, role, message, model) VALUES (?, ?, ?, ?)',
                (current_user.id, 'user', user_message, model_key)
            )
            conn.commit()

            history = conn.execute(
                '''SELECT role, message 
                FROM chat_history 
                WHERE user_id = ? AND model = ? 
                ORDER BY timestamp DESC LIMIT 10''',
                (current_user.id, model_key)
            ).fetchall()

        context = []
        for msg in reversed(history):
            context.append({"role": msg['role'], "text": msg['message']})

        if model_key in GROQ_MODELS:
            assistant_response, tokens = _get_response_groq(
                context,
                temperature=temperature,
                max_tokens=max_tokens,
                model=GROQ_MODELS[model_key],
            )
        else:
            assistant_response, tokens = _get_response_yandex_gpt(
                context, temperature=temperature, max_tokens=max_tokens
            )

        if assistant_response:
            with get_db_connection() as conn:
                conn.execute(
                    'INSERT INTO chat_history (user_id, role, message, model) VALUES (?, ?, ?, ?)',
                    (current_user.id, 'assistant', assistant_response, model_key)
                )
                conn.commit()
            return jsonify({"response": assistant_response})
        else:
            return jsonify({"response": "Извините, не удалось получить ответ."}), 500

    except Exception as e:
        logger.error(f"Error in ask endpoint: {str(e)}", exc_info=True)
        return jsonify({"response": f"Произошла ошибка: {str(e)}"}), 500

@app.route('/get_chat_history')
@login_required
def get_chat_history():
    try:
        with get_db_connection() as conn:
            history = conn.execute(
                '''SELECT role, message 
                FROM chat_history 
                WHERE user_id = ? 
                ORDER BY timestamp ASC''',
                (current_user.id,)
            ).fetchall()
        return jsonify([{"role": h['role'], "message": h['message']} for h in history])
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify([])

@app.route('/clear_chat_history', methods=['POST'])
@login_required
def clear_chat_history():
    try:
        with get_db_connection() as conn:
            conn.execute(
                'DELETE FROM chat_history WHERE user_id = ?',
                (current_user.id,)
            )
            conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return jsonify({"success": False}), 500

@app.route('/game')
@login_required
def game():
    with get_db_connection() as conn:
        # Получаем все видимые карточки текущего пользователя
        cards = conn.execute(
            'SELECT * FROM cards WHERE user_id = ? AND is_hidden = 0', 
            (current_user.id,)
        ).fetchall()
        cards_list = []
        for card in cards:
            cards_list.append({
                "id": card["id"],
                "english_word": card["english_word"],
                "russian_word": card["russian_word"],
                "is_hidden": card["is_hidden"],
            })
    return render_template("game.html", cards=cards_list)

@app.route('/memory_game')
@login_required
def memory_game():
    with get_db_connection() as conn:
        cards = conn.execute(
            'SELECT * FROM cards WHERE user_id = ? AND is_hidden = 0', 
            (current_user.id,)
        ).fetchall()
        cards_list = []
        for card in cards:
            cards_list.append({
                "english_word": card["english_word"],
                "russian_word": card["russian_word"],
            })

        # Если карточек меньше 8 пар, добавляем карточки по умолчанию
        while len(cards_list) < 8:
            default_card = DEFAULT_PAIRS[len(cards_list)]
            if default_card not in cards_list:
                cards_list.append(default_card)

    return render_template("memory_game.html", cards=cards_list[:8])

@app.route('/hide_card/<int:card_id>', methods=['POST'])
@login_required
def hide_card(card_id):
    with get_db_connection() as conn:
        # Проверяем, принадлежит ли карточка текущему пользователю
        card = conn.execute(
            'SELECT user_id FROM cards WHERE id = ?', 
            (card_id,)
        ).fetchone()
        
        if card and card['user_id'] == current_user.id:
            conn.execute(
                'UPDATE cards SET is_hidden = 1 WHERE id = ? AND user_id = ?',
                (card_id, current_user.id)
            )
            conn.commit()
    return redirect(url_for('study'))

@app.route('/restore_all', methods=['POST'])
@login_required
def restore_all():
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE cards SET is_hidden = 0 WHERE user_id = ?',
            (current_user.id,)
        )
        conn.commit()
    return redirect(url_for('study'))

@app.route('/highscores')
def highscores():
    with get_db_connection() as conn:
        scores = conn.execute('''
            SELECT h.player_name, h.score, h.date, u.username 
            FROM highscores h
            JOIN users u ON h.user_id = u.id
            ORDER BY h.score DESC 
            LIMIT 10
        ''').fetchall()
    return render_template('highscores.html', scores=scores)

@app.route('/save_score', methods=['POST'])
@login_required
def save_score():
    score = request.form.get('score')
    if score:
        player_name = random.choice(RANDOM_NAMES)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO highscores (user_id, player_name, score, date) VALUES (?, ?, ?, ?)',
                (current_user.id, player_name, score, current_time)
            )
            conn.commit()
    return redirect(url_for('highscores'))

@app.route('/get_card_description/<int:card_id>')
@login_required
def get_card_description(card_id):
    with get_db_connection() as conn:
        card = conn.execute(
            'SELECT * FROM cards WHERE id = ? AND user_id = ?',
            (card_id, current_user.id)
        ).fetchone()
    if card:
        return {
            "english_word": card["english_word"],
            "russian_word": card["russian_word"],
            "description": card["description"],
            "transcription": card["transcription"],
            "pronunciation_url": card["pronunciation_url"],
            "image_path": card["image_path"],
        }
    return {"error": "Card not found"}, 404

# Остальные маршруты остаются без изменений...

if __name__ == '__main__':
    load_dotenv()
    #check_environment()
    init_db()
    app.run(debug=True)
