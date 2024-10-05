from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from commands.db import conn, cursor, url_name, get_balance, reg_user
from assets.transform import transform_int as tr
from aiogram import types, Dispatcher
from assets.antispam import antispam
from decimal import Decimal
from bot import bot
import asyncio
import random
import time

from commands.help import CONFIG

CONFIG['help_game'] += '\n   🔘 Кн (ставка)'


games = []
waiting = {}


def creat_start_kb():
	keyboard = InlineKeyboardMarkup(row_width=1)
	keyboard.add(InlineKeyboardButton(text="🤯 Принять вызов", callback_data=f"tictactoe-start"))
	return keyboard


class Game:
	def __init__(self, chat_id, user_id, summ, message_id):
		self.chat_id = chat_id
		self.user_id = user_id
		self.chips = {}
		self.r_id = 0
		self.move = random.choice(['cross', 'zero'])
		self.message_id = message_id
		self.summ = summ
		self.board = [['  ' for _ in range(3)] for _ in range(3)]
		self.last_time = time.time()
	
	def start(self):
		self.last_time = time.time()
		players = [self.user_id, self.r_id]
		random.shuffle(players)
		self.chips['cross'] = players[0]
		self.chips['zero'] = players[1]
	
	def get_user_chips(self, user_id):
		if self.chips.get('cross') == user_id:
			return 'cross'
		else:
			return 'zero'
		
	async def accept_bet(self, user_id):
		balance = cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
		
		new_balance = Decimal(str(balance)) - Decimal(str(self.summ))
		new_balance = "{:.0f}".format(new_balance)
		
		cursor.execute(f'UPDATE users SET balance = ? WHERE user_id = ?', (str(new_balance), user_id))
		conn.commit()
	
	async def pay_money(self, user_id, summ):
		balance = cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
		
		new_balance = Decimal(str(balance)) + Decimal(str(summ))
		new_balance = "{:.0f}".format(new_balance)
		
		cursor.execute(f'UPDATE users SET balance = ? WHERE user_id = ?', (str(new_balance), user_id))
		conn.commit()
		
	def make_move(self, x, y, user_id):
		if self.board[x][y] != '  ':
			return "not empty"
		
		marker = self.get_user_chips(user_id)
		marker = '❌' if marker == 'cross' else '⭕️'
		
		self.last_time = time.time()
		self.board[x][y] = marker
		
		self.move = 'zero' if self.move == 'cross' else 'cross'
	
	def check_winner(self):
		win_combinations = [
			# горизонтали
			[(0, 0), (0, 1), (0, 2)],
			[(1, 0), (1, 1), (1, 2)],
			[(2, 0), (2, 1), (2, 2)],
			# вертикали
			[(0, 0), (1, 0), (2, 0)],
			[(0, 1), (1, 1), (2, 1)],
			[(0, 2), (1, 2), (2, 2)],
			# диагонали
			[(0, 0), (1, 1), (2, 2)],
			[(0, 2), (1, 1), (2, 0)]
		]
		
		for combo in win_combinations:
			symbols = [self.board[x][y] for x, y in combo]
			if symbols[0] != '  ' and symbols[0] == symbols[1] == symbols[2]:
				return symbols[0]
		
		if all(self.board[i][j] != '  ' for i in range(3) for j in range(3)):
			return 'draw'
		
		return None
	
	def get_kb(self):
		keyboard = InlineKeyboardMarkup(row_width=3)
		for i in range(3):
			buttons = []
			for j in range(3):
				buttons.append(
					InlineKeyboardButton(self.board[i][j], callback_data=f"TicTacToe_{i}_{j}"))
			keyboard.add(*buttons)
		return keyboard
	
		
def find_waiting(chat_id, message_id):
	for game in waiting.keys():
		if game.chat_id == chat_id and game.message_id == message_id:
			return game
	return None


def find_game_by_mid(chat_id, message_id):
	for game in games:
		if game.chat_id == chat_id and game.message_id == message_id:
			return game
	return None


def find_game_by_userid(user_id):
	for game in games:
		if game.user_id == user_id or game.r_id == user_id:
			return game
	return None


@antispam
async def start(message: types.Message):
	user_id = message.from_user.id
	name = await url_name(user_id)
	balance = await get_balance(user_id)
	
	if message.chat.type != 'supergroup':
		return
	
	if find_game_by_userid(user_id):
		await message.answer(f'{name}, у вас уже есть активная игра 😒')
		return
		
	try:
		summ = message.text.split()[1].replace('е', 'e')
		summ = int(float(summ))
	except:
		await message.answer(f'{name}, вы не ввели ставку дял игры 🫤')
		return
	
	if summ < 10:
		await message.answer(f'{name}, минимальная ставка - 10$ 😅')
		return
	
	if summ > int(balance):
		await message.answer(f'{name}, у вас недостаточно денег 😅')
		return
	
	msg = await message.answer(f"❌⭕️ {name} хочет сыграть в крестики-нолики\n💰 Ставка: {tr(summ)}$\n⏳ <i>Ожидаю противника в течении 3х минут</i>", reply_markup=creat_start_kb())
	game = Game(msg.chat.id, user_id, summ, msg.message_id)
	await game.accept_bet(user_id)
	waiting[game] = int(time.time()) + 180
	
	
