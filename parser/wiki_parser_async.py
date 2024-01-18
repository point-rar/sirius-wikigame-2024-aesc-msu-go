import time
from abc import ABC, abstractmethod

import requests

from bs4 import BeautifulSoup
from loguru import logger
import aiohttp

from model.link import Link


class WikiParser(ABC):
    URL = 'https://en.wikipedia.org/w/api.php'


class WikiParserSmarter(WikiParser):

    def __init__(self):
        pass

    async def __get_backlinks_from_page(self, session, page_name: str, count_backlinks=5000):
        # See: https://en.wikipedia.org/w/api.php?action=help&modules=parse
        # https://en.wikipedia.org/w/api.php, https://ru.wikipedia.org/w/api.php
        params_query = {
            'action': 'query',
            'bltitle': page_name,
            'format': 'json',
            'list': 'backlinks',
            'bllimit': count_backlinks
        }

        # self.session = aiohttp.ClientSession()

        async with session.get(url=self.URL, params=params_query) as req:
            data = await req.json()

        # await self.session.close()

        try:
            return data['query']['backlinks']
        except:
            return []

    async def __get_links_from_page(self, page_name: str, count_links=5000):
        # See: https://en.wikipedia.org/w/api.php?action=help&modules=parse
        # https://en.wikipedia.org/w/api.php, https://ru.wikipedia.org/w/api.php

        params_query = {
            'action': 'query',
            'titles': page_name,
            'format': 'json',
            'prop': 'links',
            'pllimit': count_links
        }

        t1 = time.time()
        self.session = aiohttp.ClientSession()

        async with self.session.get(url=self.URL, params=params_query) as req:
            data = await req.json()

        await self.session.close()

        try:
            return [i['links'] for i in data['query']['pages'].values()][0]
        except:
            return []

    async def get_links(self, page_name: str) -> list[str]:
        logger.info(f"Parsing links from '{page_name}'")
        raw_links = await self.__get_links_from_page(page_name)

        links = set()

        for raw_link in raw_links:
            title = raw_link['title']  # like a name
            # Avoid beginnings
            # Help: Wikipedia: Special: Category: Template: User talk:
            if ':' not in title:
                links.add(title)

        return list(links)

    async def get_backlinks(self, page_name: str) -> list[str]:
        logger.info(f"Parsing backlinks from '{page_name}'")
        raw_links = await self.__get_backlinks_from_page(page_name)

        links = set()

        for raw_link in raw_links:
            title = raw_link['title']  # like a name
            # Avoid beginnings
            # Help: Wikipedia: Special: Category: Template: User talk:
            if ':' not in title:
                links.add(title)

        return list(links)

# async def main():
#     wiki = WikiParserSmarter()
#     # print(await wiki.get_backlinks("cat"))
#     # await wiki.session.close()
#
#
# import asyncio
#
# loop = asyncio.get_event_loop()
# oop.run_until_complete(main())
# loop.close()


# wiki = WikiParserSmarter()

# print(wiki.get_backlinks("cat"))
