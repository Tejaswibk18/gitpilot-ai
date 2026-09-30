# GitPilot AI

**Agentic Git & GitHub Engineering Platform**

GitPilot AI is an AI-powered developer platform that uses **Google Gemini**, controlled Git tools, and human-in-the-loop approvals to automate and assist with Git and GitHub engineering workflows.

Instead of manually executing Git commands, developers can describe what they want in natural language and let GitPilot plan the required operations, inspect repository state, execute controlled tools, and request approval before performing sensitive changes.

---

## 🚀 Overview

GitPilot AI combines:

* **LLM-based reasoning** using Google Gemini
* **Agentic tool calling** for Git and GitHub operations
* **Human-in-the-loop approval** for write and destructive actions
* **AI-assisted Git conflict resolution**
* **Repository inspection and analysis**
* **GitHub Issues and Pull Request integration**
* **FastAPI backend**
* **Web-based developer interface**

The core design principle is:

> **The LLM decides what needs to be done; controlled tools decide how it is executed.**

---

## ✨ Key Features

### 🤖 Agentic Git Operations

GitPilot can understand natural-language Git requests and select the appropriate tools.

Current Git capabilities include:

* Repository status
* Repository information
* Git diff
* Commit history
* Branch creation
* Branch checkout
* Commit operations
* Push operations
* Merge operations
* Conflict detection and resolution
* Merge completion
* Merge abortion

The agent can inspect the repository before performing modifications and maintain execution state across tool calls.

---

### 🔐 Human-in-the-Loop Approval

GitPilot separates tools into different risk levels:

| Risk        | Behavior              |
| ----------- | --------------------- |
| Read        | Execute automatically |
| Write       | Require user approval |
| Destructive | Require user approval |

Examples of operations requiring approval:

* Creating branches
* Committing changes
* Pushing changes
* Merging branches
* Applying conflict resolutions
* Completing merges
* Aborting merges

This prevents the LLM from directly performing sensitive repository operations without user authorization.

---

### ⚔️ AI Git Conflict Resolution

GitPilot includes an AI-assisted merge conflict workflow.

The platform can:

1. Attempt a Git merge
2. Detect conflicted files
3. Inspect conflict regions
4. Send the conflict to Gemini
5. Generate a proposed resolution
6. Present the resolution for approval
7. Apply the resolution
8. Stage the resolved file
9. Complete the merge after approval

Conflict markers such as:

```text
<<<<<<< HEAD
current branch changes
=======
incoming branch changes
>>>>>>> feature-branch
```

are analyzed by the AI to produce a resolved version.

The resolution workflow is designed around:

```text
Detect → Inspect → Reason → Approve → Apply → Verify → Complete
```

---

### 🧠 Gemini Function Calling

GitPilot uses Google's Gemini API for agent reasoning and function/tool calling.

Gemini receives a controlled set of available tools and decides which tool is appropriate for the user's request.

Example:

> Create a branch for my authentication changes and inspect the current diff.

The agent can reason about the request and invoke tools such as:

```text
repository_status
repository_diff
create_branch
```

Tool execution remains controlled by the application rather than allowing the LLM to execute arbitrary shell commands.

---

### 🐙 GitHub Integration

GitPilot also integrates with GitHub APIs.

Current capabilities include:

* List issues
* Get issue details
* Comment on issues
* List pull requests
* Create pull requests
* Merge pull requests

This allows GitPilot to connect local Git operations with GitHub workflows.

Example future workflow:

```text
GitHub Issue
     ↓
Understand requirement
     ↓
Inspect repository
     ↓
Create branch
     ↓
Implement changes
     ↓
Run tests
     ↓
Commit
     ↓
Push
     ↓
Create Pull Request
```

---

## 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │      Developer      │
                         └──────────┬──────────┘
                                    │
                             Natural Language
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    GitPilot Agent   │
                         └──────────┬──────────┘
                                    │
                              Gemini LLM
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Tool Registry    │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
               Git Tools       GitHub Tools     AI Services
                    │               │               │
                    ▼               ▼               ▼
                 Local Git       GitHub API       Gemini
                    │
                    ▼
              Repository State
```

### Approval Flow

```text
              Gemini selects tool
                       │
                       ▼
                ┌─────────────┐
                │ Risk Check  │
                └──────┬──────┘
                       │
              ┌────────┴────────┐
              │                 │
             READ             WRITE
              │                 │
              ▼                 ▼
           Execute          Approval
                                │
                         ┌──────┴──────┐
                         │             │
                      Approve        Reject
                         │             │
                         ▼             ▼
                      Execute       Stop
                         │
                         ▼
                    Tool Result
                         │
                         ▼
                      Gemini
```

---

## 🧩 Conflict Resolution Architecture

```text
User Request
     │
     ▼
Gemini Agent
     │
     ▼
attempt_merge
     │
     ▼
Git Merge
     │
     ├── No Conflict ───────────────► Complete
     │
     └── Conflict
            │
            ▼
     detect_merge_conflicts
            │
            ▼
     get_conflict_details
            │
            ▼
       Gemini Analysis
            │
            ▼
     resolve_conflicts_ai
            │
            ▼
      Approval Required
            │
            ▼
     apply_conflict_resolution
            │
            ▼
       Verify Resolution
            │
            ▼
       complete_merge
