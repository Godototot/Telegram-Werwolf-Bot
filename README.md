# Telegram-Werwolf-Bot
A telegram bot that assists the narrator of a game of Werwolf.

## Table of Content
* [Goal](#goal)
* [Technologies](#technologies)
* [Using the Bot](#using-the-bot)
  * [Bot Key](#bot-key)
  * [Permissions](#permissions)
* [Commands](#commands)
  * [General](#general)
  * [Narrator](#narrator)
  * [Player](#player)

## Goal
The goal of this bot is to take away the boring and tiresome work that comes with narrating a game of Werwolf while still leaving the narrator enough room to make the game interesting and deal with unexpected situations


## Technologies
Project is created with:
Python: 3.8.10
with python-telegram-bot 13.8.1
with python-dotenv 0.19.2


## Using the Bot

### Bot Key
The unique key for the telegram bot is hidden in a personal '.env'-file.
To use the code with your own bot, create this file inside the config folder and write:

<em>BOT_KEY='key'</em>

### Permissions
To work properly the bot has to be an Admin in the group he is added to. 


## Commands

### General
<ul>
  <li><strong>start</strong> : first interaction with the bot. They greet you</li>
  <li><strong>list_players</strong> : returns list of all players, sorted in "alive" and "dead"
<li><strong>list_roles</strong> : returns list of all roles that are used in this game
  <li><strong>rules [rolename] </strong> : prints either all rules or the description of a specific role</li>
</ul>

### Narrator
<ul>
  <li><strong>n_join</strong> : you join the game as the narrator if there is no narrator yet</li>
  <li><strong>start_join</strong> : starts the joining-phase and allows players to join</li>
  <li><strong>end_join</strong> : ends the joining-phase</li>
  <li><strong>choose_roles</strong> : can be executeed after joining phase has ended. let's the narrator choose the roles based on a pre-set list and the number of players</li>
  <li><strong>distr_roles</strong> : can be executed after joining phase has ended. distributes the (special) roles from the chosen list to all players</li>
  <li><strong>vote [name1][opt name2][opt name 3]</strong> : starts the voting process. The bot writes each player in PC and let's them choose one from the names through custom keyboard</li>
  <li><strong>results</strong> : ends the voting process and returns the result in the group chat</li>
  <li><strong>kill [name]</strong> : changes the players state to dead and removes their right to write in the group chat</li>
  <li><strong>good morning</strong> : gives all alive players the rights to write in the group chat</li>
  <li><strong>good night</strong> : removes every players rights to write in the group chat</li>
  <li><strong>reset</strong> : deletes all information, including the narrators id</li>
</ul>

### Player
<ul>
  <li><strong>join</strong> : the player has to add a name and is then added to the game. Can only be used during joining phase</li>
  <li><strong>cancel </strong> : cancels the joining process of this player</li>
  <li><strong>change_vote</strong> : can be used during the voting process to change the vote after it has already been locked in</li>
</ul>
