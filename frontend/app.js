const API_BASE = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
    ? window.location.origin.replace(/\/$/, "") + "/api"
    : "http://localhost:8000/api";

let currentTarget = "";
let currentSessionId = null;
let currentApprovalId = null;
let selectedConflictFile = null;

// DOM ELEMENTS
const targetInput = document.getElementById("targetInput");
const tokenInput = document.getElementById("tokenInput");
const connectBtn = document.getElementById("connectBtn");
const connectBtnText = document.getElementById("connectBtnText");
const connectSpinner = document.getElementById("connectSpinner");
const repoStatusPill = document.getElementById("repoStatusPill");
const statusPillText = document.getElementById("statusPillText");

const chatContainer = document.getElementById("chatContainer");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

const approvalBanner = document.getElementById("approvalBanner");
const approvalDetails = document.getElementById("approvalDetails");
const approvalParams = document.getElementById("approvalParams");
const approveBtn = document.getElementById("approveBtn");
const rejectBtn = document.getElementById("rejectBtn");

const infoBranch = document.getElementById("infoBranch");
const infoRemotes = document.getElementById("infoRemotes");
const infoPath = document.getElementById("infoPath");
const changesList = document.getElementById("changesList");
const diffViewer = document.getElementById("diffViewer");
const historyList = document.getElementById("historyList");
const prsList = document.getElementById("prsList");
const issuesList = document.getElementById("issuesList");

const refreshDiffBtn = document.getElementById("refreshDiffBtn");
const refreshHistoryBtn = document.getElementById("refreshHistoryBtn");
const refreshPrsBtn = document.getElementById("refreshPrsBtn");
const refreshIssuesBtn = document.getElementById("refreshIssuesBtn");

// Conflict Resolver DOM Elements
const refreshConflictsBtn = document.getElementById("refreshConflictsBtn");
const conflictStatusText = document.getElementById("conflictStatusText");
const mergeSourceBranchInput = document.getElementById("mergeSourceBranchInput");
const attemptMergeBtn = document.getElementById("attemptMergeBtn");
const conflictedFilesSection = document.getElementById("conflictedFilesSection");
const conflictCountBadge = document.getElementById("conflictCountBadge");
const conflictedFilesList = document.getElementById("conflictedFilesList");
const conflictDetailSection = document.getElementById("conflictDetailSection");
const selectedConflictFileName = document.getElementById("selectedConflictFileName");
const resolveAiBtn = document.getElementById("resolveAiBtn");
const resolveAiBtnText = document.getElementById("resolveAiBtnText");
const resolveAiSpinner = document.getElementById("resolveAiSpinner");
const conflictExplanationBox = document.getElementById("conflictExplanationBox");
const conflictExplanationText = document.getElementById("conflictExplanationText");
const conflictResolvedEditor = document.getElementById("conflictResolvedEditor");
const applyResolutionBtn = document.getElementById("applyResolutionBtn");
const completeMergeBtn = document.getElementById("completeMergeBtn");
const abortMergeBtn = document.getElementById("abortMergeBtn");

function getGitHubToken() {
    return tokenInput ? tokenInput.value.trim() : "";
}

// INITIALIZATION
document.addEventListener("DOMContentLoaded", () => {
    setupTabSwitching();
    setupQuickChips();
    
    connectBtn.addEventListener("click", handleConnect);
    chatForm.addEventListener("submit", handleSendMessage);
    approveBtn.addEventListener("click", () => handleApproval(true));
    rejectBtn.addEventListener("click", () => handleApproval(false));

    if (refreshDiffBtn) refreshDiffBtn.addEventListener("click", fetchDiff);
    if (refreshHistoryBtn) refreshHistoryBtn.addEventListener("click", fetchHistory);
    if (refreshPrsBtn) refreshPrsBtn.addEventListener("click", fetchPRs);
    if (refreshIssuesBtn) refreshIssuesBtn.addEventListener("click", fetchIssues);

    if (refreshConflictsBtn) refreshConflictsBtn.addEventListener("click", fetchConflicts);
    if (attemptMergeBtn) attemptMergeBtn.addEventListener("click", handleAttemptMerge);
    if (resolveAiBtn) resolveAiBtn.addEventListener("click", handleResolveAi);
    if (applyResolutionBtn) applyResolutionBtn.addEventListener("click", handleApplyResolution);
    if (completeMergeBtn) completeMergeBtn.addEventListener("click", handleCompleteMerge);
    if (abortMergeBtn) abortMergeBtn.addEventListener("click", handleAbortMerge);

    targetInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleConnect();
    });
});

