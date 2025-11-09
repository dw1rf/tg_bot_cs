import pymysql
from typing import Any, Iterable
from .config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, DB_SSL_MODE

def db_conn():
    ssl_opt = {"ssl": {}} if DB_SSL_MODE == "REQUIRED" else None
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, ssl=ssl_opt
    )

def query_one(sql: str, params: Iterable[Any] | None = None):
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()

def query_all(sql: str, params: Iterable[Any] | None = None):
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()

def exec_(sql: str, params: Iterable[Any] | None = None):
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        conn.commit()
