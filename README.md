# TelegramSoccerBot
    A Telegram Bot intended to save time in management of soccer matches.
    Currently expects to receive a YML configuration located at `./tfab_data/tfab_configuration.yaml`.

## Botito's Menu - Prototype
### Private Chat View:
    /help | /start -> Explain about the different options
    /ranker
    If not logged in -> What's the secret password? -> Thanks! Use /help to proceed.
        /rank -> Who do you want to rank? -> Rank that player
        /myranking -> Prints a message with all ranked players, and a list of all unranked players
    /admin
    If not logged in -> What's the secret password? -> Thanks! Use /help to proceed.
        /games
            /list
                /set -> Please send today's message -> Successfully loaded today's list
                /rankmazmin -> What's the name of the mazmin? -> Give them a number -> Do they have special attributes -> Successfully saved <mazmin_name>'s ranking
                /show -> Shows today's players
            /groups
                /generate -> Generates today's groups, with the sum of each group at the end
                /show -> Shows today's groups
        /players
            /add -> What's the player name? -> Characteristics -> Added successfully
            /edit -> What's the player name? -> Player edit menu (currently- GK/Attacker/Defender)
            /show -> What's the player name? (or 'all' for everyone) -> Shows all players and their characteristics
            /delete -> What's the player name? -> Succesfully deleted X.

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