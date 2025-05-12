# Getting Started with the Discord Bot Project

Welcome to the Discord Bot project! This guide will help you set up the development environment and understand the workflow for contributing to the project.

## Prerequisites
1. Install Python 3.8+ (tested with 3.11) from [python.org](https://www.python.org/).
2. Install `pip` (Python package manager) if not already installed.
3. Install `git` for version control.

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/NaymDev/horizon-bot.git
   cd discord-bot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `config.json` file in the root directory (refer to `config.example.json` for structure).

5. Run the bot:
   ```bash
   python .\horizon_bot_project\
   ```

## Commit Conventions
We follow [Conventional Commits](https://www.conventionalcommits.org/) for clear and structured commit messages. Examples:
- `feat: add new command for user stats`
- `fix: resolve issue with message logging`
- `docs: update README with setup instructions`

## Development Tips
- Use feature branches for new work (e.g., `feature/add-logging`).
- Run `flake8` or `black` for code formatting before committing.
- Write unit tests for new features and run them with `pytest`.

## Need Help?
Feel free to reach out in the project Discord channel or open an issue in the repository.
