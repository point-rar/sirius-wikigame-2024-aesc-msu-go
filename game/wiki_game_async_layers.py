import json
import time
from typing import Optional
import asyncio
import aiohttp

import warnings

from heating.heating import heat

from game.wiki_game import WikiGame
from model.page import Page
from model.path import Path
from aiolimiter import AsyncLimiter

from loguru import logger

from parser.wiki_parser_async import WikiParserSmarter

import queue

from server.send_request import get_score

LAYER_SIZE = 25


# The simplest implementation with sequential page parsing using BFS
class WikiGameAsyncWithLayers(WikiGame):
    def __init__(self):
        self.debug = True
        self.URL = 'https://en.wikipedia.org/w/api.php'
        self.wiki_parser = WikiParserSmarter()
        self.used = set()
        self.limiter = AsyncLimiter(100000, 0.1)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.ioloop = asyncio.get_event_loop()

    def play(self, start: str, end: str, debug: bool = True, lang : str = "ru"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            self.URL = 'https://' + lang + '.wikipedia.org/w/api.php'
            self.debug = debug

            if lang == "ru":
                mid = "Земля"
            else:
                mid = "Earth"

            self.session = aiohttp.ClientSession()

            if self.debug:
                logger.info("Heating")

            self.ioloop.run_until_complete(heat(self.URL, self.session))


            if self.debug:
                logger.info(
                    "Started playing\n\t" +
                    f"Start page: '{start}'\n\t" +
                    f"End page: '{end}'\n\t"
                )

            t1 = time.time()
            #path_to = self.ioloop.run_until_complete(self.find_path(start, mid, False)).page_names
            #self.used.clear()
            #path_from = self.ioloop.run_until_complete(self.find_path(end, mid, True)).page_names[::-1]
            #path_from.pop(0)

            #path_to += path_from
            path_to = self.ioloop.run_until_complete(self.find_path_to_from(start, mid, end))
            t2 = time.time()

            if self.debug:
                logger.success("Path is:\n\t" + " -> ".join([f"'{p}'" for p in path_to]))
            logger.success(f"Time is {t2 -t1}")

            asyncio.run(self.session.close())
            self.ioloop.stop()

            self.used.clear()
            # self.cost.clear()
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
            logger.info(
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

        cur_layer = []
        next_layer = []

        tasks = [
            asyncio.create_task(
                self.make_request(start_page, backlinks, end)
            )
        ]

        while True:
            try:
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.ALL_COMPLETED
                )
            except:
                continue

            new_links = []
            for task in done:
                new_links += task.result()

            new_links = sorted(new_links)[::-1][:LAYER_SIZE]
            to_add = []

            for cost, page in new_links:
                if end == page.page_name:
                    return page.path_to_root()
                if page.page_name in self.used:
                    continue

                self.used.add(page.page_name)
                # self.cost[page.page_name] = cost
                to_add.append((cost, page))

            new_tasks = []

            for cost, page in to_add:

                async with self.limiter:
                    new_tasks.append(asyncio.create_task(
                        self.make_request(page, backlinks, end)
                    ))

            tasks = new_tasks

    async def find_path_to_from(self, start: str, mid : str, end: str):
        start_page = Page(start, 0)
        end_page = Page(end, 0)

        self.used.add(start)

        cur_layer = []
        next_layer = []

        tasks_to = [
            asyncio.create_task(
                self.make_request(start_page, True, mid)
            )
        ]
        tasks_from = [
            asyncio.create_task(
                self.make_request(end_page, False, mid)
            )
        ]

        is_path_to = False
        is_path_from = False
        path_to = -1
        path_from = -1

        while not is_path_to or not is_path_from:
            try:
                done_to, pending = await asyncio.wait(
                    tasks_to,
                    return_when=asyncio.ALL_COMPLETED
                )
                done_from, pending = await asyncio.wait(
                    tasks_from,
                    return_when=asyncio.ALL_COMPLETED
                )
            except:
                continue
            
            if not is_path_to:
                new_links_to = []
                for task in done_to:
                    new_links_to += task.result()

                new_links_to = sorted(new_links_to)[::-1][:LAYER_SIZE]
                to_add = []

                for cost, page in new_links_to:
                    if is_path_to == True:
                        continue
                    if mid == page.page_name:
                        path_to = page.path_to_root()
                        is_path_to = True
                    if page.page_name in self.used_to:
                        continue

                    self.used_to.add(page.page_name)
                    # self.cost[page.page_name] = cost
                    to_add.append((cost, page))

                new_tasks_to = []

                for cost, page in to_add:

                    async with self.limiter:
                        new_tasks_to.append(asyncio.create_task(
                            self.make_request(page, False, end)
                        ))

                tasks_to = new_tasks_to
            else:
                tasks_to = []

            if not is_path_from:
                new_links_from = []
                for task in done_from:
                    new_links_from += task.result()

                new_links_from = sorted(new_links_from)[::-1][:LAYER_SIZE]
                to_add = []

                for cost, page in new_links_from:
                    if is_path_from == True:
                        continue
                    if mid == page.page_name:
                        path_from = page.path_to_root()
                        is_path_from = True
                    if page.page_name in self.used_from:
                        continue

                    self.used_from.add(page.page_name)
                    # self.cost[page.page_name] = cost
                    to_add.append((cost, page))

                new_tasks_from = []

                for cost, page in to_add:

                    async with self.limiter:
                        new_tasks_from.append(asyncio.create_task(
                            self.make_request(page, True, end)
                        ))

                tasks_from = new_tasks_from
            else:
                tasks_from = []
        path_from = path_from[:len(path_from) - 1:-1]
        path_to += path_from
        return path_to