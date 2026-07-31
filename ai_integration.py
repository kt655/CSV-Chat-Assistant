"""
AI Integration Chatbot
-----------------------
A simple command-line chatbot that:
  1. Lets the user load a CSV file into a local SQLite database.
  2. Answers questions using the OpenAI Chat Completions API, using
     matching rows from the CSV as extra context.
  3. Logs every question/answer pair to the database.

Setup:
  1. Copy `config.example.txt` to `config.txt` and paste in your OpenAI
     API key (or set the OPENAI_API_KEY environment variable instead).
  2. Install dependencies: `pip install -r requirements.txt`
  3. Run: `python ai_integration.py`
"""

import os
import sqlite3
import requests
import tkinter as tk
from tkinter import filedialog
import pandas as pd

CONFIG_FILE = "config.txt"
DEFAULT_TABLE = "nike_shoes_sales"


# --------------------------------------------------------------------------- #
# Database helpers
# --------------------------------------------------------------------------- #
def initialize_database(database_name):
    """Create the QAPairs table if it doesn't already exist."""
    with sqlite3.connect(database_name) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS QAPairs
               (question TEXT, answer TEXT)"""
        )


def insert_qa_pair(question, answer, database_name):
    """Log a question/answer pair to the database."""
    with sqlite3.connect(database_name) as conn:
        conn.execute(
            "INSERT INTO QAPairs (question, answer) VALUES (?, ?)",
            (question, answer),
        )


def read_data_from_database(database_name, table_name):
    """Read an entire table into a DataFrame."""
    try:
        with sqlite3.connect(database_name) as conn:
            return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        print(f"Error reading data from database: {e}")
        return None


def insert_csv_into_database(file_path, table_name, database_name):
    """Load a CSV file into a SQLite table (replacing it if it exists)."""
    try:
        with sqlite3.connect(database_name) as conn:
            df = pd.read_csv(file_path)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"CSV data inserted into '{table_name}' table in database '{database_name}'.")
    except Exception as e:
        print(f"Error inserting CSV data into database: {e}")


def get_last_bot_response(database_name):
    """Return the most recent bot answer, or None if there isn't one."""
    with sqlite3.connect(database_name) as conn:
        row = conn.execute(
            "SELECT answer FROM QAPairs ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
    return row[0] if row else None


# --------------------------------------------------------------------------- #
# Dataset helpers
# --------------------------------------------------------------------------- #
def filter_dataset(df, keyword):
    """Return the 'description' values of rows that contain `keyword`."""
    if df is None:
        return []

    mask = df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)
    filtered_df = df[mask]

    if not hasattr(filter_dataset, "printed_columns"):
        print("Available columns:", filtered_df.columns.tolist())
        filter_dataset.printed_columns = True

    if "description" in filtered_df.columns:
        return filtered_df["description"].tolist()

    print("Error: 'description' column not found.")
    return []


# --------------------------------------------------------------------------- #
# OpenAI API helpers
# --------------------------------------------------------------------------- #
def read_api_key():
    """Look for an API key in the environment first, then in config.txt."""
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        return env_key.strip()

    try:
        with open(CONFIG_FILE, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"No API key found. Set OPENAI_API_KEY or create '{CONFIG_FILE}'.")
        return None


def send_to_chatgpt(input_string, extra_info="", max_tokens=200):
    """Send a prompt (plus optional context) to the OpenAI Chat API."""
    combined_input = (input_string + " " + extra_info)[:150]

    api_key = read_api_key()
    if not api_key:
        return None

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-3.5-turbo-0125",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": combined_input},
        ],
        "max_tokens": max_tokens,
    }

    response = None
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        print(f"Error sending request to OpenAI API: {e}")
        if response is not None:
            print("API Response:", response.text)
        return None


# --------------------------------------------------------------------------- #
# File selection
# --------------------------------------------------------------------------- #
def select_file():
    """Open a native file picker and return the chosen path."""
    root = tk.Tk()
    root.withdraw()  # Hide the empty root window
    file_path = filedialog.askopenfilename(title="Select a File", filetypes=[("All Files", "*.*")])
    root.destroy()
    return file_path


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #
def main():
    database_name = "local_database.db"
    initialize_database(database_name)

    print("Please select the CSV file containing data to insert into the database.")
    file_path = select_file()
    if not file_path:
        print("No file selected. Exiting...")
        return

    table_name = input("Enter the table name to insert CSV data into: ").strip() or DEFAULT_TABLE
    insert_csv_into_database(file_path, table_name, database_name)

    while True:
        input_command = input("You: ").strip()

        if input_command.lower() == "exit":
            print("Goodbye!")
            break

        elif input_command.lower() == "help":
            print("Bot: How can I assist you? You can ask questions, request to read a file, or ask for explanations about specific code.")

        elif input_command.lower() == "read file":
            print("Bot: Please select the file you want to read.")
            selected = select_file()
            if selected:
                bot_response = send_to_chatgpt("inform me", max_tokens=100)
                insert_qa_pair("read file", bot_response, database_name)
                print(f"Bot: {bot_response}")

        else:
            last_bot_response = get_last_bot_response(database_name)

            if last_bot_response and last_bot_response.lower() == input_command.lower():
                print(f"Bot: {last_bot_response}")
            else:
                df = read_data_from_database(database_name, table_name)
                extra_info = " ".join(filter_dataset(df, input_command.lower())) if df is not None else ""

                bot_response = send_to_chatgpt(input_command, extra_info, max_tokens=150)
                print("Bot:", bot_response)
                insert_qa_pair(input_command, bot_response, database_name)


if __name__ == "__main__":
    main()
