import sqlite3
from openai import OpenAI
import os
import json

conn = sqlite3.connect('data/Chinook.db')

def get_table_names():
    table_names = []
    tables = conn.execute('Select name from sqlite_master where type="table"')
    for table in tables.fetchall():
        table_names.append(table[0])

    return table_names

def get_column_names(table_name):
    """Return a list of column names."""
    column_names = []
    columns = conn.execute(f"PRAGMA table_info('{table_name}');").fetchall()
    for col in columns:
        column_names.append(col[1])
    return column_names


def get_database_info():
    """Return a list of dicts containing the table name and columns for each table in the database."""
    table_dicts = []
    for table_name in get_table_names():
        columns_names = get_column_names(table_name)
        table_dicts.append({"table_name": table_name, "column_names": columns_names})
    return table_dicts
  

database_schema = get_database_info()

database_schema_string = "\n".join(
    f"Table: {table['table_name']}\nColumns: {', '.join(table['column_names'])}" for table in database_schema
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "ask_database",
            "description": "Use this function to answer user questions about music. Input should be a fully formed SQL query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"""
                                SQL query extracting info to answer the user's question.
                                SQL should be written using this database schema:
                                {database_schema_string}
                                The query should be returned in plain text, not in JSON.
                                """,
                    }
                },
                "required": ["query"],
            },
        }
    }
]

def ask_database(query):
    results = str(conn.execute(query).fetchall())
    return results


client = OpenAI(
    api_key=os.environ.get("OPENAPI_API_KEY")
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "Answer user questions by generating SQL queries"
        },
        {
            "role": "user",
            "content": "What is the name of the album with the most tracks?"
        }
    ], 
    model="gpt-3.5-turbo",
    tools=tools
)

tool_call = chat_completion.choices[0].message.tool_calls[0]

if tool_call.function.name == 'ask_database':
    query = json.loads(tool_call.function.arguments)["query"]
    result = ask_database(query)
    print(result)