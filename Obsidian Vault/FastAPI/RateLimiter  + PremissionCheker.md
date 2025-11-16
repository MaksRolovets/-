
```python
async def get_rate_limit_by_role(request: Request,

                                response: Response,

                                current_user: User = Depends(get_current_user)) -> RateLimiter:

    if "admin" in current_user.roles:

        limiter = RateLimiter(times=10, minutes=1)

    elif "user" in current_user.roles:

        limiter = RateLimiter(times=5, minutes=1)

    else:

        limiter = RateLimiter(times=3, minutes=1)

    await limiter(request=request, response=response)

@app.get("/user", dependencies=[Depends(get_rate_limit_by_role)])

@PremissionChecker(["user"])

async def user_point(request : Request,current_user : User = Depends(get_current_user)):

    return {"message":"User panel"}


```
