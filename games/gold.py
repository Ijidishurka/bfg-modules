import asyncio
import random
import time
from decimal import Decimal

from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from assets.antispam import antispam, new_earning_msg, antispam_earning
from assets.transform import transform_int as tr
from bot import bot
from commands.db import conn, cursor
from commands.help import CONFIG
from user import BFGuser, BFGconst

CONFIG['help_game'] += '\n   🏛 Голд [ставка]'

games = {}


async def update_balance(user_id: int, amount: int, operation='subtract') -> None:
	balance = cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
	
	if operation == 'add':
		new_balance = Decimal(str(balance)) + Decimal(str(amount))
	else:
		new_balance = Decimal(str(balance)) - Decimal(str(amount))
	
	new_balance = "{:.0f}".format(new_balance)
	cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (str(new_balance), user_id))
	conn.commit()


class Game:
	def __init__(self, chat_id, user_id, summ):
		self.chat_id = chat_id
		self.user_id = user_id
		self.message_id = int()
		self.summ = summ
		self.grid = [random.choice([['💸', '🧨'], ['🧨', '💸']]) for _ in range(12)]
		self.player = [-1, -1]
		self.last_time = time.time()
	
	def get_pole(self, action: str, txt='') -> str:
		if action == 'game':
			grid = [['❓'] * 2 for _ in range(12)]
			
			for i in range(self.player[0] + 1):
				for j in range(2):
					if self.grid[i][j] == '💸':
						grid[i][j] = '💰'
		else:
			grid = self.grid
			if action == 'lose':
				grid[self.player[0]][self.player[1]] = '💥'
			else:
				grid[self.player[0]][self.player[1]] = '✅'
		
		last = 2 ** len(grid)
		
		for row in reversed(grid):
			summ = tr(self.summ * last, limit=6)
			txt += f"|{'|'.join(row)}| {summ}$ ({last}x)\n"
			last //= 2
		
		return txt
	
	def make_move(self, y: int) -> str | None:
		self.player = [self.player[0] + 1, y]
		position = self.grid[self.player[0]][self.player[1]]
		
		if position == '🧨':
			return 'lose'
		if self.player[0] == 11:
			return 'win'
		
	def get_x(self, x: int) -> int:
		return 2 * (2 ** x)
	
	async def stop_game(self) -> None:
		x = self.get_x(self.player[0])
		summ = Decimal(str(self.summ)) * Decimal(str(x))
		await update_balance(self.user_id, summ, operation='add')
	
	def get_text(self, action: str):
		txt = ''
		if action == 'win':
			txt += '🤑 {}, <b>ты успешно забрал приз!</b>'
		elif action == 'stop':
			txt += '❌ {}, <b> вы отменили игру!</b>'
		elif action == 'lose':
			txt += '💥 {}, <b> ты проиграл!\nВ следующий раз повезет!</b>'
		else:
			txt += '🤑 {}, <b>ты начал игру Золото Запада❗️</b>'
		
		pole = self.get_pole(action)
		
		txt += f'\n<code>·····················</code>\n💸 <b>Ставка:</b> {tr(self.summ, limit=6)}$'
		
		if action == 'game':
			next_win = self.get_x(self.player[0] + 1)
			next_summ = tr(int(self.summ * next_win), limit=6)
			
			txt += f'\n⚡️ <b>Сл. Ячейка:</b> x{next_win} / {next_summ}$'
		
		win = self.get_x(self.player[0])
		summ = tr(int(self.summ * win), limit=6)
			
		if action == 'win' or (action == 'game' and self.player[0] != -1):
			txt += f'\n📊 <b>Выигрыш:</b> x{win} / {summ}$'
		
		txt += '\n\n' + pole
		return txt
	
	def get_kb(self) -> InlineKeyboardMarkup:
		keyboard = InlineKeyboardMarkup(row_width=5)
		
		keyboard.add(
			InlineKeyboardButton('❓', callback_data=f"gold-tap_0|{self.user_id}"),
			InlineKeyboardButton('❓', callback_data=f"gold-tap_1|{self.user_id}"),
		)

		txt = 'Забрать выигрыш ✅' if self.player[0] != -1 else '❌ Отменить'
		keyboard.add(InlineKeyboardButton(txt, callback_data=f"gold-stop|{self.user_id}"))
		return keyboard


