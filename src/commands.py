from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatPermissions
from telegram.ext import ConversationHandler
import random
import logging
import json
from operator import itemgetter
from math import ceil
from Player import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# global variables
joining = False  # control joining phase
gamechat_id = None  # This is the main group for the game
narrator_id = None  # The ID of the narrator. He is the first to join the game
playerlist_alive = []
playerlist_dead = []
all_roles = {}
role_list = []  #list of chosen roles
srole_list = []  #list of special roles
accused = []  # Liste der angeklagten Spieler bei der Abstimmung
vote_process = 0  # keeping track of vote process


def narratorlog(context, log):
    global narrator_id
    if narrator_id:
        context.bot.send_message(chat_id=narrator_id, text=log)


def set_narrator_id(n_id):
    global narrator_id
    narrator_id = n_id


def set_gamechat_id(g_id):
    global gamechat_id
    gamechat_id = g_id


def set_joining_again():
    global joining
    joining = True


def check_for_group(update) -> bool:  # can be used to check if the command was send in a group
    if update.effective_chat.type == "supergroup":
        return True
    else:
        update.effective_chat.send_message(text="Please use this command only in the group you are playing in")
        return False


def check_for_chat(update) -> bool:  # can be used to check if the command was send in a private chat
    if update.effective_chat.type == "private":
        return True
    else:
        update.effective_chat.send_message(text="Please use this command only in private chat with me")
        return False


def check_for_narrator(update) -> bool:  # can be used for commands exclusive to the narrator
    if update.message.from_user.id == narrator_id:
        return True
    else:
        update.effective_chat.send_message(text="This command can only be used by the narrator")
        return False


def start(update, context):  # sends message when starting a chat with the bot
    update.effective_chat.send_message(text=
                                       "Hello, this is Werwolf_bot! \n Type '/join' to join the game."
                                       )


def start_join(update, context):  # starts the joining-phase
    global joining
    if check_for_group(update) & check_for_narrator(update):
        if not joining:
            joining = True
            global gamechat_id
            if gamechat_id is None:
                gamechat_id = update.effective_chat.id
                save = json.load(open('saveFiles/gamesave.json'))
                with open('saveFiles/gamesave.json', 'w') as savefile:
                    save['Gamechat'] = gamechat_id
                    save['Joining'] = True
                    json.dump(save, savefile)

            update.effective_chat.send_message(text=
                                               "Joining Phase initiated. \n You can join the game now by writing me (the bot) via private chat!"
                                               )
            narratorlog(context, "Joining Phase initiated")
            logger.info("Joining Phase initiated")

        else:
            update.effective_chat.send_message(text="The game is already in the Joining Phase")


def end_join(update, context):  # ends the joining-phase
    global joining
    if check_for_group(update) & check_for_narrator(update):
        if joining:
            joining = False
            save = json.load(open('saveFiles/gamesave.json'))
            with open('saveFiles/gamesave.json', 'w') as savefile:
                save['Joining'] = False
                json.dump(save, savefile)
            narratorlog(context, "Joining Phase concluded")
            logger.info("Joining Phase concluded")
            update.effective_chat.send_message(text="Joining Phase concluded")
        else:
            update.effective_chat.send_message(text="The game is not in the Joining Phase")


def n_join(update, context):  # let's the narrator join as such
    if check_for_chat(update):
        global narrator_id
        if narrator_id is None:
            narrator_id = update.message.from_user.id
            update.effective_chat.send_message(
                'You are now the narrator. Good luck\n'
                'The commands you can use, are:\n'
                '/start_join\n'
                '/end_join\n'
                '/choose_roles\n'
                '/distr_roles\n'
                '/vote <name1> <name2> <name3>\n'
                '/results\n'
                '/kill <name>\n'
                '/good_morning\n'
                '/good_night\n'
                '/reset'
            )
            logger.info(update.message.from_user.name + " is now the narrator")
            save = json.load(open('saveFiles/gamesave.json'))
            with open('saveFiles/gamesave.json', 'w') as savefile:
                save['Narrator'] = narrator_id
                json.dump(save, savefile)
        else:
            update.effective_chat.send_message("There is already a narrator")


