from typing import Optional

from game.wiki_game import WikiGame
from model.page import Page
from model.path import Path

from loguru import logger

from parser.wiki_parser import WikiParserDumb, WikiParserSmarter

import queue

from server.send_request import get_score


# The simplest implementation with sequential page parsing using BFS
class WikiGameSmart(WikiGame):
    def __init__(self):
        self.wiki_parser = WikiParserSmarter()
        self.cost = dict()
        self.used = dict()

    def get_cost(self, word, end_page):
        value = self.cost.get(word)
        if value is None:
            self.cost[word] = get_score([word], end_page)[0]
            return self.cost[word]

        return value

    def play(self, start_page_name: str, end_page_name: str, max_depth: int = None) -> Optional[Path]:
        logger.info(
            "Started playing\n\t" +
            f"Start page: '{start_page_name}'\n\t" +
            f"End page: '{end_page_name}'\n\t"
        )

        # Simple but not somple BFS
        start_page = Page(start_page_name, 0)
        # queued_page_names = set(start_page_name)
        q = queue.PriorityQueue(maxsize=0)
        q.put((-self.get_cost(start_page_name, end_page_name), start_page))

        while q.qsize() != 0:
            cost_page, cur_page = q.get()

            logger.debug(
                f"\n\tParsing '{cur_page.page_name}'\n\t" +
                f"Queue size: {q.qsize()}"
            )

            links = self.wiki_parser.get_links(cur_page.page_name)
            costs = get_score(links, end_page_name)
            for i in range(len(links)):
                # next_page_name = link.title
                link = links[i]
                next_page_name = link

                if next_page_name == end_page_name:
                    logger.success("Path found!")
                    end_page = Page(next_page_name, cur_page.depth + 1, cur_page)
                    return end_page.path_to_root()

                if self.used.get(next_page_name) is not None:
                    continue

                self.used[next_page_name] = True
                self.cost[next_page_name] = costs[i]

                next_page = Page(next_page_name, cur_page.depth + 1, cur_page)

                q.put((-costs[i], next_page))

        logger.error("Path not found, depth limit reached :(")
        return None
