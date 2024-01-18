from game.wiki_game_async import WikiGameAsync
import unittest

from loguru import logger



class TestSum(unittest.TestCase):
    def test_1(self):
        time = float(WikiGameAsync().play("Red_Hot_Chili_Peppers", "Server", False))
        assert time < 4


if __name__ == "__main__":
    unittest.main()
