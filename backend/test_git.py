from app.tools.git.status import get_repository_status
from app.tools.git.diff import get_repository_diff
from app.tools.git.repository import get_repository_info
from app.tools.git.history import get_commit_history


REPOSITORY_PATH = r"C:\Users\tejaswi.b\Desktop\code\fastapi_api_key_auth"


def main():

    print("\n========== REPOSITORY INFO ==========")

    repository = get_repository_info(REPOSITORY_PATH)

    print(repository)

    print("\n========== REPOSITORY STATUS ==========")

    status = get_repository_status(REPOSITORY_PATH)

    print(status)

    print("\n========== COMMIT HISTORY ==========")

    history = get_commit_history(
        REPOSITORY_PATH,
        limit=5,
    )

    for commit in history:
        print(commit)

    print("\n========== DIFF ==========")

    diff = get_repository_diff(REPOSITORY_PATH)

    print(diff)


if __name__ == "__main__":
    main()