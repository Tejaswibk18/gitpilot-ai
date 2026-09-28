from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_repository import router as repository_router
from app.api.routes_agent import router as agent_router
from app.api.routes_github import router as github_router
from app.api.routes_conflicts import router as conflicts_router


app = FastAPI(
    title="GitPilot AI",
    description="Agentic Git and GitHub Engineering Platform",
    version="0.1.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repository_router)
app.include_router(agent_router)
app.include_router(github_router)
app.include_router(conflicts_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "gitpilot-ai",
    }


# Mount Frontend UI static files
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")