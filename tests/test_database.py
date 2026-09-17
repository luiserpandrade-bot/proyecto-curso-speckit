from app.database import get_connect_args, get_db


def test_connect_args_sqlite_vs_postgres():
    sqlite_args = get_connect_args("sqlite:///./gastos.db")
    assert sqlite_args == {"check_same_thread": False}

    postgres_args = get_connect_args("postgresql://user:secret@localhost:5432/gastos")
    assert postgres_args == {}


def test_get_db_generator():
    db_gen = get_db()
    session = next(db_gen)
    assert session is not None
    try:
        next(db_gen)
    except StopIteration:
        pass
