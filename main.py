import asyncio
import os

import dotenv
import httpx

from repository import Repository, update_commits

dotenv.load_dotenv()


async def main():
    client = httpx.AsyncClient()
    repo = Repository(user="l3vith", name="torr")
    repo = await update_commits(client, repo, token=os.getenv("GITHUB_TOKEN"))

    if repo.commits is not None and len(repo.commits) > 0:
        first_commit = repo.commits[0]

        if first_commit.files is not None and len(first_commit.files) > 0:
            print(first_commit.author)

    await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
