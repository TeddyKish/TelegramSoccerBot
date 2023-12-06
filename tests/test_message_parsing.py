import re
import os
import pytest
from ..tfab_message_parser import MessageParser
from ..tfab_database_handler import TFABDBHandler

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
ג'ק = 3
1.תומר = 6
2לא מדורגים:
בטיטו = """

first_dict = {"טדי": "5", "זיו": "3.7", "ישי": "10", "גלעד": "2", "בר א": "9", "ג'ק": "3"}

second_message = "עידן = 5"
second_dict = {"עידן": "5"}

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../tfab_data/data")
matchday_messages = []
matchday_player_appearances = {}

for filename in os.listdir(data_dir):
    file_path = os.path.join(data_dir, filename)

    if os.path.isfile(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            matchday_messages.append((file_path, file.read()))

expected_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../tfab_data/expected")
with open(os.path.join(expected_dir, "locations"), "r", encoding="utf-8") as f:
    locations = f.read().split("\n")

with open(os.path.join(expected_dir, "player_list_sizes"), "r", encoding="utf-8") as f:
    player_list_sizes = [int(line) for line in f.read().split("\n")]

class TestMessageParsing:

    @pytest.mark.parametrize("parameters", [
        (first_message, first_dict),
        (second_message, second_dict)
    ])
    def test_rankings_message(self, parameters):
        message, dictionary = parameters
        assert MessageParser.parse_rankings_message(message) == dictionary

    @pytest.mark.parametrize("message_file", matchday_messages)
    def test_matchday_messages(self, message_file):
        print("File name is {0}".format(message_file[0]))
        result_dict = MessageParser.parse_matchday_message(message_file[1])

        assert result_dict[TFABDBHandler.MATCHDAYS_ROSTER_KEY] is not None and \
               result_dict[TFABDBHandler.MATCHDAYS_DATE_KEY] is not None and \
               result_dict[TFABDBHandler.MATCHDAYS_LOCATION_KEY] is not None and \
               result_dict[TFABDBHandler.MATCHDAYS_ORIGINAL_MESSAGE_KEY] is not None

        assert len(result_dict[TFABDBHandler.MATCHDAYS_ROSTER_KEY]) in player_list_sizes
        assert result_dict[TFABDBHandler.MATCHDAYS_LOCATION_KEY] in locations

        pattern = re.compile(r"\d{2}-\d{2}-\d{4}")
        assert pattern.search(result_dict[TFABDBHandler.MATCHDAYS_DATE_KEY].strip())

        for player in result_dict[TFABDBHandler.MATCHDAYS_ROSTER_KEY]:
            if player not in matchday_player_appearances.keys():
                matchday_player_appearances[player] = 1
            else:
                matchday_player_appearances[player] += 1

        sorted_appearances = dict(sorted(matchday_player_appearances.items(), key=lambda item: item[1], reverse=True))

        for player, appearances in sorted_appearances.items():
            print(f"{player} -> {appearances}")