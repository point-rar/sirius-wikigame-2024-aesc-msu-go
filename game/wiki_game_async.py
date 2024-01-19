import json
import time
from typing import Optional
import asyncio
import aiohttp

import warnings
import threading
import joblib

from joblib import Parallel, delayed

from heating.heating import heat

from game.wiki_game import WikiGame
from model.page import Page
from model.path import Path
from aiolimiter import AsyncLimiter

from loguru import logger

from parser.wiki_parser_async import WikiParserSmarter

import queue

from server.send_request import get_score

NUM_FROM_QUEUE_BY_STEP = 20


# The simplest implementation with sequential page parsing using BFS
class WikiGameAsync(WikiGame):
    def __init__(self):
        self.debug = True
        self.URL = 'https://ru.wikipedia.org/w/api.php'
        self.wiki_parser = WikiParserSmarter()
        self.limiter = AsyncLimiter(16, 0.01)
        self.path_to = []
        self.path_from = []

    def run_path_to(self, *args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        self.path_to = loop.run_until_complete(self.find_path(args[0], args[1], args[2])).page_names
        loop.close()
        return "ty pidor"
    
    def run_path_from(self, *args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
        self.path_from = loop.run_until_complete(self.find_path(args[0], args[1], args[2])).page_names[::-1]
        loop.close()
        return "ty tozhe pidor"

    def play(self, start: str, end: str, debug: bool = True, lang: str = "ru"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            warnings.simplefilter("ignore", category=RuntimeWarning)
            self.URL = 'https://' + lang + '.wikipedia.org/w/api.php'
            self.debug = debug
            mid = ''
            if lang == 'ru':
                mid = "Россия"
            else:
                mid = "Capitalism"
            # self.session = aiohttp.ClientSession()

            logger.info("Heating")
            # self.ioloop.run_until_complete(heat(self.URL, self.session))

            if self.debug:
                logger.debug(
                    "Started playing\n\t" +
                    f"Start page: '{start}'\n\t" +
                    f"End page: '{end}'\n\t"
                )

            t1 = time.time()

            thread1 = threading.Thread(target=self.run_path_to, args=(start, mid, False))
            thread2 = threading.Thread(target=self.run_path_from, args=(end, mid, True))

            thread1.start()
            thread2.start()

            thread1.join()
            thread2.join()

            print(self.path_from)

            self.path_from.pop(0)
            self.path_to += self.path_from
            t2 = time.time()

            if self.debug:
                logger.success("Path is:\n\t" + " -> ".join([f"'{p}'" for p in self.path_to]))
            logger.success(f"Time is {t2 -t1}")
            exit(-1)

            # asyncio.run(self.session.close())
            # self.ioloop.stop()

            # return path_to
            return t2 - t1
        # self.session.close()

    async def make_request(self, cur_page: Page, backlinks: bool, end_page_name: str, session):
        if backlinks:
            params_query = {
                'action': 'query',
                'bltitle': cur_page.page_name,
                'format': 'json',
                'list': 'backlinks',
                'bllimit': 'max'
            }
        else:
            params_query = {
                'action': 'query',
                'titles': cur_page.page_name,
                'format': 'json',
                'prop': 'links',
                'pllimit': 'max'
            }


        if self.debug:
            logger.debug(
                "Parsing \n\t" + cur_page.page_name
            )

        async with self.limiter:
            async with session.get(self.URL, params=params_query) as response:

                data = await response.text()
                data = json.loads(data)

                try:
                    if backlinks:
                        data = data['query']['backlinks']
                    else:
                        data = [i['links'] for i in data['query']['pages'].values()][0]
                except:
                    data = []

                links = []
                for raw_link in data:
                    title = raw_link['title']
                    if ':' not in title:
                        links.append(title)

                scores = get_score(links, end_page_name)
                ans = [(scores[i], Page(links[i], cur_page.depth + 1, cur_page)) for i in range(len(links))]

                return ans

    async def find_path(self, start: str, end: str, backlinks: bool):
        start_page = Page(start, 0)

        used =  set()

        used.add(start)

        pr_q = queue.PriorityQueue(maxsize=0)
        session = aiohttp.ClientSession()

        tasks = [
            asyncio.create_task(
                self.make_request(start_page, backlinks, end, session)
            )
        ]

        while True:
            try:
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
            except:
                continue

            new_links = [task.result() for task in done]

            for list_links in new_links:
                for cost, page in list_links:
                    if end == page.page_name:
                        await session.close()
                        return page.path_to_root()
                    if page.page_name in used:
                        continue

                    used.add(page.page_name)
                    pr_q.put((-cost, page))

            new_tasks = []

            # await self.limiter.acquire()  # blocks until there is capacity

            while not pr_q.empty() and self.limiter.has_capacity():
                cost, cur_page = pr_q.get()

                async with self.limiter:
                    new_tasks.append(asyncio.create_task(
                        self.make_request(cur_page, backlinks, end, session)
                    ))

            tasks = list(pending) + new_tasks
