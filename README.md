# TelegramSoccerBot
A Telegram Bot intended to save time in management of soccer matches.
Currently, expects to receive a YML configuration located at `./tfab_data/tfab_configuration.yaml`.

## Botito's Menu - Prototype
### Private Chat View:
#### Implemented options are prefixed with a checkmark.
- [ ] /help | /start -> Explain about the different options
  - [ ] Rankers Menu
    - [ ] Login: -> (If not logged in) What's the secret password? -> Thanks! Use /help to proceed.
      - [ ] Rank: -> Who do you want to rank? -> Rank that player
      - [ ] My Ranking: -> Prints a message with all ranked players, and a list of all unranked players
- [ ] Administrators Menu
     - [ ] Login: -> (If not logged in) What's the secret password? -> Thanks! Use /help to proceed.
       - [ ]  Games Menu
           - [ ]  Roster Menu
               - [ ] Today's Roster: -> Please send today's message -> Successfully loaded today's list
               - [ ] Outside Player: -> References the Add Player Menu 
               - [ ] Show: -> Shows today's players
           - [ ]  Groups Menu
               - [ ] Generate: -> Generates today's groups, with the sum of each group at the end
               - [ ] Show: -> Shows today's groups
       - [ ]  Players Menu
           - [X] Add Player: -> What's the player name? -> Characteristics -> Added successfully
           - [ ] Edit Player: -> What's the player name? -> Player edit menu (currently- GK/Attacker/Defender)
           - [X] Show players -> Shows all players and their characteristics.
           - [ ] Delete Player -> What's the player name? -> Succesfully deleted X.

### Group View:
    /help -> Explain about the different options
    /todayinfo -> Shows today's different groups with their score sum, or an indicative message if there are no generated groups yet

##  Version 1.0:
The prototype above will be implemented to completion.

## Version 2.0
    Some niche features, like:
    * Players that want to be put together in the same group
    * Additional features for player characteristics
    * TBA