import os
import re
import subprocess
from pathlib import Path
from typing import Any

from app.services.llm_service import LLMService


class ConflictService:

    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path).resolve()

        if not self.repository_path.exists():
            raise ValueError(
                f"Repository path does not exist: {self.repository_path}"
            )

        if not (self.repository_path / ".git").exists():
            raise ValueError(
                f"Not a Git repository: {self.repository_path}"
            )

    def _run_git(self, *args: str, check: bool = True) -> tuple[int, str, str]:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repository_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if check and result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip() or result.stdout.strip()
            )

        return result.returncode, result.stdout.strip(), result.stderr.strip()

    def get_current_branch(self) -> str:
        _, stdout, _ = self._run_git("branch", "--show-current")
        return stdout

    def is_merge_in_progress(self) -> bool:
        merge_head = self.repository_path / ".git" / "MERGE_HEAD"
        return merge_head.exists()

    def get_conflicted_files(self) -> list[str]:
        _, stdout, _ = self._run_git("diff", "--name-only", "--diff-filter=U", check=False)
        if not stdout:
            return []
        return [line.strip() for line in stdout.splitlines() if line.strip()]

    def attempt_merge(self, source_branch: str, target_branch: str | None = None) -> dict[str, Any]:
        # 1. Always fetch latest refs from remotes first
        self._run_git("fetch", "--all", check=False)

        current_branch = self.get_current_branch()

        if target_branch and target_branch != current_branch:
            self._run_git("checkout", target_branch, check=False)
            current_branch = self.get_current_branch()

        # Resolve merge ref (check if branch exists locally or as origin/branch)
        merge_ref = source_branch
        _, branch_out, _ = self._run_git("branch", check=False)
        local_branches = [line.replace("*", "").strip() for line in branch_out.splitlines()]
        
        if source_branch not in local_branches:
            _, remote_out, _ = self._run_git("branch", "-r", check=False)
            remote_branches = [line.strip() for line in remote_out.splitlines()]
            if f"origin/{source_branch}" in remote_branches or any(b.endswith(f"/{source_branch}") for b in remote_branches):
                merge_ref = f"origin/{source_branch}"

        returncode, stdout, stderr = self._run_git("merge", "--no-commit", merge_ref, check=False)

        conflicted_files = self.get_conflicted_files()

        if returncode == 0 and not conflicted_files:
            # Clean merge!
            return {
                "status": "clean",
                "message": f"Successfully merged branch '{source_branch}' into '{current_branch}' without conflicts.",
                "conflicted_files": [],
                "target_branch": current_branch,
                "source_branch": source_branch,
            }
        elif conflicted_files:
            return {
                "status": "conflict",
                "message": f"Merge conflict detected between '{source_branch}' and '{current_branch}' in {len(conflicted_files)} file(s).",
                "conflicted_files": conflicted_files,
                "target_branch": current_branch,
                "source_branch": source_branch,
            }
        else:
            # returncode != 0 and no conflicted files -> Git execution error (e.g. dirty working tree, invalid branch)
            err_details = stderr or stdout or "Git merge command failed."
            raise RuntimeError(f"Merge could not be started: {err_details}")

    def parse_conflict_markers(self, file_content: str) -> list[dict[str, Any]]:
        """
        Parses standard Git conflict markers in a file string:
        <<<<<<< header_ours
        ours_content
        =======
        theirs_content
        >>>>>>> header_theirs
        """
        pattern = re.compile(
            r"^<<<<<<< (.*?)\n(.*?)\n=======\n(.*?)\n>>>>>>> (.*?)$",
            re.MULTILINE | re.DOTALL,
        )

        conflicts = []
        for index, match in enumerate(pattern.finditer(file_content), start=1):
            ours_header, ours_content, theirs_content, theirs_header = match.groups()
            conflicts.append({
                "id": index,
                "ours_header": ours_header.strip(),
                "ours_content": ours_content,
                "theirs_header": theirs_header.strip(),
                "theirs_content": theirs_content,
            })

        return conflicts

    def get_conflict_details(self, file_path: str) -> dict[str, Any]:
        full_file_path = self.repository_path / file_path
        if not full_file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        try:
            content = full_file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"File '{file_path}' is binary or not UTF-8 text.")

        parsed_conflicts = self.parse_conflict_markers(content)

        return {
            "file_path": file_path,
            "has_conflicts": len(parsed_conflicts) > 0,
            "conflict_count": len(parsed_conflicts),
            "conflicts": parsed_conflicts,
            "full_content": content,
        }

    def generate_ai_resolution(self, file_path: str) -> dict[str, Any]:
        details = self.get_conflict_details(file_path)

        if not details["has_conflicts"]:
            return {
                "file_path": file_path,
                "resolved_content": details["full_content"],
                "explanation": "No conflict markers detected in this file.",
            }

        llm = LLMService()

        prompt = f"""You are an expert software engineer resolving Git merge conflicts.
Below is the content of the file '{file_path}' which currently contains Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).

File Content with Conflicts:
```
{details['full_content']}
```

Your Task:
1. Analyze the changes in the `<<<<<<<` (ours) block and `>>>>>>>` (theirs) block.
2. Determine the semantic intent of both modifications.
3. Synthesize a resolved version of the file content that satisfies the requirements of both changes cleanly, removing all conflict markers.
4. Output your response strictly in the following JSON format:

{{
  "explanation": "Detailed step-by-step reasoning of how you merged the two changes and why.",
  "resolved_content": "The exact full file content with conflict markers removed and combined code."
}}

Do not include markdown triple backticks around the JSON string response itself. Return raw valid JSON.
"""

        response_text = llm.generate([{"role": "user", "content": prompt}])

        # Cleanup potential markdown codeblock formatting from LLM response
        clean_json = response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        import json
        try:
            parsed_res = json.loads(clean_json)
            resolved_content = parsed_res.get("resolved_content", "")
            explanation = parsed_res.get("explanation", "AI resolution synthesized successfully.")
        except Exception:
            # Fallback if non-JSON was returned
            resolved_content = clean_json
            explanation = "AI generated resolution code directly."

        return {
            "file_path": file_path,
            "resolved_content": resolved_content,
            "explanation": explanation,
        }

    def apply_resolution(self, file_path: str, resolved_content: str) -> dict[str, Any]:
        full_file_path = self.repository_path / file_path

        # Write resolved content
        full_file_path.write_text(resolved_content, encoding="utf-8")

        # Stage file
        self._run_git("add", file_path)

        remaining_conflicts = self.get_conflicted_files()

        return {
            "file_path": file_path,
            "status": "resolved",
            "message": f"Applied resolution to '{file_path}' and staged changes.",
            "remaining_conflicts": remaining_conflicts,
            "all_conflicts_resolved": len(remaining_conflicts) == 0,
        }

    def complete_merge(self, message: str | None = None) -> dict[str, Any]:
        remaining = self.get_conflicted_files()
        if remaining:
            raise ValueError(f"Cannot complete merge. Conflicts still remain in: {', '.join(remaining)}")

        if not message:
            message = "Merge resolved via GitPilot AI"

        returncode, stdout, stderr = self._run_git("commit", "-m", message, check=False)

        return {
            "status": "completed",
            "message": stdout or "Merge completed successfully.",
        }

    def abort_merge(self) -> dict[str, Any]:
        if not self.is_merge_in_progress():
            return {
                "status": "aborted",
                "message": "No merge was in progress.",
            }

        self._run_git("merge", "--abort")

        return {
            "status": "aborted",
            "message": "Merge aborted successfully. Working directory restored.",
        }
