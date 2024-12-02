from fastapi import FastAPI
from services.firestore import test_firestore_connection
from auth import create_access_token, verify_access_token
from routers import user, plants

app = FastAPI(docs_url="/")

@app.get("/")
def root():
    if test_firestore_connection():
        return {"message": "Firestore is connected!"}
    else:
        return {"message": "Firestore connection failed!"}

app.include_router(user.router)
app.include_router(plants.router)
