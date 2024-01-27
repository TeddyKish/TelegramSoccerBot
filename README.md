# TelegramSoccerBot
A Telegram Bot intended to save time in management of soccer matches.
Currently, expects to receive a YML configuration located at `./tfab_data/tfab_configuration.yaml`.

## Botito's Menu - Prototype
### Private Chat View:
#### Implemented options are prefixed with a checkmark.
- [X] /help | /start -> Explain about the different options
  - [X] Rankers Menu
    - [X] Login: -> (If not logged in) What's the secret password? -> Thanks! Use /help to proceed.
        - [X] Rank Everyone: -> *Gets a template message* Please fill this message and send it -> Success!
      - [X] My Ranking: -> Prints a message with all ranked players, and a list of all unranked players
  - [X] Administrators Menu
     - [X] Login: -> (If not logged in) What's the secret password? -> Thanks! Use /help to proceed.
       - [X] Matchdays Menu
           - [X] Today's Roster: -> Please send today's message -> Successfully loaded today's list
           - [X] Generate: -> Generates today's teams, with the sum of each team's individual ratings at the end 
           - [X] Show: -> Shows today's information
       - [X]  Players Menu
           - [X] Add Player: -> What's the player name? -> Characteristics -> Added successfully
           - [X] Edit Player: -> What's the player name? -> Player edit menu (currently- GK/Attacker/Defender)
           - [X] Show players -> Shows all players and their characteristics.
           - [X] Delete Player -> What's the player name? -> Succesfully deleted X.

### Group View:
    /help -> Explain about the different options
    /todayinfo -> Shows today's different teams with their score sum, or an indicative message if there are no generated teams yet

## Released: Version 1.0:
The prototype above will be implemented to completion.

## Unreleased: Version 1.1:
- [X] Remove goalies from the ranked list
- [ ] Add the option to rank a specific player
- [ ] Reorganize the framework
- [ ] Enforce player-coupling/decoupling requirements
- [ ] Enforce removal of faulty rankings

## Version 2.0
    Some niche features, like:
    * Additional features for player characteristics
    * A return button from each menu backwards
    * TBA