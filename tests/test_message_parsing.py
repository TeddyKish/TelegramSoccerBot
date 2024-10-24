import datetime
import time
import re
import os
import pytest
from tfab_utils.tfab_message_parser import MessageParser
from tfab_framework.tfab_consts import Consts as TConsts

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

    def test_extract_final_lists_from_message_history(self):
        """
        Extracts all finalized rosters from all games that appear in the contents of all hist files under ./tfab_data/.
        """
        messages = []

        for file in os.listdir("../tfab_data"):
            if "hist" in file:
                with open(f"../tfab_data/{file}", encoding="utf-8") as hfile:
                    # Find all messages using re.findall
                    if file == "hist1.txt":
                        pattern = r"(\d{2}/\d{2}/\d{4}, \d{1,2}:\d{2} - .+?:) (.*?)(?=\d{2}/\d{2}/\d{4}, \d{1,2}:\d{2} -|$)"
                    else:
                        pattern = r"(\[\d{1,2}\.\d{1,2}\.\d{4}, \d{1,2}:\d{2}:\d{2}\] [^\:]+:) (.*?)(?=\[\d{1,2}\.\d{1,2}\.\d{4}, \d{1,2}:\d{2}:\d{2}\]|$)"

                    curr_matches = re.findall(pattern, hfile.read(), re.DOTALL)
                    messages += curr_matches

        actual_lists = {}
        problematic_lists = {}

        for msg in messages:
            # Validate that there are no date errors
            list_sending_date = MessageParser._get_date_value(msg[0])

            result_dict = MessageParser.parse_matchday_message(msg[1])

            if len(result_dict[TConsts.MATCHDAYS_ROSTER_KEY]) != 0 and \
                result_dict[TConsts.MATCHDAYS_DATE_KEY] is not None and \
                result_dict[TConsts.MATCHDAYS_LOCATION_KEY] is not None and \
                result_dict[TConsts.MATCHDAYS_ORIGINAL_MESSAGE_KEY] is not None:

                if time.strptime(list_sending_date, TConsts.MATCHDAYS_DATE_FORMAT) > \
                    time.strptime(result_dict[TConsts.MATCHDAYS_DATE_KEY], TConsts.MATCHDAYS_DATE_FORMAT) and \
                        result_dict[TConsts.MATCHDAYS_DATE_KEY] != "07-01-2022":
                    continue

                if len(result_dict[TConsts.MATCHDAYS_ROSTER_KEY]) < 17:
                    continue

                actual_lists[result_dict[TConsts.MATCHDAYS_DATE_KEY]] = result_dict
            elif result_dict[TConsts.MATCHDAYS_LOCATION_KEY] is not None and len(result_dict[TConsts.MATCHDAYS_ROSTER_KEY]) != 0:
                problematic_lists[list_sending_date] = result_dict

        # Include actual-problematic lists (with manual investigation unfortunately..)
        for date in ["30-08-2022", "28-01-2023"]:
            actual_lists[date] = problematic_lists[date]

        matchday_player_appearances = {}

        for date, match_dict in actual_lists.items():
            for player in match_dict[TConsts.MATCHDAYS_ROSTER_KEY]:
                if player not in matchday_player_appearances.keys():
                    matchday_player_appearances[player] = 1
                else:
                    matchday_player_appearances[player] += 1

            sorted_appearances = dict(sorted(matchday_player_appearances.items(), key=lambda item: item[1], reverse=True))

        with open(f"../tfab_data/appearances-{datetime.datetime.now().strftime(TConsts.MATCHDAYS_DATE_FORMAT)}.txt", "w+", encoding="utf-8") as app_file:
            for player, appearances in sorted_appearances.items():
                app_file.write(f"{player} -> {appearances}\n")

        assert True == True


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

        assert result_dict[TConsts.MATCHDAYS_ROSTER_KEY] is not None and \
               result_dict[TConsts.MATCHDAYS_DATE_KEY] is not None and \
               result_dict[TConsts.MATCHDAYS_LOCATION_KEY] is not None and \
               result_dict[TConsts.MATCHDAYS_ORIGINAL_MESSAGE_KEY] is not None

        assert len(result_dict[TConsts.MATCHDAYS_ROSTER_KEY]) in player_list_sizes
        assert result_dict[TConsts.MATCHDAYS_LOCATION_KEY] in locations

        pattern = re.compile(r"\d{2}-\d{2}-\d{4}")
        assert pattern.search(result_dict[TConsts.MATCHDAYS_DATE_KEY].strip())