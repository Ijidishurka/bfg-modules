import asyncio
import random
import time
from decimal import Decimal

from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from assets.antispam import antispam, new_earning_msg, antispam_earning
from assets.transform import transform as trt
from assets.transform import transform_int as tr
from bot import bot
from commands.db import conn, cursor, url_name, get_balance
from commands.help import CONFIG
from commands.main import win_luser

CONFIG['help_game'] += '\n   🐸 Квак [ставка]'

games = {}


async def update_balance(user_id, amount, operation='subtract'):
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
		self.message_id = 0
		self.summ = summ
		self.grid = [['🍀'] * 5 for _ in range(4)] + [['◾️', '◾️', '🐸', '◾️', '◾️']]
		self.place_traps()
		self.player = [4, 2]
		self.last_time = time.time()
	
	def place_traps(self):
		trap_counts = [4, 3, 2, 1]
		for row in range(4):
			positions = [i for i in range(5)]
			for _ in range(trap_counts[row]):
				pos = random.choice(positions)
				self.grid[row][pos] = '🌀'
				positions.remove(pos)
	
	def get_x(self, n):
		return {3: 1.23, 2: 2.05, 1: 5.11, 0: 25.96}.get(n, 1)
	
	def get_pole(self, stype, txt=''):
		if stype == 'game':
			grid = [['🍀'] * 5 for _ in range(4)] + [['◾️', '◾️', '🍀', '◾️', '◾️']]
			grid = [['🍀' if cell == '🐸️' else cell for cell in row] for row in grid]
			grid[self.player[0]][self.player[1]] = '🐸️'
		else:
			grid = self.grid
			if stype == 'lose':
				grid[self.player[0]][self.player[1]] = '🔵'
			
		multiplier = [25.96, 5.11, 2.05, 1.23, 1]
		for i, row in enumerate(grid):
			txt += f"<code>{'|'.join(row)}</code>| ({multiplier[i]}x)\n"
		
		return txt
	
	def make_move(self, x):
		self.grid[self.player[0]][self.player[1]] = '🍀'
		self.player = [self.player[0]-1, x]
		position = self.grid[self.player[0]][self.player[1]]
		self.grid[self.player[0]][self.player[1]] = '🐸️'
		
		if position == '🌀':
			return 'lose'
		if self.player[0] == 0:
			return 'win'
		
	async def stop_game(self):
		x = self.get_x(self.player[0])
		summ = Decimal(str(self.summ)) * Decimal(str(x))
		await update_balance(self.user_id, summ, operation='add')
			
	def get_text(self, stype):
		txt = ''
		if stype == 'win':
			txt += '🤑 {}, <b>ты успешно забрал приз!</b>'
		elif stype == 'stop':
			txt += '❌ {}, <b> вы отменили игру!</b>'
		elif stype == 'lose':
			txt += '💥 {}, <b> ты проиграл!\nВ следующий раз повезет!</b>'
		else:
			txt += '🐸 {}, <b>ты начал игру Frog Time!</b>'
			
		pole = self.get_pole(stype)
		next_win = self.get_x(self.player[0]-1)
		nsumm = trt(int(self.summ*next_win))
		
		txt += f'\n<code>·····················</code>\n💸 <b>Ставка:</b> {trt(self.summ)}$'
		
		if stype == 'game':
			txt += f'\n🍀 <b>Сл. кувшин:</b> х{next_win} / {nsumm}$'
			
		txt += '\n\n' + pole
		return txt
	
	def get_kb(self):
		keyboard = InlineKeyboardMarkup(row_width=5)
		buttons = []
		for i in range(5):
			buttons.append(InlineKeyboardButton('🍀', callback_data=f"kwak_{i}|{self.user_id}"))
		keyboard.add(*buttons)
		txt = '💰 Забрать' if self.player[0] != 4 else '❌ Отменить'
		keyboard.add(InlineKeyboardButton(txt, callback_data=f"kwak-stop|{self.user_id}"))
		return keyboard


@antispam
async def start(message: types.Message):
	user_id = message.from_user.id
	name = await url_name(user_id)
	balance = await get_balance(user_id)
	win, lose = await win_luser()
	
	if user_id in games:
		await message.answer(f'{name}, у вас уже есть активная игра {lose}')
		return
	
	try:
		if message.text.lower().split()[1] in ['все', 'всё']:
			summ = balance
		else:
			summ = message.text.split()[1].replace('е', 'e')
			summ = int(float(summ))
	except:
		await message.answer(f'{name}, вы не ввели ставку для игры {lose}')
		return
	
	if summ < 10:
		await message.answer(f'{name}, минимальная ставка - 10$ {lose}')
		return
	
	if summ > int(balance):
		await message.answer(f'{name}, у вас недостаточно денег {lose}')
		return
	
	game = Game(message.chat.id, user_id, summ)
	games[user_id] = game
	
	await update_balance(user_id, summ, operation='subtract')
	msg = await message.answer(game.get_text('game').format(name), reply_markup=game.get_kb())
	await new_earning_msg(msg.chat.id, msg.message_id)
	game.message_id = msg.message_id


@antispam_earning
async def game_kb(call: types.CallbackQuery):
	user_id = call.from_user.id
	chat_id = call.message.chat.id
	message_id = call.message.message_id
	game = games.get(user_id, None)
	name = await url_name(user_id)

	if not game or game.chat_id != chat_id or game.message_id != message_id:
		await bot.answer_callback_query(call.id, '🐸 Игра не найдена.')
		return
	
	x = int(call.data.split('_')[1].split('|')[0])
	result = game.make_move(x)

	if result == 'lose':
		await call.message.edit_text(game.get_text('lose').format(name))
		games.pop(user_id)
	elif result == 'win':
		await call.message.edit_text(game.get_text('win').format(name))
		games.pop(user_id)
	else:
		await call.message.edit_text(game.get_text('game').format(name), reply_markup=game.get_kb())


@antispam_earning
async def game_stop(call: types.CallbackQuery):
	user_id = call.from_user.id
	chat_id = call.message.chat.id
	message_id = call.message.message_id
	game = games.get(user_id, None)
	name = await url_name(user_id)
	
	if not game or game.chat_id != chat_id or game.message_id != message_id:
		await bot.answer_callback_query(call.id, '🐸 Игра не найдена.')
		return
	
	await game.stop_game()
	txt = 'stop' if game.player[0] == 4 else 'win'
	await call.message.edit_text(game.get_text(txt).format(name))
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
	dp.register_message_handler(start, lambda message: message.text.lower().startswith('квак'))
	dp.register_callback_query_handler(game_kb, text_startswith='kwak_')
	dp.register_callback_query_handler(game_stop, text_startswith='kwak-stop')


MODULE_DESCRIPTION = {
	'name': '🐸 Квак',
	'description': 'Новая игра "квак"'
}