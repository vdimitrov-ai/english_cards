# English Flashcards Game

Welcome to the English Flashcards Game! This web application is designed to help users learn English vocabulary through interactive games and flashcards.

## Features

- **Flashcards Study**: Learn new words using flashcards that display English words on one side and their Russian translations on the other.
- **King of the Hill Game**: Test your knowledge by matching English words with their Russian translations under a time limit.
- **Memory Game**: Find matching pairs of English and Russian words in a memory-style game.
- **Highscores**: Track and display the top scores for the King of the Hill game.

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Yandex GPT API Configuration
catalog_id = "your_catalog_id"        # Your Yandex GPT catalog ID
secret_key = "your_secret_key"        # Your Yandex GPT API key
GROQ_API_KEY = "your_groq_api_key"    # Your Groq API key

# System Prompt for AI Assistant
system_prompt = "You are an expert English language tutor. Your role is to:
- Provide clear and detailed explanations of English grammar rules
- Help with vocabulary, including usage examples and common collocations
- Assist with pronunciation, using phonetic transcriptions when needed
- Correct language mistakes politely and explain the corrections
- Give practical examples and context for better understanding
- Answer questions about English idioms and phrasal verbs
- Provide tips for language learning and practice
- Respond in the same language as the user's question (Russian or English)
- Format responses clearly, using examples and lists where appropriate

Always be encouraging and supportive in your responses, focusing on helping users improve their English skills."
```

To obtain the Yandex GPT API credentials:
1. Create an account at [Yandex Cloud](https://cloud.yandex.com/)
2. Navigate to the AI Services section
3. Create a new catalog and get your `catalog_id`
4. Generate an API key to get your `secret_key`

To obtain the Groq API key:
1. Create an account at [Groq](https://console.groq.com/)
2. Navigate to the API Keys section
3. Generate a new API key

**Note**: Never commit your `.env` file to version control. The repository includes a `.env.example` file as a template.

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
