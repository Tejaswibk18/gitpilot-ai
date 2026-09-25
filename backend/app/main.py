from fastapi import FastAPI

from app.api.routes_repository import router as repository_router


app = FastAPI(
    title="GitPilot AI",
    description="Agentic Git and GitHub Engineering Platform",
    version="0.1.0",
)


app.include_router(repository_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "gitpilot-ai",
    }