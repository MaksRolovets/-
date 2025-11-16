main.py 
``` python
from fastapi import FastAPI, HTTPException, Depends, Request

from model import User

from environs import Env

from passlib.context import CryptContext

from db import chech_user_db, data, tokens

from security import create_jwt_access, create_jwt_refresh, decode_user_from_jwt

from slowapi import Limiter, _rate_limit_exceeded_handler

from slowapi.util import get_remote_address

from slowapi.errors import RateLimitExceeded

  
  

env = Env()

env.read_env()

  

myctx = CryptContext(schemes=["bcrypt"])

limiter = Limiter(key_func=get_remote_address)

  

if env.str("MODE") == "DEV":

    app = FastAPI()

else:

    app = FastAPI(

        docs_url=None,

        redoc_url=None,

        openapi_url=None

    )

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

  
  

@app.post("/register")

@limiter.limit("1/minute")

def register_user(request : Request,user : User): # для работы лимитера доьавить request

    if chech_user_db(user.username) is None:

        data.append(User(username=user.username, password=myctx.hash(user.password)))

    else:

        raise HTTPException(status_code=409, detail="Пользователем с таким именем уже существует!")

    return {"message":"Регистрация прошла успешно!"}

  

@app.post("/login")

@limiter.limit("5/minute")

def login_user(request : Request,user : User):

    user_data_ = chech_user_db(user.username)

    if user_data_ is None:

        raise HTTPException(status_code=404, detail="Пользоваьеля с таким именем не существует!")

    if not myctx.verify(user.password, user_data_.password):

        raise HTTPException(status_code=401, detail="Неправильный логин или пароль")

    token_access = create_jwt_access({"sub":user.username})

    token_refresh = create_jwt_refresh({"sub":user.username})

    tokens.append({"username":user.username,"token":token_refresh})

    return {"access_token":token_access, "refresh_token":token_refresh}

  

@app.get("/protected")

@limiter.limit("5/minute")

def protected(request : Request,payload : str = Depends(decode_user_from_jwt)):

    if payload.get("type") == "access":

        user = chech_user_db(payload.get("sub"))

        if user:

            return user

    else:

        raise HTTPException(status_code=401, detail="Токен должен иметь тип ACCESS")

  

@app.get("/refresh")

def refresh(payload : str = Depends(decode_user_from_jwt)):

    if payload.get("type") == "refresh":

        for users in tokens:

            if users["username"] == payload.get("sub"):

                token = [create_jwt_refresh({"sub":users["username"]}),create_jwt_access({"sub":users["username"]})]

                users["token"] = token[0]

                return {"access_token":token[1], "refresh_token":token[0]}

    else:

        return{"message":"Токен должен иметь тип refresh"}

    return {"message":"Чтото пошло не так"}
```

security
``` python
import jwt

from fastapi.security import OAuth2PasswordBearer

import datetime

from fastapi import Depends, HTTPException

from typing import Dict

  

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

  

SECRET_KEY = "sdkflksndfsefnafkjesjlfnkslf"

ALGHORITM = "HS256"

ACCESS_TOKEN_EXPIRE_MIN = 1

  

def create_jwt_access(dict : Dict):

    to_encode = dict.copy()

    expire = datetime.datetime.now() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)

    to_encode.update({"exp":expire.timestamp(), "type":"access"})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGHORITM)

  

def create_jwt_refresh(dict : Dict):

    to_encode = dict.copy()

    expire = datetime.datetime.now() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)

    to_encode.update({"exp":expire, "type":"refresh"})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGHORITM)

  

def decode_user_from_jwt(token : str = Depends(oauth2_scheme)):

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGHORITM])

        username = payload.get("sub")

        if not username:

            raise HTTPException(status_code=401, detail="Invalid token payload")

        return payload

    except jwt.ExpiredSignatureError:

        raise HTTPException(status_code=401, detail="Время жизни токена истекло")

    except jwt.InvalidTokenError:

        raise HTTPException(status_code=401, detail="Токен поврежден, изменен или подделан")
```

db
``` python
from model import User

import secrets

data : User = []

tokens = [] # username:token

  

def chech_user_db(username : str) -> User | None:

    for user in data:

        if secrets.compare_digest(username, user.username):

            return user

    return None
```

models
``` python
from pydantic import BaseModel

  

class Base(BaseModel):

    username : str

class User(Base):

    password : str
```