// TAB SWITCHING
function setupTabSwitching() {
    const tabContainer = document.querySelector(".inspector-tabs");
    if (tabContainer) {
        tabContainer.addEventListener("wheel", (evt) => {
            if (evt.deltaY !== 0) {
                evt.preventDefault();
                tabContainer.scrollLeft += evt.deltaY;
            }
        });
    }

    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            
            btn.classList.add("active");
            btn.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' });

            const targetTab = document.getElementById(`tab-${btn.dataset.tab}`);
            if (targetTab) targetTab.classList.add("active");

            if (btn.dataset.tab === "prs") fetchPRs();
            if (btn.dataset.tab === "issues") fetchIssues();
            if (btn.dataset.tab === "conflicts") fetchConflicts();
        });
    });
}

// QUICK CHIPS
function setupQuickChips() {
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            userInput.value = chip.dataset.prompt;
            chatForm.dispatchEvent(new Event("submit"));
        });
    });
}

// CONNECT / CLONE REPOSITORY
async function handleConnect() {
    const target = targetInput.value.trim();
    if (!target) return alert("Please enter a local path or GitHub URL.");

    setConnectingState(true);

    try {
        const res = await fetch(`${API_BASE}/repository/info`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: target })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Failed to connect to repository");
        }

        currentTarget = target;
        updateRepoStatusPill(true, data.branch);
        infoBranch.textContent = data.branch || "main";
        infoRemotes.textContent = data.remotes || "No remotes configured";
        infoPath.textContent = target;

        appendAgentMessage(`Successfully connected to repository at \`${target}\` on branch \`${data.branch}\`.`);

        // Refresh all live stats
        await Promise.all([fetchStatus(), fetchDiff(), fetchHistory(), fetchPRs(), fetchIssues()]);
    } catch (err) {
        updateRepoStatusPill(false, "Connection Failed");
        appendAgentMessage(`**Connection Error**: ${err.message}`);
    } finally {
        setConnectingState(false);
    }
}

function setConnectingState(isConnecting) {
    if (isConnecting) {
        connectBtnText.textContent = "Connecting...";
        connectSpinner.classList.remove("hidden");
        connectBtn.disabled = true;
    } else {
        connectBtnText.textContent = "Connect / Clone";
        connectSpinner.classList.add("hidden");
        connectBtn.disabled = false;
    }
}

function updateRepoStatusPill(online, label) {
    if (online) {
        repoStatusPill.className = "status-pill online";
        statusPillText.textContent = `Connected: ${label}`;
    } else {
        repoStatusPill.className = "status-pill offline";
        statusPillText.textContent = label || "No Repository";
    }
}

// FETCH LIVE INSPECTOR DATA
async function fetchStatus() {
    if (!currentTarget) return;
    try {
        const res = await fetch(`${API_BASE}/repository/status`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget })
        });
        const data = await res.json();
        
        changesList.innerHTML = "";
        const allChanges = [
            ...(data.modified || []).map(f => ({ file: f, type: 'M' })),
            ...(data.staged || []).map(f => ({ file: f, type: 'A' })),
            ...(data.deleted || []).map(f => ({ file: f, type: 'D' })),
            ...(data.untracked || []).map(f => ({ file: f, type: 'U' }))
        ];

        if (allChanges.length === 0) {
            changesList.innerHTML = '<div class="empty-state">Working tree clean. No uncommitted changes.</div>';
            return;
        }

        allChanges.forEach(item => {
            const div = document.createElement("div");
            div.className = "change-item";
            div.innerHTML = `
                <span>${item.file}</span>
                <span class="change-status status-${item.type}">${item.type}</span>
            `;
            changesList.appendChild(div);
        });
    } catch (err) {
        console.error("Status error:", err);
    }
}

async function fetchDiff() {
    if (!currentTarget) return;
    diffViewer.textContent = "Loading diff...";
    try {
        const res = await fetch(`${API_BASE}/repository/diff`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget })
        });
        const data = await res.json();
        diffViewer.textContent = data.diff || "No uncommitted diffs found.";
    } catch (err) {
        diffViewer.textContent = "Error loading diff.";
    }
}

