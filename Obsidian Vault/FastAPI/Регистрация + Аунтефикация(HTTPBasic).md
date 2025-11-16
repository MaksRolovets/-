```python
from fastapi import FastAPI, Depends, status, HTTPException

from pydantic import BaseModel, field_validator

from fastapi.security import HTTPBasic,HTTPBasicCredentials

from passlib.context import CryptContext

import secrets

  
  

fake_db = []

  

app = FastAPI()

security = HTTPBasic()

myctx = CryptContext(schemes=["bcrypt"])

  

class UserBase(BaseModel):

    username : str

  

class User(UserBase):

    password : str        

  

class UserlnDB(UserBase):

    hashed_password : str

  

def check_username(name : str) -> UserlnDB | None:

    for user in fake_db:

        if name == user.username:

            return user

    return None

  

def auth_user(credentials : HTTPBasicCredentials = Depends(security)):

    user = check_username(credentials.username)

    if user is None:

        raise HTTPException(status_code=401, detail="Такого пользователя не существует", headers={"WWW-Authenticate":"Basic"})

    if secrets.compare_digest(user.username, credentials.username):

        if not myctx.verify(credentials.password,user.hashed_password):

            raise HTTPException(status_code=401, detail="Неправильный логин или пароль", headers={"WWW-Authenticate":"Basic"})

        return user

    else:

        raise HTTPException(status_code=401, detail="Неправильный логин или пароль", headers={"WWW-Authenticate":"Basic"})

  

@app.post("/register")

def register_user(user : User):

    if not check_username(user.username) is None:

        raise HTTPException(status_code=401, detail="Такое имя уже существует")

    fake_db.append(UserlnDB(username=user.username, hashed_password=myctx.hash(user.password)))

    return {"message": "Вы успешно зарегестрировались"}

  

@app.get("/login")

def login_user(user:User = Depends(auth_user)):

    return {"message":"Вы успешно авторизированы!", "userINFO":user}
```