@antispam
async def start(message: types.Message, user: BFGuser):
	win, lose = BFGconst.emj()
	
	if user.user_id in games:
		await message.answer(f'{user.url}, у вас уже есть активная игра {lose}')
		return
	
	try:
		if message.text.lower().split()[1] in ['все', 'всё']:
			summ = int(user.balance)
		else:
			summ = message.text.split()[1].replace('е', 'e')
			summ = int(float(summ))
	except:
		await message.answer(f'{user.url}, вы не ввели ставку для игры {lose}')
		return
	
	if summ < 10:
		await message.answer(f'{user.url}, минимальная ставка - 10$ {lose}')
		return
	
	if summ > int(user.balance):
		await message.answer(f'{user.url}, у вас недостаточно денег {lose}')
		return
	
	game = Game(message.chat.id, user.user_id, summ)
	games[user.user_id] = game
	
	await update_balance(user.user_id, summ, operation='subtract')
	msg = await message.answer(game.get_text('game').format(user.url), reply_markup=game.get_kb())
	await new_earning_msg(msg.chat.id, msg.message_id)
	game.message_id = msg.message_id


@antispam_earning
async def game_kb(call: types.CallbackQuery, user: BFGuser):
	user_id = call.from_user.id
	chat_id = call.message.chat.id
	message_id = call.message.message_id
	game = games.get(user_id, None)
	
	if not game or game.chat_id != chat_id or game.message_id != message_id:
		await bot.answer_callback_query(call.id, '⚡️ Игра не найдена.')
		return
	
	x = int(call.data.split('_')[1].split('|')[0])
	result = game.make_move(x)
	
	if result == 'lose':
		await call.message.edit_text(game.get_text('lose').format(user.url))
		games.pop(user_id)
	elif result == 'win':
		await call.message.edit_text(game.get_text('win').format(user.url))
		await game.stop_game()
		games.pop(user_id)
	else:
		await call.message.edit_text(game.get_text('game').format(user.url), reply_markup=game.get_kb())


@antispam_earning
async def game_stop(call: types.CallbackQuery, user: BFGuser):
	user_id = call.from_user.id
	chat_id = call.message.chat.id
	message_id = call.message.message_id
	game = games.get(user_id, None)
	
	if not game or game.chat_id != chat_id or game.message_id != message_id:
		await bot.answer_callback_query(call.id, '⚡️ Игра не найдена.')
		return
	
	await game.stop_game()
	txt = 'stop' if game.player[0] == -1 else 'win'
	await call.message.edit_text(game.get_text(txt).format(user.url))
	games.pop(user_id)


async def check_game():
	while True:
		for user_id, game in list(games.items()):
			if int(time.time()) > int(game.last_time + 60):
				games.pop(user_id)
				try:
					await game.stop_game()
					txt = f'⚠️ <b>От вас давно не было активности!</b>\nИгра отменена! На ваш баланс возвращено {tr(game.summ)}$'
					await bot.send_message(game.chat_id, txt, reply_to_message_id=game.message_id)
				except:
					pass
		await asyncio.sleep(15)


loop = asyncio.get_event_loop()
loop.create_task(check_game())


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(start, lambda message: message.text.lower().startswith('голд'))
	dp.register_callback_query_handler(game_kb, text_startswith='gold-tap_')
	dp.register_callback_query_handler(game_stop, text_startswith='gold-stop')


MODULE_DESCRIPTION = {
	'name': '🏛 Голд',
	'description': 'Новая игра "голд"'
}