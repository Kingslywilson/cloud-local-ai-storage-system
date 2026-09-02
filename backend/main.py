from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.files import router as files_router
from database import engine
from models import Base
from routers.auth import router as auth_router
from routers.folders import router as folders_router

app = FastAPI(
    title="Gradious Cloud Storage API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(files_router)
app.include_router(folders_router)


@app.get("/")
def home():
    return {
        "message": "Cloud Storage API is running",
        "database": "MySQL connected"
    }