async function fetchHistory() {
    if (!currentTarget) return;
    try {
        const res = await fetch(`${API_BASE}/repository/history?limit=10`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget })
        });
        const data = await res.json();

        historyList.innerHTML = "";
        if (!data || data.length === 0) {
            historyList.innerHTML = '<div class="empty-state">No commits found.</div>';
            return;
        }

        data.forEach(commit => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerHTML = `
                <div class="commit-hash">${commit.short_hash}</div>
                <div class="commit-msg">${escapeHtml(commit.message)}</div>
                <div class="commit-author">${escapeHtml(commit.author)} • ${commit.date}</div>
            `;
            historyList.appendChild(div);
        });
    } catch (err) {
        console.error("History error:", err);
    }
}

// FETCH PULL REQUESTS
async function fetchPRs() {
    if (!currentTarget || !prsList) return;
    prsList.innerHTML = '<div class="empty-state">Loading Pull Requests...</div>';
    try {
        const token = getGitHubToken();
        const res = await fetch(`${API_BASE}/github/prs`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget, token: token || undefined })
        });
        const data = await res.json();

        prsList.innerHTML = "";
        if (!res.ok) {
            prsList.innerHTML = `<div class="empty-state" style="color:var(--accent-danger);">${escapeHtml(data.detail || "Unable to fetch Pull Requests.")}</div>`;
            return;
        }

        if (!data.pull_requests || data.pull_requests.length === 0) {
            prsList.innerHTML = '<div class="empty-state">No open Pull Requests found.</div>';
            return;
        }

        data.pull_requests.forEach(pr => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="commit-hash">#${pr.number}</span>
                    <span class="change-status status-A">${pr.state.toUpperCase()}</span>
                </div>
                <div class="commit-msg"><a href="${pr.html_url}" target="_blank" style="color:inherit;">${escapeHtml(pr.title)}</a></div>
                <div class="commit-author">by ${escapeHtml(pr.user)} • ${pr.head_branch} ➔ ${pr.base_branch}</div>
            `;
            prsList.appendChild(div);
        });
    } catch (err) {
        prsList.innerHTML = '<div class="empty-state">Unable to fetch Pull Requests.</div>';
    }
}

// FETCH ISSUES
async function fetchIssues() {
    if (!currentTarget || !issuesList) return;
    issuesList.innerHTML = '<div class="empty-state">Loading GitHub Issues...</div>';
    try {
        const token = getGitHubToken();
        const res = await fetch(`${API_BASE}/github/issues`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget, token: token || undefined })
        });
        const data = await res.json();

        issuesList.innerHTML = "";
        if (!res.ok) {
            issuesList.innerHTML = `<div class="empty-state" style="color:var(--accent-danger);">${escapeHtml(data.detail || "Unable to fetch GitHub Issues.")}</div>`;
            return;
        }

        if (!data.issues || data.issues.length === 0) {
            issuesList.innerHTML = '<div class="empty-state">No open Issues found.</div>';
            return;
        }

        data.issues.forEach(issue => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="commit-hash">Issue #${issue.number}</span>
                    <button class="btn-secondary btn-sm ask-issue-btn" data-issue="${issue.number}">Fix Issue</button>
                </div>
                <div class="commit-msg"><a href="${issue.html_url}" target="_blank" style="color:inherit;">${escapeHtml(issue.title)}</a></div>
                <div class="commit-author">Opened by ${escapeHtml(issue.user)} • ${issue.comments_count} comments</div>
            `;
            issuesList.appendChild(div);
        });

        // Add handlers for issue fix buttons
        document.querySelectorAll(".ask-issue-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const num = btn.dataset.issue;
                userInput.value = `Inspect Issue #${num}, analyze what is needed, and summarize a solution.`;
                chatForm.dispatchEvent(new Event("submit"));
            });
        });
    } catch (err) {
        issuesList.innerHTML = '<div class="empty-state">Unable to fetch GitHub Issues.</div>';
    }
}

