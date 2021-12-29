from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatPermissions
from telegram.ext import ConversationHandler
import random
import logging
from Player import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# global variables
joining = False  # control joining phase
gamechat_id = None  # This is the main group for the game
narrator_id = None  # The ID of the narrator. He is the first to join the game
playerlist_alive = []
playerlist_dead = []
accused = []  # Liste der angeklagten Spieler bei der Abstimmung
vote_process = 0  # keeping track of vote process


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
                with open('saveFiles/werwolf.save', 'a') as savetxt:
                    savetxt.write(str(gamechat_id) + '\n')
            update.effective_chat.send_message(text=
                                               "Joining Phase initiated. \n You can join the game now by writing me (the bot) via private chat!"
                                               )
            logger.info("Joining Phase initiated")
            with open('saveFiles/werwolf.save', 'a') as savetxt:
                savetxt.write('joining\n')
        else:
            update.effective_chat.send_message(text="The game is already in the Joining Phase")


def end_join(update, context):  # ends the joining-phase
    global joining
    if check_for_group(update) & check_for_narrator(update):
        if joining:
            joining = False
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
                '/distr_roles\n'
                '/vote <name1> <name2> <name3>\n'
                '/results\n'
                '/kill <name>\n'
                '/good_morning\n'
                '/good_night\n'
                '/reset'
            )
            logger.info(narrator_id)
            logger.info(update.message.from_user.name + " is now the narrator")
            with open('saveFiles/werwolf.save', 'w') as savetxt:
                savetxt.write(str(narrator_id) + '\n')
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
    playerlist_alive.append(Player(update.effective_chat.id, update.message.from_user.id, input_name, None))
    update.effective_chat.send_message(
        text="The name you entered is '" + playerlist_alive[-1].name + "'.\n Do you wanna keep that? (yes/no).",
        reply_markup=ReplyKeyboardMarkup([["yes", "no"]], one_time_keyboard=True))
    return 1


def join_name_re(update, context) -> int:
    if update.message.text.lower() == "yes":
        update.effective_chat.send_message(text="You joined the game. Have fun!", reply_markup=ReplyKeyboardRemove())
        for player in playerlist_alive:
            if player.chat_id == update.effective_chat.id:
                with open('saveFiles/werwolf.save', 'a') as savetxt:
                    savetxt.write(player.print() + '\n')
                logger.info(player.name + " joined the game")
                return ConversationHandler.END
    elif update.message.text.lower() == "no":
        for player in playerlist_alive:
            if player.chat_id == update.effective_chat.id:
                playerlist_alive.remove(player)
                break
        update.effective_chat.send_message(text="Please enter a new name:", reply_markup=ReplyKeyboardRemove())
        return 0
    else:
        update.effective_chat.send_message("Please enter 'yes' or 'no'",
                                           reply_markup=ReplyKeyboardMarkup([["yes", "no"]], one_time_keyboard=True))
        return 1


def join_cancel(update, context) -> int:
    for player in playerlist_alive:
        if player.chat_id == update.effective_chat.id:
            playerlist_alive.remove(player)
    update.effective_chat.send_message("Joining has been canceled")
    return ConversationHandler.END


def list_players(update, context):  # lists all living and dead players
    players_out = "Alive: \n"
    for player in playerlist_alive:
        players_out += player.name + '\n'
    players_out += "Dead: \n"
    for player in playerlist_dead:
        players_out += player.name + '\n'
    update.effective_chat.send_message(text=players_out)


def distr_roles(update, context):  # distributes the roles to the players
    if not joining and check_for_narrator(update):
        rolelist = []
        # reading roles from txt
        with open('../config/roles.txt', 'r') as rolestxt:
            for role in rolestxt.readlines():
                rolelist.append(role.replace('\n', ''))
        if len(rolelist) != len(playerlist_alive):
            update.effective_chat.send_message(text="The numbers of roles and players do not match")
        else:
            # shuffle rolelist and distribute to players
            random.shuffle(rolelist)
            for i in range(len(rolelist)):
                playerlist_alive[i].role = rolelist[i]
            logger.info("Roles shuffled and distributed")
            # reading special roles from txt
            s_rolelist = []
            with open('../config/special_roles.txt', 'r') as s_rolestxt:
                for s_role in s_rolestxt.readlines():
                    s_rolelist.append(s_role.replace('\n', ''))
                if len(s_rolelist) > len(playerlist_alive):
                    update.effective_chat.send_message(
                        text="The numbers of special roles is higher than the number of players")
                else:
                    # distribute special roles to players
                    i = 0
                    for player in random.sample(playerlist_alive, len(s_rolelist)):
                        player.special_role = s_rolelist[i]
                        i += 1
                    # sending roles to players
                    for player in playerlist_alive:
                        o = "Your role is '" + player.role + "'!\n"
                        if player.special_role is not None:
                            o += "You have an additional role as well: '" + player.special_role + "'.\n"
                        o += "I can't handle special abilities (yet), so if there is anything to do, the narrator will take care of it."
                        context.bot.send_message(chat_id=player.chat_id, text=o)
                        o = "Assigned " + player.role
                        if player.special_role is not None:
                            o += " and " + player.special_role
                        o += " to " + player.name
                        logger.info(o)
                    with open('saveFiles/werwolf.save', 'w') as savetxt:
                        savetxt.write(str(narrator_id)+'\n')
                        savetxt.write(str(gamechat_id)+'\n')
                    for player in playerlist_alive:
                        with open('saveFiles/werwolf.save', 'a') as savetxt:
                            savetxt.write("a," + player.print() + '\n')
                    update.effective_chat.send_message(
                        "Roles have been distributed. Everyone should know their role now.")


