import pytest
from ..tfab_message_parser import RankingsMessageParser

first_message = """בלהבלה
בלהלהלה
טדי = 5
זיו = 3.7
בר א = 19
עידן = 0
טדי = 13
גדשגחלשלך
טא = 34
איינ = גך
גלעד =2
= 5
בל = 2.11
גל
teddy =
= 5
עומר 4
עומר == 4
לילה . 3
ישי = 10
בר א = 9
1.תומר = 6
2לא מדורגים:
בטיטו = """

first_dict = {"טדי": "5", "זיו": "3.7", "ישי": "10", "גלעד": "2", "בר א": "9"}

second_message = "עידן = 5"
second_dict = {"עידן": "5"}
class TestMessageParsing:

    @pytest.mark.parametrize("parameters", [
        (first_message, first_dict),
        (second_message, second_dict)
    ])
    def test_rankings_message(self, parameters):
        message, dictionary = parameters
        assert RankingsMessageParser.parse_rankings_message(message) == dictionary