import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Response
from pydantic import BaseModel
from typing import Optional
from random import randrange
import time

app = FastAPI()

load_dotenv()

while True:
    try:
        conn = psycopg.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )

        cur = conn.cursor(row_factory=dict_row)
        print("Database connection was successful!")
        break

    except psycopg.Error as error:
        print("Connection to database failed")
        print(f"Error: {error}")
        time.sleep(2)


class Post(BaseModel):
    title: str
    content: str
    published: bool = True
    rating: Optional[int] = None


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/posts")
def get_posts():
    cur.execute("""SELECT * FROM posts """)
    posts = cur.fetchall()
    return {"data": posts}


@app.get("/posts/latest")
def latest_posts():
    cur.execute("""SELECT * FROM posts ORDER BY created_at DESC LIMIT 1""")
    latest_post = cur.fetchone()
    return latest_post


@app.get("/posts/{id}")
def get_post(id: int):
    cur.execute("""SELECT * FROM posts WHERE id = (%s) """, (id,))
    post = cur.fetchone()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {id} was not found",
        )
        # response.status_code = status.HTTP_404_NOT_FOUND
        # return {"message": f"post with id: {id} was not found"}

    return {"data": post}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post):
    try:
        query = "INSERT INTO posts (title, content, published) VALUES (%s,%s,%s) RETURNING *"
        cur.execute(query, (post.title, post.content, post.published))
        new_post = cur.fetchone()
        conn.commit()
        return {"data": new_post}

    except psycopg.Error:
        conn.rollback()
        raise

    # Never use f-strings or string concatenation to insert user input into SQL.
    # It can lead to SQL Injection, where attackers inject malicious SQL commands.
    #
    # Always use parameterized queries:
    # cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    #
    # %s = placeholder; (username,) = actual parameter (tuple).
    # This keeps user input separate from SQL code.
    # Psycopg treats parameters as data, not executable SQL.


@app.put("/posts/{id}")
def update_post(post: Post, id: int):
    cur.execute(
        """UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING * """,
        (
            post.title,
            post.content,
            post.published,
            id,
        ),
    )
    updated_post = cur.fetchone()
    conn.commit()

    if updated_post == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {id} does not exist",
        )

    return {"data": updated_post}


@app.delete("/posts/{id}")
def delete_post(id: int):
    cur.execute("""DELETE FROM posts WHERE id = %s RETURNING *""", (id,))
    deleted_post = cur.fetchone()
    conn.commit()

    if deleted_post == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {id} does not exist",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
