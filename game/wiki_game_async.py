import json
import time
from typing import Optional
import asyncio
import aiohttp

import warnings

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
        self.cost, self.used = dict(), set()
        self.limiter = AsyncLimiter(10, 0.1)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.ioloop = asyncio.get_event_loop()

    def play(self, start: str, end: str, debug: bool = True, lang: str = "ru"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.URL = 'https://' + lang + '.wikipedia.org/w/api.php'
            self.debug = debug
            mid = ''
            if lang == 'ru':
                mid = "Земля"
            else:
                mid = "Capitalism"
            self.session = aiohttp.ClientSession()

            logger.info("Heating")
            self.ioloop.run_until_complete(heat(self.URL, self.session))

            if self.debug:
                logger.debug(
                    "Started playing\n\t" +
                    f"Start page: '{start}'\n\t" +
                    f"End page: '{end}'\n\t"
                )

            t1 = time.time()

            path_to = self.ioloop.run_until_complete(self.find_path(start, mid, False)).page_names
            path_from = self.ioloop.run_until_complete(self.find_path(end, mid, True)).page_names[::-1]
            path_from.pop(0)

            path_to += path_from
            t2 = time.time()

            if self.debug:
                logger.success("Path is:\n\t" + " -> ".join([f"'{p}'" for p in path_to]))
            logger.success(f"Time is {t2 -t1}")

            asyncio.run(self.session.close())
            self.ioloop.stop()

            self.used.clear()
            self.cost.clear()
            # return path_to
            return t2 - t1
        # self.session.close()

    async def make_request(self, cur_page: Page, backlinks: bool, end_page_name: str):
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
            async with self.session.get(self.URL, params=params_query) as response:

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

        self.used.add(start)

        pr_q = queue.PriorityQueue(maxsize=0)

        tasks = [
            asyncio.create_task(
                self.make_request(start_page, backlinks, end)
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
                        return page.path_to_root()
                    if page.page_name in self.used:
                        continue

                    self.used.add(page.page_name)
                    self.cost[page.page_name] = cost
                    pr_q.put((-cost, page))

            new_tasks = []

            # await self.limiter.acquire()  # blocks until there is capacity

            while not pr_q.empty() and self.limiter.has_capacity():
                cost, cur_page = pr_q.get()

                async with self.limiter:
                    new_tasks.append(asyncio.create_task(
                        self.make_request(cur_page, backlinks, end)
                    ))

            tasks = list(pending) + new_tasks
