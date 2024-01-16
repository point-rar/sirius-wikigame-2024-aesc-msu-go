from abc import ABC, abstractmethod

import requests

from bs4 import BeautifulSoup
from loguru import logger

from model.link import Link


class WikiParser(ABC):
    URL = 'https://en.wikipedia.org/w/api.php'

    @abstractmethod
    def get_links(self, page_name: str) -> set[str]:
        pass


class WikiParserDumb(WikiParser):
    def __init__(self):
        self.session = requests.Session()

    def __get_page(self, page_name: str) -> str:
        # See: https://en.wikipedia.org/w/api.php?action=help&modules=parse
        # https://en.wikipedia.org/w/api.php, https://ru.wikipedia.org/w/api.php
        params = {
            'action': 'parse',
            'page': page_name,
            'format': 'json'
        }
        req = self.session.get(url=self.URL, params=params)
        data = req.json()

        return data['parse']['text']['*']

    def get_links(self, page_name: str) -> set[Link]:
        logger.info(f"Parsing links from '{page_name}'")
        page = self.__get_page(page_name)
        # https://beautiful-soup-4.readthedocs.io/en/latest/
        soup = BeautifulSoup(page, 'html.parser')
        raw_links = soup.find_all('a', href=lambda x: x and x.startswith('/wiki/'), class_=False)

        links = set()

        for raw_link in raw_links:
            title = raw_link.attrs['title']
            # Avoid beginnings
            # Help: Wikipedia: Special: Category: Template: User talk:
            if ':' not in title:
                links.add(Link(title))

        return links


class WikiParserSmarter(WikiParser):
    def __init__(self):
        self.session = requests.Session()

    def __get_backlinks_from_page(self, page_name: str, count_backlinks=500) -> str:
        # See: https://en.wikipedia.org/w/api.php?action=help&modules=parse
        # https://en.wikipedia.org/w/api.php, https://ru.wikipedia.org/w/api.php
        params_query = {
            'action': 'query',
            'bltitle': page_name,
            'format': 'json',
            'list': 'backlinks',
            'bllimit':  count_backlinks
        }

        req = self.session.get(url=self.URL, params=params_query)
        data = req.json()

        # print(data.keys())
        #
        # print(data['query'].keys())
        # print(data['query']['backlinks'])

        return data['query']['backlinks']
    def __get_links_from_page(self, page_name: str) -> str:
        # See: https://en.wikipedia.org/w/api.php?action=help&modules=parse
        # https://en.wikipedia.org/w/api.php, https://ru.wikipedia.org/w/api.php

        params_parse = {
            'action': 'parse',
            'page': page_name,
            'format': 'json',
            'props': 'links'
        }

        req = self.session.get(url=self.URL, params=params_parse)
        data = req.json()

        # print(data.keys())
        #
        # print(data['parse'].keys())
        # print(data['parse']['links'])

        return data['parse']['links']

    def get_links(self, page_name: str) -> set[Link]:
        logger.info(f"Parsing links from '{page_name}'")
        raw_links = self.__get_links_from_page(page_name)

        links = set()

        for raw_link in raw_links:
            title = raw_link['*'] # like a name
            # Avoid beginnings
            # Help: Wikipedia: Special: Category: Template: User talk:
            if ':' not in title:
                links.add(Link(title))

        return links

    def get_backlinks(self, page_name: str) -> set[Link]:
        logger.info(f"Parsing backlinks from '{page_name}'")
        raw_links = self.__get_backlinks_from_page(page_name)

        links = set()

        for raw_link in raw_links:
            title = raw_link['title'] # like a name
            # Avoid beginnings
            # Help: Wikipedia: Special: Category: Template: User talk:
            if ':' not in title:
                links.add(Link(title))

        return links


# wiki = WikiParserSmarter()

# print(wiki.get_backlinks("cat"))

