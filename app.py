import os
import random
import sqlite3
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from configs import ADVANCED_WORDS, ALLOWED_EXTENSIONS, DATABASE, DEFAULT_PAIRS, RANDOM_NAMES, UPLOAD_FOLDER

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
                        (word[0], word[1])
                    ).fetchone()

                    # Вставляем только если карточки нет
                    if not existing:
                        conn.execute(
                            """INSERT INTO cards 
                            (english_word, russian_word, description, transcription, pronunciation_url) 
                            VALUES (?, ?, ?, ?, ?)""",
                            (word[0], word[1], word[2], word[3], word[4])
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
        # Генерируем случайное имя
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


if __name__ == "__main__":
    init_db()  # Инициализируем базу данных при запуске
    app.run(debug=True)
