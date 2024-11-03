import os
import random
import sqlite3
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for, jsonify
from werkzeug.utils import secure_filename

from configs import (
    ADVANCED_WORDS,
    ALLOWED_EXTENSIONS,
    DATABASE,
    DEFAULT_PAIRS,
    RANDOM_NAMES,
    UPLOAD_FOLDER,
)

# Добавьте импорт для работы с dotenv
from dotenv import load_dotenv

from yandex_gpt import _get_response_yandex_gpt
from groq_llm import _get_response_groq, GROQ_MODELS

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Добавьте функцию проверки расширения файла
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db():
    try:
        with get_db_connection() as conn:
            # Создаем таблицу cards
            conn.execute(
                """CREATE TABLE IF NOT EXISTS cards (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            english_word TEXT NOT NULL,
                            russian_word TEXT NOT NULL,
                            description TEXT,
                            transcription TEXT,
                            pronunciation_url TEXT,
                            image_path TEXT,
                            is_hidden INTEGER DEFAULT 0
                            )"""
            )

            # Создаем таблицу highscores
            conn.execute(
                """CREATE TABLE IF NOT EXISTS highscores (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            player_name TEXT NOT NULL,
                            score INTEGER NOT NULL,
                            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )"""
            )

            # Создаем таблицу chat_history с полем model
            conn.execute(
                """CREATE TABLE IF NOT EXISTS chat_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            role TEXT NOT NULL,
                            message TEXT NOT NULL,
                            model TEXT NOT NULL DEFAULT 'yandex',
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )"""
            )

            # Проверяем количество существующих карточек
            card_count = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]

            # Добавляем карточки только если их нет или меньше 8
            if card_count < 8:
                # Выбираем 8 случайных карточек из списка ADVANCED_WORDS
                selected_cards = random.sample(ADVANCED_WORDS, 8)

                # Проверяем каждую карточку перед вставкой
                for word in selected_cards:
                    # Проверяем, существует ли уже такая карточка
                    existing = conn.execute(
                        "SELECT id FROM cards WHERE english_word = ? AND russian_word = ?",
                        (word[0], word[1]),
                    ).fetchone()

                    # Вставляем только если карточки нет
                    if not existing:
                        conn.execute(
                            """INSERT INTO cards 
                            (english_word, russian_word, description, transcription, pronunciation_url) 
                            VALUES (?, ?, ?, ?, ?)""",
                            (word[0], word[1], word[2], word[3], word[4]),
                        )

            conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


# Добавляем обработчик ошибок
@app.errorhandler(Exception)
def handle_error(e):
    print(f"Error: {e}")
    return render_template("error.html", error=str(e)), 500


# Главная страница
@app.route("/")
def index():
    return render_template("index.html")


# Добавление новой карточки
@app.route("/add_card", methods=["GET", "POST"])
def add_card():
    if request.method == "POST":
        english_word = request.form["english_word"]
        russian_word = request.form["russian_word"]
        description = request.form["description"]
        transcription = request.form["transcription"]
        pronunciation_url = request.form["pronunciation_url"]

        image_path = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_path = f"card_images/{filename}"

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO cards (english_word, russian_word, description, transcription, 
                                 pronunciation_url, image_path) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    english_word,
                    russian_word,
                    description,
                    transcription,
                    pronunciation_url,
                    image_path,
                ),
            )
            conn.commit()
        return redirect(url_for("study"))
    return render_template("add_card.html")


# Обучение карточкам (только видимые карточки)
@app.route("/study")
def study():
    with get_db_connection() as conn:
        cards = conn.execute("SELECT * FROM cards WHERE is_hidden = 0").fetchall()
    return render_template("study.html", cards=cards)


# Скрытие одной карточки
@app.route("/hide_card/<int:card_id>", methods=["POST"])
def hide_card(card_id):
    with get_db_connection() as conn:
        conn.execute("UPDATE cards SET is_hidden = 1 WHERE id = ?", (card_id,))
        conn.commit()
    return redirect(url_for("study"))


# Восстановление всех скрытых карточек
@app.route("/restore_all", methods=["POST"])
def restore_all():
    with get_db_connection() as conn:
        conn.execute("UPDATE cards SET is_hidden = 0")
        conn.commit()
    return redirect(url_for("study"))