async def start_game_kb(call: types.CallbackQuery):
	user_id = call.from_user.id
	await reg_user(user_id)
	balance = await get_balance(user_id)
	game = find_waiting(call.message.chat.id, call.message.message_id)
	
	if not game or user_id == game.user_id:
		return
	
	if balance < game.summ:
		await bot.answer_callback_query(call.id, text='❌ У вас недостаточно денег.')
		return
	
	games.append(game)
	waiting.pop(game)
	
	game.r_id = user_id
	game.start()
	
	cross = await url_name(game.chips['cross'])
	zero = await url_name(game.chips['zero'])
	
	crossp, zerop = ('ᅠ ', '👉') if game.move == 'zero' else ('👉', 'ᅠ ')
	
	text = f'''<b>Игра крестики-нолики</b>
💰 Ставка: {tr(game.summ)}$

{crossp}❌ {cross}
{zerop}⭕️ {zero}'''
	
	await call.message.edit_text(text, reply_markup=game.get_kb())
	await game.accept_bet(user_id)


async def game_kb(call: types.CallbackQuery):
	user_id = call.from_user.id
	await reg_user(user_id)
	game = find_game_by_mid(call.message.chat.id, call.message.message_id)
	
	if not game:
		return
	
	if game.r_id != user_id and game.user_id != user_id:
		await bot.answer_callback_query(call.id, '💩 Вы не можете нажать на эту кнопку.')
		return
	
	if game.get_user_chips(user_id) != game.move:
		await bot.answer_callback_query(call.id, text='❌ Не ваш ход.')
		return
	
	x = int(call.data.split('_')[1])
	y = int(call.data.split('_')[2])
	result = game.make_move(x, y, user_id)
	
	if result == 'not empty':
		await bot.answer_callback_query(call.id, text='❌ Эта клетка уже занята.')
		return
	
	cross = await url_name(game.chips['cross'])
	zero = await url_name(game.chips['zero'])
	
	crossp, zerop = ('ᅠ ', '👉') if game.move == 'zero' else ('👉', 'ᅠ ')
	
	text = f'''<b>Игра крестики-нолики</b>
💰 Ставка: {tr(game.summ)}$

{crossp}❌ {cross}
{zerop}⭕️ {zero}'''
	
	await call.message.edit_text(text, reply_markup=game.get_kb())
	
	result = game.check_winner()
	if result:
		if result == 'draw':
			await call.message.answer(f'🥸 У вас ничья!\n<i>Деньги возвращены.</i>', reply=game.message_id)
			await game.pay_money(game.user_id, game.summ)
			await game.pay_money(game.r_id, game.summ)
		else:
			move = 'zero' if result == '⭕️' else 'cross'
			win = game.chips[move]
			win_name = await url_name(win)
			await call.message.answer(f'🎊 {win_name} поздравляем с победой!\n<i>💰 Приз: {tr(game.summ*2)}$</i>', reply=game.message_id)
			await game.pay_money(win, (game.summ*2))
		
		games.remove(game)


async def check_waiting():
	while True:
		for game, gtime in list(waiting.items()):
			if int(time.time()) > gtime:
				waiting.pop(game)
				chat_id = game.chat_id
				message_id = game.message_id
				try:
					await bot.send_message(chat_id, f'❌ Не удалось найти противника.', reply_to_message_id=message_id)
					await game.pay_money(game.user_id, game.summ)
				except:
					pass
		await asyncio.sleep(30)
		
		
async def check_game():
	while True:
		for game in games:
			if int(time.time()) > int(game.last_time+60):
				games.remove(game)
				chat_id = game.chat_id
				message_id = game.message_id
				try:
					win = 'zero' if game.move == 'cross' else 'cross'
					win = game.chips[win]
					win_name = await url_name(win)
					await game.pay_money(win, (game.summ * 2))
					txt = f'⚠️ <b>От противника давно не было активности</b>\n{win_name} поздравляем с победой!\n<i>💰 Приз: {tr(game.summ*2)}$</i>'
					await bot.send_message(chat_id, txt, reply_to_message_id=message_id)
					await game.pay_money(game.user_id, game.summ)
				except:
					pass
		await asyncio.sleep(30)


loop = asyncio.get_event_loop()
loop.create_task(check_waiting())
loop.create_task(check_game())


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(start, lambda message: message.text.lower().startswith('кн'))
	dp.register_callback_query_handler(start_game_kb, text_startswith='tictactoe-start')
	dp.register_callback_query_handler(game_kb, text_startswith='TicTacToe')
	

MODULE_DESCRIPTION = {
	'name': '❌⭕️ Крестики-нолики',
	'description': 'Новая игра "крестики-нолики" против других игроков (на деньги)'
}