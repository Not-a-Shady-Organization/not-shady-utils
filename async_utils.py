from aiohttp import ClientSession
import asyncio
import sys
import os

# Max requests you can make at once
LIMIT = os.environ.get('MAX_REQUESTS_LIVE', 10)


def handle_requests(requests):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    responses = loop.run_until_complete(run_requests(requests))
    return responses


async def fetch(request, session):
    async with session.request(**request) as response:
        return await response.read()


async def run_requests(requests):
    async with ClientSession() as session:
        return await asyncio.ensure_future(
            run(
                session,
                requests
            )
        )

async def bound_fetch(sem, request, session):
    # Getter function with semaphore.
    async with sem:
        return await fetch(request, session)

async def run(session, requests):
    tasks = []

    # create instance of Semaphore
    sem = asyncio.Semaphore(LIMIT)

    for request in requests:
        # pass Semaphore and session to every GET request
        task = asyncio.ensure_future(bound_fetch(sem, request, session))
        tasks.append(task)
    responses = asyncio.gather(*tasks)
    return await responses
