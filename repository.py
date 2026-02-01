import asyncio
from typing import Any, Optional

import httpx
import pydantic
from loguru import logger


class Commit(pydantic.BaseModel):
    """
    Structure to represent a singular commit in a repository

    sha: SHA hash identifying the commit
    commit: Git commit metadata containing message, author/committer
            info (name/email/date), and the associated tree reference
    author: GitHub user object for the commit author (may be null)
    committer: GitHub user object for the commit committer (may be null)
    parents: List of parent commit objects (merge commits have multiple)
    stats: Additions/deletions summary for the commit (detail endpoint only)
    files: List of changed files, including patch diffs when available
    """

    sha: str
    commit: dict[str, Any]

    author: dict[str, Any]
    committer: dict[str, Any]
    parents: list[dict[str, Any]]

    stats: Optional[dict[str, Any]] = None
    files: Optional[list[dict[str, Any]]] = None


# Modularize commit class with seperate CommitMetadata class


class Repository(pydantic.BaseModel):
    user: str
    name: str

    commits: Optional[list[Commit]] = None


async def get_patch(
    client: httpx.AsyncClient,
    user: str,
    name: str,
    sha: str,
    token: str | None = None,
) -> Any:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        logger.warning("Tokenless API Calls In Use!")

    try:
        logger.info(f"Fetching patches for {user}:{sha}")
        req = await client.get(
            f"https://api.github.com/repos/{user}/{name}/commits/{sha}",
            headers=headers,
            timeout=10.0,
        )
        req.raise_for_status()
        return req.json()
    except httpx.RequestError as e:
        logger.error(
            f"Failed to fetch repository patches for {user} due to Request Error: {e}"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Status code: {e.response.status_code}")
        logger.error(f"Response body: {e.response.text}")
    finally:
        logger.info(f"Finished trying to fetch repository patches for {user}")

    raise RuntimeError("Failed to fetch repository patches")


async def get_patches(
    client: httpx.AsyncClient,
    repo: Repository,
    token: str | None = None,
) -> Repository:
    headers = {}
    if token:
        logger.warning("Tokenless API Calls In Use!")
        headers["Authorization"] = f"Bearer {token}"
    else:
        logger.warning("Tokenless API Calls In Use!")

    if repo.commits is None:
        logger.error("Patches requested before fetching commit SHA hashes")
        raise RuntimeError("Repository commits not fetched")

    tasks = [
        get_patch(client, repo.user, repo.name, commit.sha, token)
        for commit in repo.commits
    ]
    results = await asyncio.gather(*tasks)

    for commit, detail in zip(repo.commits, results):
        commit.stats = detail["stats"]
        commit.files = detail["files"]

    return repo


async def get_commits(
    client: httpx.AsyncClient,
    repo: Repository,
    token: str | None = None,
) -> Repository:
    headers = {}
    if token:
        logger.warning("Tokenless API Calls In Use!")
        headers["Authorization"] = f"Bearer {token}"
    else:
        logger.warning("Tokenless API Calls In Use!")

    try:
        logger.info(f"Fetching repository commits for {repo.user}")
        req = await client.get(
            f"https://api.github.com/repos/{repo.user}/{repo.name}/commits",
            headers=headers,
            timeout=10.0,
        )
        req.raise_for_status()
        json_data = req.json()
        commits = [Commit.model_validate(commit) for commit in json_data]
        updated_repo = repo.model_copy(update={"commits": commits})
        return updated_repo
    except httpx.RequestError as e:
        logger.error(
            f"Failed to fetch repository commits for {repo.user} due to Request Error: {e}"
        )
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to fetch repository commits for {repo.user} due to Status Error: {e}"
        )
    finally:
        logger.info(f"Finished trying to fetch repository commits for {repo.user}")

    raise RuntimeError("Failed to fetch repository commits")


async def update_commits(
    client: httpx.AsyncClient, repo: Repository, token: str | None = None
) -> Repository:
    repo = await get_commits(client, repo, token)
    repo = await get_patches(client, repo, token)

    return repo
