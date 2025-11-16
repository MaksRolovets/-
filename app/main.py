from fastapi import FastAPI, HTTPException, Depends, Request, Response
from model import User, UserLogin, Content
from environs import Env
from passlib.context import CryptContext
from rbac import PremissionChecker, OwnershipCheker
from db import tokens, get_user_for_login, resources
from depencies import get_current_user, get_rate_limit_by_role
from security import create_jwt_access, create_jwt_refresh, decode_jwt
from contextlib import asynccontextmanager
from redis import asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi_limiter import FastAPILimiter


env = Env()
env.read_env()

myctx = CryptContext(schemes=["bcrypt"])

@asynccontextmanager
async def limiter_context(_:FastAPI):
    redis_connection = redis.from_url("redis://localhost:6379", encoding = "utf8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)
    yield
    await FastAPILimiter.close()



if env.str("MODE") == "DEV":
    app = FastAPI(lifespan=limiter_context)
else:
    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )

@app.post("/login")
def login_user(request : Request,user : UserLogin):
    user_data_ = get_user_for_login(user.username)
    if user_data_ is None:
        raise HTTPException(status_code=404, detail="Пользоваьеля с таким именем не существует!")
    #if not myctx.verify(user.password, user_data_.password):
    if user.password != user_data_.password:
        raise HTTPException(status_code=401, detail="Неправильный логин или пароль")
    token_access = create_jwt_access({"sub":user.username})
    token_refresh = create_jwt_refresh({"sub":user.username})
    tokens.append({"username":user.username,"token":token_refresh})
    return {"access_token":token_access, "refresh_token":token_refresh}

@app.get("/refresh")
def refresh(payload : str = Depends(decode_jwt)):
    if payload.get("type") == "refresh":
        for users in tokens:
            if users["username"] == payload.get("sub"):
                token = [create_jwt_refresh({"sub":users["username"]}),create_jwt_access({"sub":users["username"]})]
                users["token"] = token[0]
                return {"access_token":token[1], "refresh_token":token[0]}
    else:
        return{"message":"Токен должен иметь тип refresh"}
    return {"message":"Чтото пошло не так"}

@app.get("/admin", dependencies=[Depends(PremissionChecker(["admin"])),Depends(get_rate_limit_by_role)])
async def admin_point(request : Request):
    return {"message":"Admin panel"}

@app.get("/user", dependencies=[Depends(PremissionChecker(["user"])),Depends(get_rate_limit_by_role)])
async def user_point(request : Request,current_user : User = Depends(get_current_user)):
    return {"message":"User panel"}

@app.get("/guest")
async def guest_point():
    return {"message":"Guest panel"}

@app.get("/protected/{username}", dependencies=[Depends(PremissionChecker(["guest", "user"])),
                                                Depends(get_rate_limit_by_role),
                                                Depends(OwnershipCheker())])
async def get_protected(username : str, current_user : User = Depends(get_current_user)):
    try:
        return resources[username]["content"]
    except:
        raise HTTPException(status_code=404, detail="Not found")
    
@app.post("/protected/{username}", dependencies=[Depends(PremissionChecker(["user"])),Depends(get_rate_limit_by_role)])
async def post_protected(username:str, content_new : Content, current_user : User = Depends(get_current_user)):
    resources[username] = {"content":content_new.content, "is_public":content_new.is_public}
    return resources[username]["content"]

@app.put("/protected/{username}", dependencies=[
                                                Depends(PremissionChecker(["user"])),
                                                Depends(get_rate_limit_by_role),
                                                Depends(OwnershipCheker())])
async def post_protected(username:str, content_new : Content):
    resources[username].update(content=content_new.content)
    return {resources[username]["content"]}

@app.delete("/protected/{username}", dependencies=[Depends(PremissionChecker(["user"])),Depends(get_rate_limit_by_role)])
async def post_protected(username:str, current_user : User = Depends(get_current_user)):
    resources.pop(username)
    return {"Пользователь удален!"}



