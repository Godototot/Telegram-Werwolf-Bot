import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from os.path import exists
from dotenv import load_dotenv
import json

from commands import *
from Player import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    load_dotenv('../config/.env')
    load_save_file()
    updater = Updater(os.environ.get("BOT_KEY"), use_context=True)
    dispatcher = updater.dispatcher
    setup_handlers(dispatcher)
    updater.start_polling()

    updater.idle()


def load_save_file():  # read in save.json in case the bot shut down
    if not exists('saveFiles/gamesave.json'):
        if not exists('saveFiles'):
            os.mkdir("saveFiles")
        with open('saveFiles/gamesave.json', 'w') as newfile:
            blank_json = {
                'Narrator': None,
                'Gamechat': None,
                'Loading': False,
                'Players': []
            }
            json.dump(blank_json, newfile)

        logger.info("created savefile")
        return

    logger.info("Savefile exists")
    save = json.load(open('saveFiles/gamesave.json'))
    if save['Narrator']:
        set_narrator_id(save['Narrator'])
        logger.info("Added narrator again")
        if save['Gamechat']:
            set_gamechat_id(save['Gamechat'])
            logger.info("Added gamechat again")
            if save['Joining']:
                set_joining_again()
                logger.info("Set joining again")
            if save['Players']:
                for p in save['Players']:
                    new_p = Player(p['id'], p['name'], p['role'], p['special_role'])
                    if p['alive']:
                        playerlist_alive.append(new_p)
                        logger.info("Added " + new_p.name + " back to the game alive.")
                    else:
                        playerlist_dead.append(new_p)
                        logger.info("Added " + new_p.name + " back to the game dead.")


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
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('choose_roles', cr_start)],
            states={
                0: [MessageHandler(Filters.text & (~Filters.command), cr_start)],
                1: [MessageHandler(Filters.text & (~Filters.command), choose_roles)]
            },
            fallbacks=[CommandHandler('cancel', cr_cancel)]
        )
    )
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command) & Filters.chat_type.private, vote_answer))


if __name__ == '__main__':
    main()
