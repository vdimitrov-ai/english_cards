# English Flashcards Game

Welcome to the English Flashcards Game! This web application is designed to help users learn English vocabulary through interactive games and flashcards.

## Features

- **Flashcards Study**: Learn new words using flashcards that display English words on one side and their Russian translations on the other.
- **King of the Hill Game**: Test your knowledge by matching English words with their Russian translations under a time limit.
- **Memory Game**: Find matching pairs of English and Russian words in a memory-style game.
- **Highscores**: Track and display the top scores for the King of the Hill game.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/english-flashcards-game.git
   cd english-flashcards-game
   ```

2. **Set up a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   - The application will automatically create and initialize the database when you first run it.

## Usage

1. **Run the application**:
   ```bash
   python app.py
   ```

2. **Access the application**:
   - Open your web browser and go to `http://127.0.0.1:5000`.

3. **Navigate through the application**:
   - Use the navigation menu to access different features like studying flashcards, playing games, and viewing highscores.

## Project Structure

- `app.py`: The main application file containing the Flask routes and database logic.
- `templates/`: Contains HTML templates for rendering the web pages.
- `static/`: Contains static files like CSS for styling the application.
- `db/`: Directory where the SQLite database is stored.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgments

- Thanks to the Flask community for providing excellent resources and support.
- Icons and images used in the project are sourced from [source].