```

---

## 📁 Project Structure

```text
gitpilot-ai/
│
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── agent.py
│   │   │   ├── approval.py
│   │   │   ├── evaluator.py
│   │   │   ├── gemini_agent.py
│   │   │   ├── git_tools.py
│   │   │   ├── state.py
│   │   │   └── tool_registry.py
│   │   │
│   │   ├── api/
│   │   │   ├── routes_agent.py
│   │   │   ├── routes_conflicts.py
│   │   │   ├── routes_github.py
│   │   │   └── routes_repository.py
│   │   │
│   │   ├── models/
│   │   │   └── repository.py
│   │   │
│   │   ├── services/
│   │   │   ├── conflict_service.py
│   │   │   ├── git_service.py
│   │   │   ├── github_service.py
│   │   │   ├── llm_service.py
│   │   │   └── repository_service.py
│   │   │
│   │   ├── tools/
│   │   │   ├── git/
│   │   │   │   ├── branch.py
│   │   │   │   ├── checkout.py
│   │   │   │   ├── commit.py
│   │   │   │   ├── conflict_resolver.py
│   │   │   │   ├── diff.py
│   │   │   │   ├── history.py
│   │   │   │   ├── merge.py
│   │   │   │   ├── push.py
│   │   │   │   ├── repository.py
│   │   │   │   └── status.py
│   │   │   │
│   │   │   └── github/
│   │   │       ├── issues.py
│   │   │       └── pull_request.py
│   │   │
│   │   └── main.py
│   │
│   ├── tests/
│   │   └── test_conflict_service.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
└── .gitignore
```

---

## 🛠️ Tech Stack

### Backend

* Python
* FastAPI
* Pydantic
* Google Gemini API
* Git CLI
* GitHub REST API

### Frontend

* HTML
* CSS
* JavaScript

### AI

* Google Gemini
* Function calling
* Structured tool execution
* AI-assisted conflict resolution

### Version Control

* Git
* GitHub

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd gitpilot-ai
```

### 2. Create a virtual environment

```bash
cd backend

python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file inside `backend/`:

```env
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_token
```

Never commit `.env` or API keys to Git.

---

## ▶️ Running the Application

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The FastAPI application will be available at:

```text
http://127.0.0.1:8000
```

The frontend is served by FastAPI when the `frontend/` directory is available.

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

---

## 🔌 API Endpoints

### Agent

```text
POST /api/agent/run
POST /api/agent/approve
GET  /api/agent/session/{session_id}
```

### Repository

```text
POST /api/repository/info
POST /api/repository/status
POST /api/repository/diff
POST /api/repository/history
```

### Conflict Resolution

```text
POST /api/conflicts/attempt-merge
POST /api/conflicts/detect
POST /api/conflicts/details
POST /api/conflicts/resolve-ai
POST /api/conflicts/apply
POST /api/conflicts/complete
POST /api/conflicts/abort
```

### GitHub

```text
POST /api/github/prs
POST /api/github/pr/create
POST /api/github/pr/merge
POST /api/github/issues
POST /api/github/issue/comment
```

---

## 🧪 Testing

The project includes automated tests for conflict-resolution functionality.

Run:

```bash
pytest
```

For a controlled Git conflict test, use a dedicated test repository rather than the GitPilot development repository.

A typical conflict scenario is:

```text
main
 │
 ├── branch A → modifies the same line
 │
 └── branch B → modifies the same line
                  │
                  ▼
                merge
                  │
                  ▼
              CONFLICT
                  │
                  ▼
             GitPilot AI
                  │
                  ▼
             AI Resolution
```

---

## 🔒 Safety Design

GitPilot is designed around controlled execution rather than arbitrary LLM-generated shell commands.

The LLM does **not** directly execute:

```bash
git <arbitrary-command>
```

Instead, it selects registered application tools.

Each tool defines:

* Name
* Description
* Parameters
* Risk level
* Approval requirement

Example:

```text
create_branch
    risk: write
    requires_approval: true
```

This provides an explicit security boundary between AI reasoning and repository modification.

---

## 🎯 Example Requests

GitPilot is designed to understand requests such as:

```text
Show me my current changes.
```

```text
Create a branch called feature/authentication.
```

```text
Show me the latest commits.
```

```text
Review the current diff.
```

```text
Merge feature/login into main.
```

```text
Resolve the current merge conflicts.
```

```text
Create a pull request from my current branch to main.
```

Future workflows can combine multiple operations:

```text
Create a branch for my authentication changes,
review the diff, commit the changes, push the branch,
and create a pull request.
```

---

## 🧠 Design Philosophy

GitPilot is built around an **agentic execution loop**:

```text
Understand
    ↓
Plan
    ↓
Select Tool
    ↓
Execute / Request Approval
    ↓
Observe Result
    ↓
Evaluate
    ↓
Continue or Finish
```

This allows the system to move beyond simple chatbot responses toward an AI engineering agent capable of interacting with real development workflows.

---

## 🚧 Future Improvements

Planned areas include:

* Persistent agent sessions
* Repository memory
* RAG over project documentation
* Automated test execution
* Issue-to-code workflows
* AI-generated commits
* Automated PR review
* CI/CD integration
* GitHub OAuth
* Multi-file conflict resolution
* Conflict-resolution verification
* Automatic rollback and recovery
* Dockerized deployment
* Persistent database-backed agent state
* More advanced GitHub automation

---

## 👨‍💻 Project Goal

GitPilot AI aims to provide a safer and more intelligent way for developers to interact with Git and GitHub.

Instead of remembering individual commands, developers can describe their engineering intent in natural language while GitPilot handles the reasoning, tool selection, repository inspection, execution, and approval workflow.

**Natural language → Agent reasoning → Controlled tools → Human approval → Verified engineering action**
