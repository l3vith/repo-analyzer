import asyncio
import json
from typing import Any, Optional

import httpx
import pydantic
from loguru import logger


class Commit(pydantic.BaseModel):
    sha: str
    commit: dict[str, Any]
    author: dict[str, Any]
    committer: dict[str, Any]
    parents: list[dict[str, Any]]

    stats: Optional[dict[str, Any]] = None
    files: Optional[list[dict[str, Any]]] = None
    patches: Optional[list[str]] = None

class Repository(pydantic.BaseModel):
    user: str
    url: str
    
    commits: Optional[list[Commit]] = None

async def get_commits(
    client: httpx.AsyncClient, user: str, repo_name: str, token: str | None = None
) -> list[dict[str, Any]]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        logger.info(f"Fetching repository commits for {user}")
        req = await client.get(
            f"https://api.github.com/repos/{user}/{repo_name}/commits",
            headers=headers,
            timeout=10.0,
        )
        req.raise_for_status()
        return req.json()
    except httpx.RequestError as e:
        logger.error(
            f"Failed to fetch repository commits for {user} due to Request Error: {e}"
        )
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to fetch repository commits for {user} due to Status Error: {e}"
        )
    finally:
        logger.info(f"Finished trying to fetch repository commits for {user}")

    raise RuntimeError("Failed to fetch repository commits")


async def main():
    client = httpx.AsyncClient()
    # implement handling for pydantic @validate_call
    data = await get_commits(client, "l3vith", "torr")
    # print(json.dumps(data, indent=4))
    print(len(data) if data else None)

    commits = [Commit.model_validate(commit) for commit in data]
    print(commits)

    await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())