def join(update, context) -> int:  # adds the player who sent the command to the game
    if check_for_chat(update):
        if joining:
            if context.bot.get_chat_member(gamechat_id, update.message.from_user.id) is not None:
                for player in playerlist_alive:
                    if player.id == update.message.from_user.id:
                        update.effective_chat.send_message(text="You already joined the game")
                        return ConversationHandler.END
                update.effective_chat.send_message(text="Please enter your name:\n(type '/cancel' to cancel)")
                return 0
        else:
            update.effective_chat.send_message(text="The game is not open to join")
            return ConversationHandler.END


def join_name(update, context) -> int:
    input_name = update.message.text.replace(" ", "")
    for player in playerlist_alive:
        if player.name == input_name:
            update.effective_chat.send_message(
                text="Sorry there is already a player with this name. Please enter a different name:")
            return 0
    playerlist_alive.append(Player(update.message.from_user.id, input_name, "", None, None))
    update.effective_chat.send_message(
        text="The name you entered is '" + input_name + "'.\n Do you wanna keep that? (yes/no).",
        reply_markup=ReplyKeyboardMarkup([["yes", "no"]], one_time_keyboard=True))
    return 1


def join_name_re(update, context) -> int:
    if update.message.text.lower() == "yes":
        update.effective_chat.send_message(text="Name saved! \n May I also ask for your pronouns? \n(If they are not listed or you don't want share them you can use the normal keyboard to write anything.)", reply_markup=ReplyKeyboardMarkup([["er/ihm", "sie/ihr", "they/them"]], one_time_keyboard=True))
        return 2
    elif update.message.text.lower() == "no":
        for player in playerlist_alive:
            if player.id == update.effective_chat.id:
                playerlist_alive.remove(player)
                break
        update.effective_chat.send_message(text="Please enter a new name:", reply_markup=ReplyKeyboardRemove())
        return 0
    else:
        update.effective_chat.send_message("Please enter 'yes' or 'no'",
                                           reply_markup=ReplyKeyboardMarkup([["yes", "no"]], one_time_keyboard=True))
        return 1


def join_pronouns(update, context) -> int:
    input_pro = update.message.text
    for player in playerlist_alive:
        if player.id == update.effective_chat.id:
            player.pronouns = input_pro
            update.effective_chat.send_message(
                text="The pronouns you entered are \n'" + input_pro + "'.\n Do you wanna keep that? (yes/no).",
                reply_markup=ReplyKeyboardMarkup([["yes", "no"]], one_time_keyboard=True))
            return 3


def join_pronouns_re(update, context) -> int:
    if update.message.text.lower() == "yes":
        update.effective_chat.send_message(text="You joined the game. Have fun!", reply_markup=ReplyKeyboardRemove())
        for player in playerlist_alive:
            if player.id == update.effective_chat.id:
                save = json.load(open('saveFiles/gamesave.json'))
                with open('saveFiles/gamesave.json', 'w') as savefile:
                    p_dict = {'id': player.id, 'name': player.name, 'pronouns': player.pronouns, 'role': None, 'special_role': None, 'silence_counter': 0, 'alive': True}
                    save['Players'].append(p_dict)
                    json.dump(save, savefile)
                narratorlog(context, player.name + ' (' + player.pronouns + ") joined the game")
                logger.info(player.name + ' (' + player.pronouns + ") joined the game")
                return ConversationHandler.END
    elif update.message.text.lower() == "no":
        update.effective_chat.send_message(text="Please enter different pronouns:", reply_markup=ReplyKeyboardMarkup([["er/ihm", "sie/ihr", "they/them"]], one_time_keyboard=True))
        return 2
    else:
        update.effective_chat.send_message("Please enter 'yes' or 'no'",
                                           reply_markup=ReplyKeyboardMarkup([["yes", "no"]], one_time_keyboard=True))
        return 3


