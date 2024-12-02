from fastapi import APIRouter, HTTPException, Depends
from services.firestore import create_user, get_user_by_id, get_user_by_email
from auth import verify_password, create_access_token, hash_password, get_current_user
from pydantic import BaseModel, EmailStr

router = APIRouter()

# Pydantic model for user registration
class UserRegister(BaseModel):
    username: str
    email: EmailStr  # Validates email format
    password: str

@router.post("/api/register")
async def register(user: UserRegister):
    # Check if the username already exists
    existing_user = get_user_by_id(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password and create user data
    hashed_password = hash_password(user.password)
    user_data = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
    }

    # Save user to Firestore
    create_user(user.username, user_data)
    return {"message": "User registered successfully"}


# Pydantic model for login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/api/login")
async def login(user: UserLogin):
    # Fetch user from Firestore using the email
    stored_user = get_user_by_email(user.email)
    if not stored_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify the provided password against the hashed password
    if not verify_password(user.password, stored_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Create a JWT token
    token = create_access_token({"sub": stored_user["username"]})
    return {"token": token}