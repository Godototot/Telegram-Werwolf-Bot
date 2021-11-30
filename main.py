import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from os.path import exists
from dotenv import load_dotenv

from commands import *
from Player import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    load_dotenv()
    updater = Updater(os.environ.get("BOT_KEY"), use_context=True)
    dispatcher = updater.dispatcher

    # read in save.txt in case the bot did shut down
    global gamechat_id
    global narrator_id
    if exists('save.txt'):
        with open('save.txt', 'r') as savetxt:
            lines = savetxt.readlines()
            for l in lines:
                l = l.replace('\n', '')
            for i in range(len(lines)):
                if i == 0:
                    narrator_id = int(lines[i])
                    logger.info("Added narrator again")
                elif i == 1:
                    gamechat_id = int(lines[i])
                    logger.info("Added gamechat again")
                else:
                    cut_line = lines[i].split(',')
                    p = Player(int(cut_line[1]), int(cut_line[2]), cut_line[3])
                    p.role = cut_line[4]
                    if len(cut_line) > 5:
                        p.special_role = cut_line[5]
                    if cut_line[0] == 'a':
                        playerlist_alive.append(p)
                        logger.info("Added " + p.name + " back to the game alive.")
                    else:
                        playerlist_dead.append(p)
                        logger.info("Added " + p.name + " back to the game dead.")
    else:
        open('save.txt', 'x')
        logger.info("Created save file")

    setup_handlers(dispatcher)
    updater.start_polling()

    updater.idle()


def setup_handlers(dispatcher):

    # commandHandlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('start_join', start_join))
    dispatcher.add_handler(CommandHandler('end_join', end_join))
    dispatcher.add_handler(CommandHandler('n_join', n_join))
    dispatcher.add_handler(CommandHandler('list_players', list_players))
    dispatcher.add_handler(CommandHandler('distr_roles', distr_roles))
    dispatcher.add_handler(CommandHandler('vote', vote))
    dispatcher.add_handler(CommandHandler('change_vote', change_vote))
    dispatcher.add_handler(CommandHandler('results', results))
    dispatcher.add_handler(CommandHandler('kill', kill))
    dispatcher.add_handler(CommandHandler('good_morning', good_morning))
    dispatcher.add_handler(CommandHandler('good_night', good_night))
    dispatcher.add_handler(CommandHandler('reset', reset))

    # specialHandlers
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('join', join)],
            states={
                0: [MessageHandler(Filters.text & (~Filters.command), join_name)],
                1: [MessageHandler(Filters.text & (~Filters.command), join_name_re)]
            },
            fallbacks=[CommandHandler('cancel', join_cancel)]
        )
    )
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command) & Filters.chat_type.private, vote_answer))



if __name__ == '__main__':
    main()