def vote(update, context):  # starts the voting process
    if check_for_group(update) and check_for_narrator(update):
        global accused
        update.effective_chat.send_message(text="Voting has started!\n Please vote via private chat.")
        accused = context.args
        for player in playerlist_alive:
            context.bot.send_message(chat_id=player.chat_id,
                                     text="Please vote for the person you wanna see dead.\n Choose from the options below.",
                                     reply_markup=ReplyKeyboardMarkup([accused], one_time_keyboard=True))
        logger.info("Voting process initiated")


def vote_answer(update, context):  # collects the answer of the votes
    if accused == []:
        return
    for player in playerlist_alive:
        if (player.chat_id == update.effective_chat.id):
            if (player.vote is None):
                if update.message.text in accused:
                    player.vote = update.message.text
                    update.effective_chat.send_message(
                        "Thanks for your vote!\n You may change your vote with '/change_vote' until the results are out.",
                        reply_markup=ReplyKeyboardRemove())
                    global vote_process
                    vote_process += 1
                    context.bot.send_message(chat_id=gamechat_id, text="Vote process: " + str(vote_process) + '/' + str(
                        len(playerlist_alive)))
                    logger.info(player.name + " voted for " + update.message.text)
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
            if (player.chat_id == update.effective_chat.id):
                player.vote = None
                global vote_process
                vote_process -= 1
                update.effective_chat.send_message(
                    text="Your vote has now been erased. Please vote again from the options below.",
                    reply_markup=ReplyKeyboardMarkup([accused], one_time_keyboard=True))
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
                context.bot.send_message(chat_id=player.chat_id, text="You didn't vote. Make sure to vote next time.",
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
            logger.info("The vote ended in a draw.")
        else:
            out += "This means '" + accused[winner] + "' got the most votes and should die."
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
                logger.info(player.name + " killed.")

                # changing save-file
                new_text = ""
                with open('saveFiles/werwolf.save', 'r') as savetxt:
                    for line in savetxt:
                        new_line = line.replace("a," + str(player.chat_id), "d," + str(player.chat_id))
                        new_text += new_line
                with open('saveFiles/werwolf.save', 'w') as savetxt:
                    savetxt.write(new_text)

                playerlist_dead.append(player)
                playerlist_alive.remove(player)
                return
        update.effective_chat.send_message("There is no player with that name, that can be killed")


def good_morning(update, context):  # starts the day/ ends the night
    if check_for_group(update):  # and check_for_narrator(update):
        for player in playerlist_alive:
            context.bot.restrict_chat_member(gamechat_id, player.id,
                                             ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                                             can_send_other_messages=True))
        update.effective_chat.send_message("Good Morning!")


def good_night(update, context):  # ends the day/ starts the night
    if check_for_group(update):  # and check_for_narrator(update):
        for player in playerlist_alive:
            context.bot.restrict_chat_member(gamechat_id, player.id, ChatPermissions(can_send_messages=False))
        update.effective_chat.send_message("Good Night!")


def reset(update, context):
    if check_for_narrator(update):
        global playerlist_alive
        global gamechat_id
        global playerlist_dead
        for player in playerlist_dead:
            context.bot.restrict_chat_member(gamechat_id, player.id,
                                             ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                                             can_send_other_messages=True))
        open('saveFiles/werwolf.save', 'w').close()
        gamechat_id = None
        global narrator_id
        narrator_id = None
        playerlist_alive = []
        playerlist_dead = []
        update.effective_chat.send_message("Everything has been reset.")
        logger.info("Everything has been reset.")