def join_cancel(update, context) -> int:
    for player in playerlist_alive:
        if player.id == update.effective_chat.id:
            playerlist_alive.remove(player)
    update.effective_chat.send_message("Joining has been canceled")
    return ConversationHandler.END


def list_players(update, context):  # lists all living and dead players
    players_out = "****Alive**** \n"
    for player in playerlist_alive:
        players_out += player.name + ' (' + player.pronouns + ')' + '\n'
    players_out += "\n ****Dead**** \n"
    for player in playerlist_dead:
        players_out += player.name + ' (' + player.pronouns + ')' + " - " + player.role + '\n'
    update.effective_chat.send_message(text=players_out)


def list_roles(update, context):  # lists all roles that are in the game
    rolefile = json.load(open('../config/roles.json'))
    roles_out = "**Roles** \n"
    for r in rolefile['Roles']:
        if list([x for x in playerlist_alive if x.role == r['name']]) or list([x for x in playerlist_dead if x.role == r['name']]):
            roles_out += r['name'] + '\n'
    roles_out += "\n **Special Roles** \n"
    for s in rolefile['SpecialRoles']:
        if list([x for x in playerlist_alive if x.special_role == s['name']]) or list([x for x in playerlist_dead if x.special_role == s['name']]):
            roles_out += s['name'] + '\n'
    update.effective_chat.send_message(text=roles_out)


def reshape(arr, cols):
    rows = ceil(len(arr) / cols)
    res = []
    for row in range(rows):
        current_row = []
        for col in range(cols):
            arr_idx = row * cols + col
            if arr_idx < len(arr):
                current_row.append(arr[arr_idx])
        res.append(current_row)
    return res


def cr_start(update, context) -> int:  # for the narrator to choose the roles that are in the game
    global all_roles
    if check_for_chat(update) and check_for_narrator(update):
        if not joining:
            all_roles = json.load(open('../config/roles.json'))
            roles_keyboard = reshape(list(map(itemgetter('name'), all_roles['Roles'])), 3)
            sroles_keyboard = reshape(list(map(itemgetter('name'), all_roles['SpecialRoles'])), 3)
            if len(role_list) >= len(playerlist_alive):
                update.effective_chat.send_message(text="All roles have been chosen. Do you want to add any special roles? (Type 'end' if you are finished)",
                                                   reply_markup=ReplyKeyboardMarkup(sroles_keyboard))
            else:
                update.effective_chat.send_message(text="There are " + str(len(playerlist_alive)) + " roles to choose. What will it be? (Type '/cancel' to cancel.)",
                                                   reply_markup=ReplyKeyboardMarkup(roles_keyboard))
            return 1
        else:
            update.effective_chat.send_message(text="This command can only be used after the joining phase")
    return ConversationHandler.END


