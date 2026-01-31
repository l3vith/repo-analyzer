import asyncio
import httpx
from repository import get_commits, Commit

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