// SEND AGENT MESSAGE
async function handleSendMessage(e) {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    if (!currentTarget) {
        return alert("Please connect to a repository or enter a GitHub URL first.");
    }

    appendUserMessage(message);
    userInput.value = "";
    sendBtn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/agent/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_request: message,
                target: currentTarget,
                session_id: currentSessionId
            })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Agent run failed");

        currentSessionId = data.session_id;
        handleAgentResponse(data);
    } catch (err) {
        appendAgentMessage(`**Agent Error**: ${err.message}`);
    } finally {
        sendBtn.disabled = false;
    }
}

// HANDLE APPROVAL DECISION
async function handleApproval(approved) {
    if (!currentSessionId) return;

    approvalBanner.classList.add("hidden");
    appendUserMessage(approved ? "[APPROVED] Write operation confirmed." : "[REJECTED] Write operation cancelled.");

    try {
        const res = await fetch(`${API_BASE}/agent/approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: currentSessionId,
                approval_id: currentApprovalId,
                approved: approved
            })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Approval processing failed");

        handleAgentResponse(data);
    } catch (err) {
        appendAgentMessage(`**Approval Error**: ${err.message}`);
    }
}

// PROCESS AGENT RESPONSE DATA
function handleAgentResponse(data) {
    // Render tool calls
    if (data.tool_calls && data.tool_calls.length > 0) {
        data.tool_calls.forEach(call => {
            appendToolCard(call.tool_name, call.arguments);
        });
    }

    // Render final response if completed
    if (data.final_response) {
        appendAgentMessage(data.final_response);
    }

    // Check if waiting for approval
    if (data.status === "waiting_approval" && data.approval_requests && data.approval_requests.length > 0) {
        const req = data.approval_requests[data.approval_requests.length - 1];
        currentApprovalId = req.approval_id || req.id;
        
        approvalDetails.textContent = `Agent requests to run tool '${req.tool_name}' which modifies repository/GitHub state.`;
        approvalParams.textContent = JSON.stringify(req.arguments, null, 2);
        approvalBanner.classList.remove("hidden");
    }

    // Refresh live git & github stats
    fetchStatus();
    fetchDiff();
    fetchHistory();
    fetchPRs();
    fetchIssues();
}

// DOM HELPERS
function appendUserMessage(text) {
    const welcome = document.querySelector(".system-welcome");
    if (welcome) welcome.remove();

    const div = document.createElement("div");
    div.className = "chat-bubble user";
    div.textContent = text;
    chatContainer.appendChild(div);
    scrollToBottom();
}

function appendAgentMessage(text) {
    const welcome = document.querySelector(".system-welcome");
    if (welcome) welcome.remove();

    const div = document.createElement("div");
    div.className = "chat-bubble agent";
    div.innerHTML = parseMarkdown(text);
    chatContainer.appendChild(div);
    scrollToBottom();
}

function appendToolCard(toolName, args) {
    const div = document.createElement("div");
    div.className = "tool-card";
    div.innerHTML = `
        <div class="tool-card-title">
            <span>TOOL CALL: ${escapeHtml(toolName)}</span>
            <span style="font-size:0.7rem; opacity:0.7;">EXECUTED</span>
        </div>
        <div class="tool-card-args">${escapeHtml(JSON.stringify(args))}</div>
    `;
    chatContainer.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function escapeHtml(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function parseMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\n/g, '<br>');
    return html;
}

// SMART CONFLICT RESOLVER LOGIC
async function fetchConflicts() {
    if (!currentTarget) return;
    try {
        const res = await fetch(`${API_BASE}/conflicts/detect`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to detect conflicts.");

        if (data.merge_in_progress && data.conflict_count > 0) {
            conflictStatusText.textContent = `Merge in progress: ${data.conflict_count} file(s) with conflicts.`;
            conflictCountBadge.textContent = data.conflict_count;
            conflictedFilesSection.classList.remove("hidden");

            conflictedFilesList.innerHTML = "";
            data.conflicted_files.forEach(file => {
                const div = document.createElement("div");
                div.className = "change-item";
                div.style.cursor = "pointer";
                div.innerHTML = `
                    <span>${escapeHtml(file)}</span>
                    <span class="change-status status-U">CONFLICT</span>
                `;
                div.addEventListener("click", () => loadConflictFileDetails(file));
                conflictedFilesList.appendChild(div);
            });

            // Auto-select first conflict if none selected
            if (!selectedConflictFile && data.conflicted_files.length > 0) {
                loadConflictFileDetails(data.conflicted_files[0]);
            }
        } else if (data.merge_in_progress && data.conflict_count === 0) {
            conflictStatusText.textContent = "Merge in progress: All conflicts resolved! Ready to complete merge.";
            conflictedFilesSection.classList.add("hidden");
        } else {
            conflictStatusText.textContent = "No active merge conflicts detected.";
            conflictedFilesSection.classList.add("hidden");
            conflictDetailSection.classList.add("hidden");
            selectedConflictFile = null;
        }
    } catch (err) {
        conflictStatusText.textContent = `Error: ${err.message}`;
    }
}

async function loadConflictFileDetails(filePath) {
    selectedConflictFile = filePath;
    selectedConflictFileName.textContent = filePath;
    conflictExplanationBox.classList.add("hidden");

    try {
        const res = await fetch(`${API_BASE}/conflicts/details`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget, file_path: filePath })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to load file conflict details.");

        conflictResolvedEditor.value = data.full_content || "";
        conflictDetailSection.classList.remove("hidden");
    } catch (err) {
        alert(`Error loading conflict details: ${err.message}`);
    }
}

async function handleAttemptMerge() {
    const sourceBranch = mergeSourceBranchInput.value.trim();
    if (!sourceBranch) return alert("Please enter a source branch to merge from.");

    if (!currentTarget) return alert("Please connect to a repository first.");

    try {
        const res = await fetch(`${API_BASE}/conflicts/attempt-merge`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget, source_branch: sourceBranch })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to attempt merge.");

        if (data.status === "clean") {
            appendAgentMessage(`**Clean Merge**: ${data.message}`);
        } else {
            appendAgentMessage(`**Merge Conflict**: ${data.message}`);
        }

        fetchConflicts();
        fetchStatus();
    } catch (err) {
        alert(`Merge error: ${err.message}`);
    }
}

async function handleResolveAi() {
    if (!selectedConflictFile) return alert("Please select a conflicted file first.");

    resolveAiBtnText.textContent = "Analyzing...";
    resolveAiSpinner.classList.remove("hidden");
    resolveAiBtn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/conflicts/resolve-ai`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget, file_path: selectedConflictFile })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "AI resolution failed.");

        conflictExplanationText.textContent = data.explanation || "Resolution synthesized.";
        conflictExplanationBox.classList.remove("hidden");
        conflictResolvedEditor.value = data.resolved_content || "";
        appendAgentMessage(`**AI Resolution Generated** for \`${selectedConflictFile}\`.\n\n*Explanation*: ${data.explanation}`);
    } catch (err) {
        alert(`AI resolution error: ${err.message}`);
    } finally {
        resolveAiBtnText.textContent = "Resolve with Gemini AI";
        resolveAiSpinner.classList.add("hidden");
        resolveAiBtn.disabled = false;
    }
}

