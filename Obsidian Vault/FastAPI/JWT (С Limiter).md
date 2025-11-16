**main.py** 
```python
from fastapi import FastAPI, HTTPException, Depends, Request

from model import User

from db import data

from environs import Env

from passlib.context import CryptContext

import secrets

from security import get_user_from_token, create_jwt_token

from slowapi import Limiter, _rate_limit_exceeded_handler

from slowapi.util import get_remote_address

from slowapi.errors import RateLimitExceeded

  

env = Env()

env.read_env()

  

limiter = Limiter(key_func=get_remote_address)

  

myctx = CryptContext(schemes=["bcrypt"])

  

if env.str("MODE") == "DEV":

    app = FastAPI()

else:

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

  

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

  

def check_user_from_db(username : str) -> User | None:

    for user in data:

        if secrets.compare_digest(username, user.username):

            return user

    return None

  

@app.post("/register")

@limiter.limit("1/minute")

def register_user(request : Request, user : User):

    if check_user_from_db(user.username) is None:

        data.append(User(username=user.username, password=myctx.hash(user.password)))

    else:

        raise HTTPException(status_code=409, detail="Такой никнейм уже существует, используйте другой!")

    return {"message":"регистрация прошла успешно!", "login":data[0]}

#задать вопрос по raise

@app.post("/login")

@limiter.limit("5/minute")

def login_user(request : Request, user : User):

    user_data_ = check_user_from_db(user.username)

    if user_data_ is None:

        raise HTTPException(status_code=404, detail="Пользователя с таким именем не существует!")

    if not myctx.verify(user.password, user_data_.password):

        raise HTTPException(status_code=401, detail="Неправильный логин или пароль")

    token = create_jwt_token({"sub":user.username})

    return {"token": token}

#В login сделать проверку пороля и username при валидных данных вызывать функцию создания токена -> обращать к справке материалов  

@app.get("/protected")

def protected(current_name : str = Depends(get_user_from_token)):

    user = check_user_from_db(current_name)

    if user:

        return user

    else:

        return {"message":"ЧТОТО не то"}
```

security.py
```python
import jwt

from typing import Dict

from fastapi.security import OAuth2PasswordBearer

import datetime

from fastapi import Depends, HTTPException

  

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

  

SECRET_KEY = "ksdflkjseopfowpkf32"

ALGHORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MIN = 15

  

def create_jwt_token(dict : Dict):

    to_encode = dict.copy()

    expire = datetime.datetime.now() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)

    to_encode.update({"exp":expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGHORITHM)

  

def get_user_from_token(token : str = Depends(oauth2_scheme)):

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGHORITHM])

        username = payload.get("sub")

        if not username:

            raise HTTPException(status_code=401, detail="Invalid token payload")

        return username

    except jwt.ExpiredSignatureError:

        raise HTTPException(status_code=401, detail="Время жизни токена истекло")

    except jwt.InvalidTokenError:

        raise HTTPException(status_code=401, detail="Токен поврежден, изменен или подделан")

```

model.py
```python
from pydantic import BaseModel

  

class Base(BaseModel):

    username : str

class User(Base):

    password : str

  

class UserHS(Base):

    password_hs : str
```

db.py
```python
from model import User

data : User = []
```
