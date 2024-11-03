# Contributing Guide

Thank you for your interest in contributing to English Flashcards! This document provides guidelines and instructions for contributors.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/english_cards.git
   cd english_cards
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Project Structure

```
english_cards/
├── app.py              # Main application file
├── configs.py          # Configurations and constants
├── static/             # Static files (CSS, images)
├── templates/          # HTML templates
├── db/                 # SQLite database
└── tests/             # Tests
```

## Development Guidelines

### Code

1. Use Python 3.8 or higher
2. Follow PEP 8 style guide
3. Add type hints for new functions
4. Maximum line length is 120 characters
5. Use meaningful variable and function names

### Commits

1. Use clear commit messages in English
2. Start the message with a verb in imperative mood:
   - "Add feature..."
   - "Fix bug..."
   - "Update documentation..."
   - "Refactor..."

### Pull Requests

1. Create a separate branch for each feature/fix
2. PR title should briefly describe the changes
3. In PR description include:
   - What changed
   - Why it's needed
   - How to test the changes

## Testing

1. Add tests for new functionality
2. Run tests before creating PR:
   ```bash
   pytest
   ```

## Code Style

The project uses the following tools for code quality:

1. flake8 - linter
2. black - code formatter
3. isort - import sorter
4. mypy - type checker

Run checks before submitting PR:
```bash
flake8 .
black .
isort .
mypy .
```

## Documentation

1. Add docstrings for new functions
2. Update README.md when adding new features
3. Comment complex code sections

## Database

1. All DB schema changes must be reflected in `init_db()`
2. Add migrations when changing DB structure

## Security

1. Don't commit sensitive data
2. Use parameterized queries for DB
3. Validate user input

## Questions and Discussions

1. Use Issues for bug reports and feature requests
2. Ask questions in Discussions
3. Check existing Issues before creating new ones

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the main project.

## Contact

If you have questions, you can:
- Create an Issue
- Email dimitrov_rabota@mail.ru