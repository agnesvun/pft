from .cli import app
from .database import init_db


def main():
    init_db()
    app()
