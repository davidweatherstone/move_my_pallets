import sqlite3

import click
from flask import current_app, g


def get_db():
    """
    Return a SQLite database connection stored in the Flask application context.

    If the connection does not exist in the global 'g' object, it creates a new connection 
    using the database path specified in the current Flask application's configuration.
    Sets row_factory to sqlite3.Row for returning rows as dictionaries.

    Returns:
        sqlite3.Connection: SQLite database connection.
    """
    
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    
    return g.db


def close_db(e=None):
    """
    Close the SQLite database connection stored in the Flask application context.

    Args:
        e: Optional exception information.

    Closes the database connection stored in the global 'g' object if it exists.
    """

    db = g.pop("db", None)
    
    if db is not None:
        db.close()
        
        
def init_db():
    """
    Initialize the database by executing SQL commands from 'schema.sql' file.

    Uses the get_db() function to obtain a database connection.
    Reads and executes all SQL commands from 'schema.sql' to create database tables and structure.
    """
    
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
        
        
@click.command("init-db")
def init_db_command():
    """
    Flask CLI command to initialize the database.

    Clears existing data and creates new tables by calling the init_db() function.
    Outputs a message confirming successful initialization.
    """

    init_db()
    click.echo("Initialized the database")
    

def init_app(app):
    """
    Initialize the Flask application with database-related functionality.

    Registers the close_db() function to be called when the application context is torn down.
    Adds the init_db_command() as a CLI command to the Flask application for database initialization.

    Args:
        app: Flask application instance.
    """
    
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)