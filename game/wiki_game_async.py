import time
from typing import Optional
import asyncio
import aiohttp

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
        self.wiki_parser = WikiParserSmarter()
        self.cost, self.used = dict(), set()
        self.limiter = AsyncLimiter(150, 1)
        self.ioloop = asyncio.get_event_loop()

    def play(self, start : str, end : str):
        mid = "Capitalism"
        self.session = aiohttp.ClientSession()

        logger.info(
            "Started playing\n\t" +
            f"Start page: '{start}'\n\t" +
            f"End page: '{end}'\n\t"
        )

        path_to = self.ioloop.run_until_complete(self.find_path(start, mid, False)).page_names
        path_from = self.ioloop.run_until_complete(self.find_path(end, mid, True)).page_names[::-1]
        path_from.pop(0)

        path_to += path_from

        logger.success("Path is:\n\t" + " -> ".join([f"'{p}'" for p in path_to]))

        self.ioloop.stop()
        return path_to
        # self.session.close()

    async def make_request(self, cur_page : Page, backlinks : bool, end_page_name : str):
        if backlinks:
            params_query = {
                'action': 'query',
                'bltitle': cur_page.name,
                'format': 'json',
                'list': 'backlinks',
                'bllimit': 'max'
            }
        else:
            params_query = {
                'action': 'query',
                'titles': cur_page.name,
                'format': 'json',
                'prop': 'links',
                'pllimit': 'max'
            }
        
        async with self.limiter:
            data = await self.session.get(self.URL, params=params_query).json()
            if backlinks:
                data = data['query']['backlinks']
            else:
                data = [i['links'] for i in data['query']['pages'].values()][0]

            links = []
            for raw_link in data:
                title = raw_link['title']
                if ':' not in title:
                    links.append(raw_link)

            scores = get_score(links, end_page_name)
            ans = [(scores[i], Page(links[i], cur_page.depth + 1, cur_page)) for i in range(len(links))]

            return ans


    async def find_path(self, start : str, end : str, backlinks : bool):
        start_page = Page(start, 0)
    
        self.used.add(start)

        pr_q = queue.PriorityQueue(maxsize=0)

        tasks = [
            asyncio.create_task(
                self.make_request(start_page, backlinks)
            )
        ]

        while True:
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            new_links = [task.result() for task in done]

            for cost, page in new_links:
                if end == page.page_name:
                    return page.path_to_root()
                if page.page_name in self.used:
                    continue
                
                self.used.add(page.page_name)
                self.cost[page.page_name] = cost
                pr_q.put(-cost, page)

            new_tasks = []
            while not pr_q.empty() and self.limiter.has_capacity():
                cost, cur_page = pr_q.get()

                new_tasks.append(asyncio.create_task(
                    self.make_request(cur_page, backlinks, end)
                ))
            
            tasks = list(pending) + new_tasks


            

