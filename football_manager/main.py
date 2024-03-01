from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from pydantic import BaseModel
from typing import List, Optional
import uuid

users = {}
TOKEN = ""
subscribers = {}
game = {}

handlers_keys = {
  "/rg": "הירשם כמנוי",
  "/ng": "אשר  הגעה למשחק הקרוב",
  "/gg": "קבל משתמשים למשחק הקרוב",
  "/name": "שנה שם /name <שם פרטי>"
}

class Player(BaseModel):
    t_id: str | None = None
    t_name: str | None = None
    nickname: str | None = None

    def update_nickname(self, nickname):
      self.nickname = nickname


class Subscriber(Player):
    sub_type: str # enum regular/guest

class NextGame(BaseModel):
    players: List[Subscriber] = []
    num_players: int = 15

    def __contains__(self, ttid):
        for player in self.players:
            if player.t_id == ttid:
              return True
        return False

    def reset_next_game(self):
        self.players = []
    
    def signup(self, sub: Subscriber):
        if len(self.players) < self.num_players and not sub.t_id in self:
            self.players.append(sub)
            return True
        return False

class Manager(BaseModel):
    players: List[Player] | None = None
    subscribers: List[Subscriber] | None = None
    next_game: NextGame | None = None

    def add_player(self, t_id, t_name):
      p = Player(t_id=t_id, t_name=t_name)
      self.players.append(p)
    
    def add_subscriber(self, player: Player, sub_type: str):
        sub = Subscriber(sub_type=sub_type, **player.model_dump())
        self.subscribers.append(sub)
    
    def init(self):
        self.players = []
        self.subscribers = []
        self.next_game = NextGame()

class NodimSession(BaseModel):
  _session_id: int
  manager: Manager
  nodim_bot: Application | None = None

  class Config:
      arbitrary_types_allowed = True
  
  @classmethod
  def fart(cls):
    _id = uuid.uuid4()
    _bot = None
    manager = Manager()
    manager.init()
    return cls(
      _session_id=_id,
      nodim_bot = _bot,
      manager=manager
    )
  
  def get_player(self, update: Update) -> Player:
      player_id = update.effective_message.id
      if self.manager.players is None:
        return
      next(
            (
                player
                for player in self.manager.players
                if player.t_id == player_id
            ),
            None
        )
  
  def get_subscriber(self, update: Update) -> Subscriber:
      id = update.effective_message.id
      return next(filter(self.manager.subscribers, lambda x: x.t_id==id), None)

  async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
      player = self.get_player(update)
      if player:
        self.manager.add_subscriber(player, "מנוי")

  async def add_user_to_game_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
      global game
      user_id = update.effective_chat.id
      if user_id in self.manager.next_game:
        await update.message.reply_text(f"{game[update.effective_chat.id]} נרשמת כבר נסיך")
      else:
        sub = self.get_subscriber(update)
        if self.manager.next_game.signup(sub):
          await update.message.reply_text(f'{update.effective_user.first_name} נרשמת בהצלחה למשחק הקרוב')
        else:
          await update.message.reply_text(f'{update.effective_user.first_name} המשחק כבר מלא או שכבר נרשמת אליו')

  async def game_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
      global game
      msg = ""
      for key, value in game.items():
        msg += f"user {key} -> {value} יגיע למשחק הקרוב\n"
      await update.message.reply_text(msg)


  async def notify_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
      for sub in self.manager.subscribers:
          msg = f"{sub.nickname}השתמש ב /ng כדי להירשם למשחק הקרוב"
          await context.bot.send_message(chat_id=sub.t_id, text=msg)

  async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
      """Parses the CallbackQuery and updates the message text."""
      query = update.callback_query

      # CallbackQueries need to be answered, even if no notification to the user is needed
      # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
      await query.answer()
      if query.data == "subscribe":
          await self.subscribe(update, context)
      elif query.data == "register":
          await self.add_user_to_game_handler(update, context)
      else:
        await query.edit_message_text(text=f"Selected option: {query.data}")

  async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
      """Sends a message with three inline buttons attached."""
      self.manager.add_player(update.effective_chat.id, update.effective_chat.first_name)
      keyboard = [
          [
              InlineKeyboardButton("Subscribe", callback_data="subscribe"),
              InlineKeyboardButton("Register for next game", callback_data="register"),
          ],
          [InlineKeyboardButton("Option 3", callback_data="3")],
      ]

      reply_markup = InlineKeyboardMarkup(keyboard)

      await update.message.reply_text("Please choose:", reply_markup=reply_markup)

    
  async def name_handler_func(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
      text = update.effective_message.text
      new_name = text.strip("/name ")
      if update.effective_chat.id not in subscribers:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="נסיך תירשם קודם /start")
      else:
        subscribers[update.effective_chat.id] = new_name
        users[update.effective_chat.id] = new_name
        game[update.effective_chat.id] = new_name
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"השם שונה בהצלחה {new_name}")

  def puk(self):
    self.nodim_bot = Application.builder().token(TOKEN).build()
    start_handler = CommandHandler('start', self.start)
    notify_handler = CommandHandler('notify', self.notify_users)
    name_handler = CommandHandler('name', self.name_handler_func)
    subscribers_handler = CommandHandler('rg', self.subscribe)
    games_handler = CommandHandler('ng', self.add_user_to_game_handler)
    games_users_handler = CommandHandler('gg', self.game_users)
    button_handler = (CallbackQueryHandler(self.button))

    handlers = [start_handler, subscribers_handler,games_handler, games_users_handler, notify_handler, name_handler, button_handler]
    self.nodim_bot.add_handlers(handlers)
    self.nodim_bot.run_polling()


def main():
    nodim_session = NodimSession.fart()
    # Start Telegram Bot
    nodim_session.puk()


if __name__ == "__main__":
    main()







