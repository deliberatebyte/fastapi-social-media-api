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


my_posts = [
    {
        "title": "my favourite sports",
        "content": "table tennis",
        "id": 1,
    },
    {
        "title": "my favourite food",
        "content": "chicken biryani",
        "id": 2,
    },
]


def find_post(id):
    for p in my_posts:
        if p["id"] == id:
            return p


def find_post_index(id):
    for ind, post in enumerate(my_posts):
        if post["id"] == id:
            return ind


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
    latest_post = my_posts[len(my_posts) - 1]
    return latest_post


@app.get("/posts/{id}")
def get_post(id: int):
    post = find_post(id)
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
    index = find_post_index(id)
    if index == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {id} does not exist",
        )

    updated_post = post.model_dump()
    updated_post["id"] = id
    my_posts[index] = updated_post
    return {"data": updated_post}


@app.delete("/posts/{id}")
def delete_post(id: int):
    index = find_post_index(id)
    if index == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {id} does not exist",
        )

    my_posts.pop(index)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
