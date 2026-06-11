from dotenv import load_dotenv
import os
import psycopg
from fastapi import HTTPException
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

pool = ConnectionPool(conninfo=DATABASE_URL)

def fetch_one(query: str, params=None):
    try: 
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query, params)
                return cur.fetchone()
    except psycopg.Error:
        print("DB Error", psycopg.Error)
        raise HTTPException(status_code=500, detail="Database error")

def fetch_all(query: str, params=None):
    try: 
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query, params)
                return cur.fetchall()
    except psycopg.Error:
        print("DB Error", psycopg.Error)
        raise HTTPException(status_code=500, detail="Database error")

def execute(query: str, params=None):
    try: 
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query, params)
                conn.commit()
    except psycopg.Error:
        print("DB Error", psycopg.Error)
        raise HTTPException(status_code=500, detail="Database error")