def choose_roles(update, context) -> int:
    global all_roles
    global role_list
    global srole_list
    if len(role_list) < len(playerlist_alive):
        if update.message.text in list(map(itemgetter('name'), all_roles['Roles'])):
            role_list.append(update.message.text)
            logger.info("added " + update.message.text)
            if len(role_list) >= len(playerlist_alive):
                sroles_keyboard = reshape(list(map(itemgetter('name'), all_roles['SpecialRoles'])), 3)
                update.effective_chat.send_message(
                    text="All roles have been chosen. Do you want to add any special roles? (Type 'end' if you are finished)",
                    reply_markup=ReplyKeyboardMarkup(sroles_keyboard))
                return 1
            update.effective_chat.send_message(text="There are " + str(len(playerlist_alive)) + "roles left  to choose. (Type '/cancel' to cancel.) \n The current chosen roles are: \n" + '\n'.join(role_list))
            return 1
        else:
            update.effective_chat.send_message(text="I do not know this role. Choose a different one.")
            return 1
    else:
        if update.message.text == 'end':
            update.effective_chat.send_message(
                text="The final list of roles is: \n **Roles** \n" + '\n'.join(role_list) +'\n' + "**Special Roles** \n" + '\n'.join(srole_list) + "\nIf you are not happy with this use '/choose_roles' again and cancel to delete all chosen roles.",
                reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        if update.message.text in list(map(itemgetter('name'), all_roles['SpecialRoles'])):
            srole_list.append(update.message.text)
            logger.info("added "+update.message.text)
            update.effective_chat.send_message(text="Do you want to add another special roles? (Type 'end' if you are finished) \n The current chosen special roles are: \n" + '\n'.join(srole_list))
            return 1
        else:
            update.effective_chat.send_message(text="I do not know this role. Choose a different one.")
            return 1


def cr_cancel(update, context) -> int:  # cancel the choose_role process
    global role_list, srole_list
    role_list = []
    srole_list = []
    update.effective_chat.send_message(text='All chosen roles have been deleted.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def distr_roles(update, context):  # distributes the roles to the players
    if not joining and check_for_narrator(update) and check_for_group(update):
        global role_list, srole_list
        if len(role_list) < len(playerlist_alive):
            update.effective_chat.send_message(text="Please choose the roles you wanna play with first. You can do that with the command '/choose_roles'")
            return
        # shuffle rolelist and distribute to players
        dist_role_list = role_list.copy()
        random.shuffle(dist_role_list)
        for i in range(len(role_list)):
            playerlist_alive[i].role = dist_role_list[i]
        narratorlog(context, "Roles shuffled and distributed")
        logger.info("Roles shuffled and distributed")
        # distribute special roles to players
        i = 0
        for player in random.sample(playerlist_alive, len(srole_list)):
            player.special_role = srole_list[i]
            i += 1
        # sending roles to players
        for player in playerlist_alive:
            o = "Your role is '" + player.role + "'!\n"
            if player.special_role is not None:
                o += "You have an additional role as well: '" + player.special_role + "'.\n"
            o += "I can't handle special abilities (yet), so if there is anything to do, the narrator will take care of it."
            context.bot.send_message(chat_id=player.id, text=o)
            o = "Assigned " + player.role
            if player.special_role is not None:
                o += " and " + player.special_role
            o += " to " + player.name
            narratorlog(context, o)
        save = json.load(open('saveFiles/gamesave.json'))
        with open('saveFiles/gamesave.json', 'w') as savefile:
            for i in range(len(playerlist_alive)):
                save['Players'][i]['role'] = playerlist_alive[i].role
                save['Players'][i]['special_role'] = playerlist_alive[i].special_role
            json.dump(save, savefile)
        update.effective_chat.send_message(
            "Roles have been distributed. Everyone should know their role now. \n Good luck!")
        logger.info("All Players know their roles now")


def vote(update, context):  # starts the voting process
    if check_for_group(update) and check_for_narrator(update):
        global accused
        update.effective_chat.send_message(text="Voting has started!\n Please vote via private chat.")
        accused = context.args
        for player in playerlist_alive:
            context.bot.send_message(chat_id=player.id,
                                     text="Please vote for the person you wanna see dead.\n Choose from the options below.",
                                     reply_markup=ReplyKeyboardMarkup([accused], one_time_keyboard=True))
        narratorlog(context, "Voting process initiated")
        logger.info("Voting process initiated")


def vote_answer(update, context):  # collects the answer of the votes
    if not accused:
        return
    for player in playerlist_alive:
        if player.id == update.effective_chat.id:
            if player.vote is None:
                if update.message.text in accused:
                    player.vote = update.message.text
                    update.effective_chat.send_message(
                        "Thanks for your vote!\n You may change your vote with '/change_vote' until the results are out.",
                        reply_markup=ReplyKeyboardRemove())
                    global vote_process
                    vote_process += 1
                    if vote_process == ceil(len(playerlist_alive)/2) or vote_process == len(playerlist_alive)-1:
                        context.bot.send_message(chat_id=gamechat_id, text="Vote process: " + str(vote_process) + '/' + str(len(playerlist_alive)))
                    narratorlog(context, player.name + "voted for" + update.message.text)
                    logger.info(player.name + "has voted")
                    return
                else:
                    update.effective_chat.send_message(text="Please vote for one of the accused players.",
                                                       reply_markup=ReplyKeyboardMarkup([accused],
                                                                                        one_time_keyboard=True))
                    return
            else:
                update.effective_chat.send_message(
                    text="You have already voted. You can use '/change_vote' if you want to change your vote.")
                return
    update.effective_chat.send_message(text="Sorry, you can't vote.")
    return


def change_vote(update, context):  # allows players to change their vote before the deadline
    if check_for_chat(update):
        for player in playerlist_alive:
            if player.id == update.effective_chat.id:
                player.vote = None
                global vote_process
                vote_process -= 1
                update.effective_chat.send_message(
                    text="Your vote has now been erased. Please vote again from the options below.",
                    reply_markup=ReplyKeyboardMarkup([accused], one_time_keyboard=True))
                narratorlog(context, player.name + " erased their vote")
                logger.info(player.name + " erased their vote")
                return
        update.effective_chat.send_message(text="Sorry, you can't vote.")
        return


def results(update, context):  # finishes the voting process
    global accused
    if check_for_group(update) and accused != [] and check_for_narrator(update):
        votes_list = []
        for victim in accused:
            votes = []
            for player in playerlist_alive:
                if player.vote == victim:
                    votes.append(player.name)
            votes_list.append(votes)
        out = "Results: \n"
        for i in range(len(votes_list)):
            out += "'" + accused[i] + "' [" + str(len(votes_list[i])) + "]: " + ", ".join(votes_list[i]) + '\n'

        not_voted = []
        for player in playerlist_alive:
            if player.vote is None:
                not_voted.append(player.name)
                context.bot.send_message(chat_id=player.id, text="You didn't vote. Make sure to vote next time.",
                                         reply_markup=ReplyKeyboardRemove())
        out += "No vote: " + ", ".join(not_voted) + '\n'

        winner = votes_list.index(max(votes_list, key=len))
        draw = False
        for i in range(len(votes_list)):
            if len(votes_list[i]) == len(votes_list[winner]) and i != winner:
                draw = True
                break
        if draw:
            out += "It's a draw!"
            narratorlog(context, "The vote has ended in a draw")
            logger.info("The vote ended in a draw.")
        else:
            out += "This means '" + accused[winner] + "' got the most votes and should die."
            narratorlog(context, "Results have been shared. " + accused[winner] + " got the most votes.")
            logger.info("Results have been shared. " + accused[winner] + " got the most votes.")
        update.effective_chat.send_message(out)

        accused = []
        global vote_process
        vote_process = 0
        for player in playerlist_alive:
            player.vote = None


def kill(update, context):  # Command for narrator to kill a player
    if check_for_group(update) and check_for_narrator(update):
        dead = context.args[0]
        for player in playerlist_alive:
            if player.name == dead:
                context.bot.restrict_chat_member(gamechat_id, player.id, ChatPermissions(can_send_messages=False))
                o = player.name + " died. They were "
                if player.role is not None:
                    o += player.role + "!"
                update.effective_chat.send_message(o)
                narratorlog(context, player.name + "killed.")
                logger.info(player.name + " killed.")

                # changing save-file
                save = json.load(open('saveFiles/gamesave.json'))
                with open('saveFiles/gamesave.json', 'w') as savefile:
                    for p in save['Players']:
                        if p['id'] == player.id:
                            p['alive'] = False
                    json.dump(save, savefile)

                playerlist_dead.append(player)
                playerlist_alive.remove(player)
                return
        update.effective_chat.send_message("There is no player with that name, that can be killed")


def good_morning(update, context):  # starts the day/ ends the night
    if check_for_group(update) and check_for_narrator(update):
        for player in playerlist_alive:
            context.bot.restrict_chat_member(gamechat_id, player.id,
                                             ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                                             can_send_other_messages=True))
            player.silence_counter += 1
            save = json.load(open('saveFiles/gamesave.json'))
            with open('saveFiles/gamesave.json', 'w') as savefile:
                for p in save['Players']:
                    p['silence_counter'] += 0
                json.dump(save, savefile)
        update.effective_chat.send_message("Good Morning!")


def good_night(update, context):  # ends the day/ starts the night
    if check_for_group(update) and check_for_narrator(update):
        for player in playerlist_alive:
            context.bot.restrict_chat_member(gamechat_id, player.id, ChatPermissions(can_send_messages=False))
            if player.silence_counter == 1:
                context.bot.send_message(chat_id=player.id, text="You didn't write anything today. Make sure to be active tomorrow, otherwise I gotta snitch to the narrator that you have to die and nobody wants that.")
                narratorlog(context, player.name + " didn't write anything today.")
            elif player.silence_counter >= 2:
                narratorlog(context, player.name + " was not active for multiple days. Do with that info what you want.")
        update.effective_chat.send_message("Good Night!")


def two_day_rule(update, context):  # sets players 'silence_counter' to zero if they write something
    if update.effective_chat.id == gamechat_id:
        for player in playerlist_alive:
            if player.id == update.message.from_user.id:
                if player.silence_counter >= 0:
                    player.silence_counter = 0
                    save = json.load(open('saveFiles/gamesave.json'))
                    with open('saveFiles/gamesave.json', 'w') as savefile:
                        for p in save['Players']:
                            if player.id == p['id']:
                                p['silence_counter'] = 0
                        json.dump(save, savefile)


def rules(update, context): # to ask the bot for either all or specific rules
    rolefile = json.load(open('../config/roles.json'))
    rulesfile = json.load(open('../config/rules.json'))
    if context.args:
        role = context.args[0]
        if list([x for x in playerlist_alive if x.role == role or x.special_role == role]) or list([x for x in playerlist_dead if x.role == role or x.special_role == role]):
            for r in rolefile['Roles']:
                if r['name'] == role:
                    update.effective_chat.send_message(text=r['description'])
                    return
            for s in rolefile['SpecialRoles']:
                if s['name'] == role:
                    update.effective_chat.send_message(text=s['description'])
                    return
            update.effective_chat.send_message(text="No description for this role found.")
        else:
            update.effective_chat.send_message(text="This role is not used in this game.")
    else:
        all_rules = rulesfile['General'] + "\n\n\nChats:\n\n"
        for chat in rulesfile['Chats']:
            all_rules += chat['name'] + ": " + chat['description'] + '\n\n'
        all_rules += "\n\n\nRollen: \n\n"
        for r in rolefile['Roles']:
            if list([x for x in playerlist_alive if x.role == r['name']]) or list([x for x in playerlist_dead if x.role == r['name']]):
                all_rules += r['name'] + '\n' + r['description'] + "\n\n"
        all_rules += "\n\n\nSpezialrollen: \n\n"
        for s in rolefile['SpecialRoles']:
            if list([x for x in playerlist_alive if x.special_role == s['name']]) or list([x for x in playerlist_dead if x.special_role == s['name']]):
                all_rules += s['name'] + '\n' + s['description'] + "\n\n"
        update.effective_chat.send_message(text=all_rules)


def reset(update, context):
    if check_for_narrator(update):
        global playerlist_alive
        global gamechat_id
        global playerlist_dead
        for player in playerlist_dead:
            context.bot.restrict_chat_member(gamechat_id, player.id,
                                             ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                                             can_send_other_messages=True))
        with open('saveFiles/gamesave.json', 'w') as newfile:
            blank_json = {
                'Narrator': None,
                'Gamechat': None,
                'Loading': False,
                'Players': []
            }
            json.dump(blank_json, newfile)
        gamechat_id = None
        global narrator_id
        narrator_id = None
        playerlist_alive = []
        playerlist_dead = []
        update.effective_chat.send_message("Everything has been reset.")
        logger.info("Everything has been reset.")
