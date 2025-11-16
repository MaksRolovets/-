```python
from fastapi import FastAPI, HTTPException

from contextlib import asynccontextmanager

from databases import Database

from pydantic import BaseModel

from typing import List

  

DATABASE_URL = "postgresql://myuser:1234@localhost/mtdatabase"

  

database = Database(DATABASE_URL)

  

class UserBase(BaseModel):

    username : str

    email : str

  

class UserCreate(UserBase):

    pass

  

class UserReturn(UserBase):

    id : int

  

class TodoCreate(BaseModel):

    title : str

    descriptions : str = None

    completed : bool = False

  

class TodoReturn(TodoCreate):

    id:int

  

class UserTodos(BaseModel):

    username: str

    todos: List[TodoReturn]

  

  # Пример расширения моделей для учебных целей:

# class UserCreateWithPassword(UserCreate):

#     password: str

#     password_confirm: str

  

# class UserPrivateInfo(UserReturn):

#     created_at: datetime

#     last_login: datetime

  

@asynccontextmanager

async def lifespan(app: FastAPI):

    await database.connect()

    yield

    await database.disconnect()

  

app = FastAPI(lifespan=lifespan)

  

@app.post("/users/", response_model=UserReturn)

async def  create_user(user: UserCreate):

    query = """

        INSERT INTO users (username, email)

        VALUES (:username, :email)

        RETURNING id  /* Получаем автоматически сгенерированный ID */

    """

    try:

        #async with database.transaction():

        user_id = await database.execute(

            query=query,

            values=user.model_dump()

        )

  

        return UserReturn(

            id=user_id,

            **user.model_dump(mode='json')

        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Ошибка при создании пользователя: {str(e)}"

        )

@app.get("/users/{user_id}", response_model=UserReturn)

async def get_user(user_id : int):

    query = '''SELECT id, username, email FROM users WHERE id = :user_id'''

    try:

        result = await database.fetch_one(

            query=query,

            values={"user_id":user_id}

        )

    except Exception:

        raise HTTPException(

            status_code=500,

            detail=f"Ошибка получения пользоватедя {str(Exception)}"

        )

    if not result:

        raise HTTPException(

            status_code=404,

            detail="Пользователя с указанныи ID не найден"

        )

    return UserReturn(

        id = result["id"],

        username=result["username"],

        email=result["email"]

    )

  

@app.put("/users/{user_id}", response_model=UserReturn)

async def update_user(user_id : int, user : UserCreate):

    query = '''UPDATE users SET username = :username, email = :email WHERE id = :user_id RETURNING id'''

  

    values = {

        "user_id": user_id,

        "username": user.username,

        "email":user.email

    }

    try:

        result = await database.execute(

            query=query,

            values=values

        )

        if not result:

            raise HTTPException(

                status_code=404,

                detail="Пользователя с указанныи ID не найден"

            )

        return UserReturn(**user.model_dump(), id= result)

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Ошибка обновления пользователя: {str(e)}"

        )

@app.delete("/users/{user_id}", response_model = dict)

async def delete_user(user_id : int):

    query = '''DELETE FROM users WHERE id = :user_id RETURNING id'''

    try:

        deleted_id = await database.execute(

            query=query,

            values = {"user_id":user_id}

        )

        if not deleted_id:

            raise HTTPException(

                status_code=404,

                detail="Пользователь с указанным ID не найден"

            )

        return {"message":"Польщователь успешно удален"}

    except HTTPException:

        raise

    except Exception:

        raise HTTPException(

            status_code=500,

            detail=f"Ошибка удаления пользователя: {str(Exception)}"

        )

@app.post("/todos/{user_id}", response_model=TodoReturn)

async def create_todo(user_id : int,todo : TodoCreate):

    query = '''INSERT INTO todos(title, descriptions, compelted, user_id) VALUES (:title, :descriptions, :completed, :user_id) RETURNING id'''

    values = {**todo.model_dump(),

              "user_id":user_id}

    try:

        result = await database.execute(

            query=query,

            values=values

        )

        return TodoReturn(id=result, **todo.model_dump(mode='json'))

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Ошибка при создании заметки {str(e)}"

        )

@app.get("/todos/{user_id}", response_model=UserTodos)

async def get_todo(user_id : int):

    query = '''SELECT u.username, t.id, t.title, t.descriptions, t.compelted FROM users u JOIN todos t ON u.id = t.user_id WHERE u.id = :user_id'''

    try:

        result = await database.fetch_all(

            query=query,

            values={"user_id":user_id}

        )

        if not result:

            raise HTTPException(

                status_code=404,

                detail="Пользователя с таким ID не существует"

            )

        todos = [

        TodoReturn(

            id=r["id"],

            title=r["title"],

            descriptions=r["descriptions"],

            completed=r["compelted"]

        )

        for r in result

    ]

        return {"username":result[0]["username"], "todos":todos}

  

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Ошибка получения заметки {str(e)}"

        )

  

@app.put("/todos/{id}", response_model=TodoReturn)

async def update_todo(id : int, todo : TodoCreate):

    query = '''UPDATE todos SET title=:title, descriptions=:descriptions, compelted=:compelted WHERE id = :id RETURNING id'''

    values ={

        "title":todo.title,

        "descriptions":todo.descriptions,

        "compelted":todo.completed,

        "id":id

    }

    try:

        result = await database.execute(

            query=query,

            values=values

        )

        if not result:

            raise HTTPException(

                status_code=404,

                detail="Пользователя с таким ID не существует"

            )

        return TodoReturn(

            title=values["title"],

            descriptions=values['descriptions'],

            completed=values['compelted'],

            id=values['id']

        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Ошибка обновления заметки: {str(e)}"

        )

    except HTTPException:

        raise

  

@app.delete("/todos/{id}")

async def delete_todo(id:int):

    query = '''DELETE FROM todos WHERE id=:id RETURNING id'''

    try:

        result = await database.execute(

            query=query,

            values={"id":id}

        )

        if not result:

            raise HTTPException(

                status_code=404,

                detail="Заметка с указанным ID не найдена"

            )

        return {"message":"Заметка успешна удалена", "id":result}

  

    except HTTPException:

        raise

    except Exception:

        raise HTTPException(

            status_code=500,

            detail=f"Ошибка удаления заметки: {str(Exception)}")

```