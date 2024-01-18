from game.wiki_game_async import WikiGameAsync
import unittest

from loguru import logger



class TestWiki(unittest.TestCase):
    def test_1(self):
        wiki = WikiGameAsync()
        time = float(wiki.play("Red_Hot_Chili_Peppers", "Server", False))
        assert time < 60

    def test_3(self):
        wiki = WikiGameAsync()
        time = float(wiki.play("Adolf_Hitler", "Benito_Mussolini", False))
        assert time < 60

    def test_5(self):
        wiki = WikiGameAsync()
        time = float(wiki.play("Red_Hot_Chili_Peppers", "New_York_Giants_(baseball)", False))
        assert time < 60

    def test_7(self):
        wiki = WikiGameAsync()
        time = float(wiki.play("Dog", "1984", False))
        assert time < 60

    def test_9(self):
        wiki = WikiGameAsync()
        time = float(wiki.play("FIFA", "1984", False))
        assert time < 60

    def test_11(self):
        wiki = WikiGameAsync()
        time = float(wiki.play("Dog", "Server", False))
        assert time < 60


if __name__ == "__main__":
    unittest.main()