# Добавьте новый маршрут после существующих
@app.route("/game")
def game():
    with get_db_connection() as conn:
        # Получаем все видимые карточки и преобразуем их в список словарей
        cards = conn.execute("SELECT * FROM cards WHERE is_hidden = 0").fetchall()
        cards_list = []
        for card in cards:
            cards_list.append(
                {
                    "id": card["id"],
                    "english_word": card["english_word"],
                    "russian_word": card["russian_word"],
                    "is_hidden": card["is_hidden"],
                }
            )
    return render_template("game.html", cards=cards_list)


# Добавим новые маршруты для рекордов
@app.route("/highscores")
def highscores():
    with get_db_connection() as conn:
        scores = conn.execute(
            """
            SELECT player_name, score, date 
            FROM highscores 
            ORDER BY score DESC 
            LIMIT 10
        """
        ).fetchall()
    return render_template("highscores.html", scores=scores)


# Измените функцию save_score
@app.route("/save_score", methods=["POST"])
def save_score():
    score = request.form.get("score")
    if score:
        # Генерируем случа��ное имя
        player_name = random.choice(RANDOM_NAMES)
        # Получаем текущую дату и время
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO highscores (player_name, score, date) VALUES (?, ?, ?)",
                (player_name, score, current_time),
            )
            conn.commit()
    return redirect(url_for("highscores"))


@app.route("/memory_game")
def memory_game():
    with get_db_connection() as conn:
        cards = conn.execute("SELECT * FROM cards WHERE is_hidden = 0").fetchall()
        cards_list = []
        for card in cards:
            cards_list.append(
                {
                    "english_word": card["english_word"],
                    "russian_word": card["russian_word"],
                }
            )

        # Если карточек меньше 8 пар, добавляем карточки по умолчанию
        while len(cards_list) < 8:
            default_card = DEFAULT_PAIRS[len(cards_list)]
            if default_card not in cards_list:
                cards_list.append(default_card)

    return render_template(
        "memory_game.html", cards=cards_list[:8]
    )  # Берем только первые 8 пар


# Добавьте новый маршрут для получения описания карточки
@app.route("/get_card_description/<int:card_id>")
def get_card_description(card_id):
    with get_db_connection() as conn:
        card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
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


# Добавьте новые маршруты
@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        user_message = data.get("message")
        model_key = data.get("model", "yandex")  # По умолчанию используем Yandex
        temperature = float(data.get("temperature", 0.7))
        max_tokens = int(data.get("max_tokens", 2000))

        # Сохраняем сообщение пользователя
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO chat_history (role, message, model) VALUES (?, ?, ?)",
                ("user", user_message, model_key),
            )
            conn.commit()

            # Получаем последние N сообщений для контекста только для текущей модели
            history = conn.execute(
                "SELECT role, message FROM chat_history WHERE model = ? ORDER BY timestamp DESC LIMIT 10",
                (model_key,),
            ).fetchall()

        # Формируем контекст для модели
        context = []
        for msg in reversed(history):
            context.append({"role": msg["role"], "text": msg["message"]})

        # Выбираем модель и получаем ответ
        if model_key in GROQ_MODELS:  # Если выбрана одна из моделей Groq
            assistant_response, tokens = _get_response_groq(
                context,
                temperature=temperature,
                max_tokens=max_tokens,
                model=GROQ_MODELS[model_key],
            )
        else:  # yandex
            assistant_response, tokens = _get_response_yandex_gpt(
                context, temperature=temperature, max_tokens=max_tokens
            )

        if assistant_response:
            # Сохраняем ответ ассистента
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO chat_history (role, message, model) VALUES (?, ?, ?)",
                    ("assistant", assistant_response, model_key),
                )
                conn.commit()
            return jsonify({"response": assistant_response})
        else:
            return (
                jsonify({"response": "Извините, произошла ошибка. Попробуйте позже."}),
                500,
            )

    except Exception as e:
        print(f"Error in ask endpoint: {e}")
        return (
            jsonify({"response": "Извините, произошла ошибка. Попробуйте позже."}),
            500,
        )


@app.route("/get_chat_history")
def get_chat_history():
    try:
        with get_db_connection() as conn:
            history = conn.execute(
                "SELECT role, message FROM chat_history ORDER BY timestamp ASC"
            ).fetchall()
        return jsonify([{"role": h["role"], "message": h["message"]} for h in history])
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return jsonify([])


# Добавьте новый маршрут для очистки истории
@app.route("/clear_chat_history", methods=["POST"])
def clear_chat_history():
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM chat_history")
            conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return jsonify({"success": False}), 500


if __name__ == "__main__":
    init_db()  # Инициализируем базу данных при запуске
    app.run(debug=True)
