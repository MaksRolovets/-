
```python
from fastapi import FastAPI, Depends, HTTPException

from pydantic import BaseModel

from typing import Optional

from database import DB_NAME

import asyncpg

from asyncpg.exceptions import ForeignKeyViolationError

  

DATABASE_URL = "postgresql://myuser:1234@localhost/users"

  

async def get_db_connection():

    conn = await asyncpg.connect(DATABASE_URL)

    try:

        yield conn

    finally:

        await conn.close()

  

app = FastAPI()

  
  

class Todo(BaseModel):

    title : str

    description : str = None

    completed : bool = False

    user_id : int

  

class User(BaseModel):

    username : str

    password : str

  

@app.post("/register")

async def register(user : User, db : asyncpg.Connection = Depends(get_db_connection)):

    await db.execute('''INSERT INTO users (username, password) VALUES($1,$2)''', user.username, user.password)

    return {"message":"Регистрация прошла успешно"}

  

@app.post("/todos")

async def create_todo(user : Todo, db : asyncpg.Connection = Depends(get_db_connection)):

    try:

        await db.execute('''INSERT INTO todo (title, description, completed, user_id) VALUES ($1, $2, $3, $4)''', user.title, user.description, user.completed, user.user_id)

    except ForeignKeyViolationError:

        raise HTTPException(status_code=404, detail="Скорее всего вы пытаетесь добавить в несуществующий id")

    return "Данные добавлены"

  
  

@app.get("/todos/{id}")

async def get_todo(id : int,db : asyncpg.Connection = Depends(get_db_connection)):

    try:

        answer = await db.fetch('''SELECT u.username, t.title

                                    FROM users u

                                    JOIN todo t ON u.id = t.user_id

                                    WHERE u.id = $1;''',id)

        return answer

    except:

        raise HTTPException(status_code=404, detail="Not Found")

@app.put("/todos/{id}")

async def put_todo(id: int,user : Todo,db:asyncpg.Connection = Depends(get_db_connection) ):

    await db.execute('''UPDATE todo SET title=$1, description=$2, completed=$3, user_id = $4 WHERE id = $5''', user.title, user.description, user.completed,user.user_id, id)

    answer = await db.fetchrow('''SELECT * FROM todo WHERE id = $1''', id)

    return answer

  

@app.delete("/todos/{id}")

async def delete_todo(id : int, db:asyncpg.Connection = Depends(get_db_connection)):

    try:

        await db.execute('''DELETE FROM todo WHERE id = $1''', id)

    except:

        raise HTTPException(status_code=404, detail="id не существует")

    return "delete todo "            

  

@app.delete("/users/{user_id}")

async def delete_user(user_id : int, db : asyncpg.Connection = Depends(get_db_connection)):

    try:

        await db.execute('''DELETE FROM users WHERE id = $1''', user_id)

    except:

        raise HTTPException(status_code=404, detail="id не существует")

    return "delete user"
```
 **ВАЖНО**
ALTER TABLE todos ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
and
SELECT u.username, t.title

                                FROM users u

                                    JOIN todo t ON u.id = t.user_id

                                    WHERE u.id = $1;
```python
import sqlite3

DB_NAME = "database.sqlite"

  

def get_db_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn
```