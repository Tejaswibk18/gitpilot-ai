from pydantic import BaseModel, Field


class RepositoryStatus(BaseModel):
    branch: str
    clean: bool

    staged: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)
    untracked: list[str] = Field(default_factory=list)


class CommitInfo(BaseModel):
    hash: str
    short_hash: str
    author: str
    date: str
    message: str


class RemoteInfo(BaseModel):
    name: str
    fetch_url: str
    push_url: str


class RepositoryInfo(BaseModel):
    path: str
    branch: str
    remotes: list[RemoteInfo] = Field(default_factory=list)