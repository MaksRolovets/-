```python
from fastapi import FastAPI, Depends, HTTPException, status

from pydantic import BaseModel

from fastapi.openapi.docs import get_swagger_ui_html

from fastapi.openapi.utils import get_openapi

from fastapi.security import HTTPBasic, HTTPBasicCredentials

from passlib.context import CryptContext

from environs import Env

import secrets

  

env = Env()

env.read_env()

  

USERNAME_ADMIN = env.str("DOCS_USER")

PASSWORD_ADMIN = env.str("DOCS_PASSWORD")

MODE = env.str("MODE").strip().upper()

  

security = HTTPBasic()

myctx = CryptContext(["bcrypt"])

  

def auth_user(credentials : HTTPBasicCredentials = Depends(security)):

    correct_username = secrets.compare_digest(credentials.username, USERNAME_ADMIN)

    correct_password = secrets.compare_digest(credentials.password, PASSWORD_ADMIN)

    if not (correct_username and correct_password):

        raise HTTPException(status_code=401, detail="Неправильные данные для доступа к docs", headers={"WWW-Authenticate": "Basic"})

    return credentials.username

  

if MODE == "DEV":

    app = FastAPI(

        docs_url=None,

        redoc_url=None,

        openapi_url=None

    )

  

    @app.get("/docs", include_in_schema=True)

    def docs(_ : str = Depends(auth_user)):

        return get_swagger_ui_html(openapi_url="/openapi.json", title= "Docs")

  

    @app.get("/openapi.json", include_in_schema=False)

    def openapi_get(_ : str = Depends(auth_user)):

        return get_openapi(

            title="Docs",

            routes=app.routes,

            version="1.0.0"

        )

else:

    app = FastAPI(

        docs_url=None,

        redoc_url=None,

        openapi_url=None

    )

  

class BaseUser(BaseModel):

    username : str

  

class User(BaseUser):

    password : str

  

class Userhs(BaseUser):

    hash_password : str

  

@app.get("/ping")

def ping():

    return {"message": "pong"}
```