from fastapi.security import OAuth2PasswordRequestForm
from grpc import Status
from fastapi import APIRouter, Depends, HTTPException, Request

from endpoints.helper.db_init import User, get_session
from endpoints.helper.jwt_handler import create_access_token
from endpoints.helper.password_checker import gen_hashed_password, get_user, verify_password
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/login")
async def login_for_access_token(request: Request):
    request = await request.json()
    print("Login request:", request )
    user = get_user(request.get("email"))
    print("User:", user)
    if not user or not verify_password(request.get("password"), user["hashed_password"]):
        return JSONResponse(
            status_code=401,
            content={"error": "Incorrect username or password"}
        )   
    access_token = create_access_token(
        data={"sub": user["username"], "username": user["username"]}
    )
    return JSONResponse(
        status_code=200,
        content={"access_token": access_token, "token_type": "bearer"}
    )


@router.post("/register")
async def register_user(request: Request):
    data = await request.json()
    print (data)
    username = data.get("email")
    password = data.get("password")

    if not username or not password:
        return JSONResponse(
            status_code=400,
            content={"error": "Username and password are required"}
        )
    
    existing_user = get_user(username)
    if existing_user:
        return JSONResponse(
            status_code=400,
            content={"error": "Username already exists"}
        )
    
    hashed_password = gen_hashed_password(password)

    new_user = User(
        username=username,
        password=hashed_password
    )

    session = next(get_session())   
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return JSONResponse(
        status_code=201,
        content={
            "message": "User registered successfully",
            "user": {
                "username": new_user.username,
            }
        }
    )


