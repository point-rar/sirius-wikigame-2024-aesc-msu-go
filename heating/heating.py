import requests
import aiohttp


async def heat(URL, session, page_name="Hitler", cnt_heat=20):
    params_query = {
        'action': 'query',
        'bltitle': page_name,
        'format': 'json',
        'list': 'backlinks',
        'bllimit': 20
    }

    for i in range(cnt_heat):
        async with session.get(url=URL, params=params_query) as req:
            continue