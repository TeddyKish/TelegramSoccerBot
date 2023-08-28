# TelegramSoccerBot
A Telegram Bot intended to save time in management of soccer matches.

## Botito's Menu - Prototype
### Private Chat View:
    /help -> Explain about the different options
    /start -> What's the secret password? -> Great! What's your name? -> Start ranking all available players
    /ranker
        /rank -> Who do you want to rank? -> Rank that player
        /myranking -> Prints a message with all ranked players, and a list of all unranked players
        /settings
            /changename -> What's your name? -> Succesfully updated
            /getadmin -> What's the Admin password? -> Successfully made you an admin of this bot!
            /reset -> Are you sure you want to reset all rankings? -> Successfully reset rankings, deletes the chat and everything
    /admin
        /gameday
            /list
                /set -> Please send today's message -> Successfully loaded today's list
                /rankmazmin -> What's the name of the mazmin? -> Give them a number -> Do they have special attributes -> Successfully saved <mazmin_name>'s ranking
                /show -> Shows today's players
            /groups
                /generate -> Generates today's groups, with the sum of each group at the end
                /show -> Shows today's groups
        /players
            /show -> What's the player name? (or 'all' for everyone) -> Shows all players and their characteristics
            /edit -> What's the player name? -> Player edit menu (currently- GK/ATT/DEF/MID)

### Group View:
    /help -> Explain about the different options
    /todayinfo -> Shows today's different groups with their score sum, or an indicative message if there are no generated groups yet

##  Version 1.0 
The prototype above will be implemented to completion.

## Version 2.0
Some niche features, like:
* Players that want to be put together in the same group
* Additional features for player characteristics
* TBA