from fastapi import FastAPI
from routers import user, plants
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(docs_url="/")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow cookies to be included in requests
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(user.router)
app.include_router(plants.router)
