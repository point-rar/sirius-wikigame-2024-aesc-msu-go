from game.wiki_game_async import WikiGameAsync
import unittest

from loguru import logger



class TestWiki(unittest.TestCase):
    def test_1(self):
        time = float(WikiGameAsync().play("Red_Hot_Chili_Peppers", "Server", False))
        assert time < 60

    def test_2(self):
        time = float(WikiGameAsync().play("Adolf_Hitler", "Benito_Mussolini", False))
        assert time < 60

    def test_3(self):
        time = float(WikiGameAsync().play("Red_Hot_Chili_Peppers", "Server", False))
        assert time < 60

    def test_4(self):
        time = float(WikiGameAsync().play("Dog", "1984", False))
        assert time < 60

    def test_5(self):
        time = float(WikiGameAsync().play("FIFA", "1984", False))
        assert time < 60

    def test_6(self):
        time = float(WikiGameAsync().play("Dog", "Server", False))
        assert time < 60


if __name__ == "__main__":
    unittest.main()