async function handleApplyResolution() {
    if (!selectedConflictFile) return alert("No file selected.");
    const content = conflictResolvedEditor.value;

    try {
        const res = await fetch(`${API_BASE}/conflicts/apply`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                repository_path: currentTarget,
                file_path: selectedConflictFile,
                resolved_content: content
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to apply resolution.");

        appendAgentMessage(`**Resolution Staged**: Applied and staged resolution for \`${selectedConflictFile}\`.`);
        fetchConflicts();
        fetchDiff();
        fetchStatus();
    } catch (err) {
        alert(`Apply error: ${err.message}`);
    }
}

async function handleCompleteMerge() {
    try {
        const res = await fetch(`${API_BASE}/conflicts/complete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to complete merge.");

        appendAgentMessage(`**Merge Complete**: ${data.message}`);
        fetchConflicts();
        fetchStatus();
        fetchHistory();
    } catch (err) {
        alert(`Complete merge error: ${err.message}`);
    }
}

async function handleAbortMerge() {
    try {
        const res = await fetch(`${API_BASE}/conflicts/abort`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repository_path: currentTarget })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to abort merge.");

        appendAgentMessage(`**Merge Aborted**: ${data.message}`);
        fetchConflicts();
        fetchStatus();
        fetchDiff();
    } catch (err) {
        alert(`Abort error: ${err.message}`);
    }
}
