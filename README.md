# AI Integration Chatbot

A command-line chatbot that loads a CSV file into a local SQLite database,
then answers your questions using the OpenAI Chat Completions API — pulling
in matching rows from the CSV as extra context. Every question and answer is
logged to the database.

## Features

- Load any CSV into a local SQLite database via a file picker
- Ask natural-language questions; relevant rows are pulled in as context
- Conversation history logged to `local_database.db`
- Repeats the last answer instantly if you ask the same question twice

## Setup

1. **Clone the repo and install dependencies**

   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   pip install -r requirements.txt
   ```

2. **Add your OpenAI API key** (choose one):

   - Environment variable (recommended):
     ```bash
     export OPENAI_API_KEY="sk-..."
     ```
   - Or copy the example config file and paste your key in:
     ```bash
     cp config.example.txt config.txt
     ```
     `config.txt` is already in `.gitignore`, so it won't be committed.

3. **Run it**

   ```bash
   python ai_integration.py
   ```

   You'll be prompted to select a CSV file and give it a table name. After
   that, just start chatting — type `help` for commands or `exit` to quit.

## Requirements

- Python 3.9+
- Tkinter (bundled with most Python installs; on Linux you may need
  `sudo apt install python3-tk`)
- An OpenAI API key

## Notes

- The CSV you load should include a `description` column, since that's what
  gets pulled in as context for the chatbot.
- `local_database.db` is created at runtime and is git-ignored — delete it
  any time to start fresh.

## License

[MIT](LICENSE)
