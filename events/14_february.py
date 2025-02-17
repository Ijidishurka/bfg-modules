import asyncio
import random
import sqlite3
import time

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from commands.db import cursor
from assets.antispam import antispam, antispam_earning, new_earning
from assets.gettime import check_time
from commands.db import get_name
import config as cfg
from bot import bot

from user import BFGuser

VALENTINE_PHOTO = 'https://i.ibb.co/q3c9hfZM/photo-2025-02-17-14-17-28.jpg'

get_valentine_time = dict()
give_valentine_time = dict()
active_date = dict()
date_time = dict()


class ValentineState(StatesGroup):
    recipient_id = State()
    anonymous = State()
    message = State()
	
	
def select_mod(recipient_id: int) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=1)
	keyboards.add(
		InlineKeyboardButton('🥷 Инкогнито', callback_data=f'send-valentine_{recipient_id}_1'),
		InlineKeyboardButton('😍 Признаться открыто', callback_data=f'send-valentine_{recipient_id}_0'),
	)
	return keyboards


def valentine_menu(user_id: int) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=1)
	keyboards.add(
		InlineKeyboardButton('📊 Топ Валентинок', callback_data=f'valentine-top|{user_id}'),
		InlineKeyboardButton('💝 Мои Валентинки', callback_data=f'my-valentine_1|{user_id}'),
	)
	return keyboards


def mt_valentine_menu(user_id: int, page: int, data: int) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=3)
	keyboards.add(
		InlineKeyboardButton('‹', callback_data=f'my-valentine_{page-1}|{user_id}'),
		InlineKeyboardButton(f'{page}/{(data+4)//5}', callback_data='@BFGcopybot'),
		InlineKeyboardButton('›', callback_data=f'my-valentine_{page+1}|{user_id}'),
	)
	keyboards.row(InlineKeyboardButton('🔝 В начало', callback_data=f'my-valentine-menu|{user_id}'))
	return keyboards


def valentine_back(user_id: int) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup()
	keyboards.row(InlineKeyboardButton('🔙 Назад', callback_data=f'my-valentine-menu|{user_id}'))
	return keyboards


def invite_to_date(user_id: int, rid: int) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=2)
	keyboards.add(
		InlineKeyboardButton('✅ Да', callback_data=f'event-date_yes_{user_id}|{rid}'),
		InlineKeyboardButton('❌ Нет', callback_data=f'event-date_no_{user_id}|{rid}'),
	)
	return keyboards


async def check_user(game_id: int) -> int | None:
	return cursor.execute('SELECT user_id FROM users WHERE game_id = ?', (game_id,)).fetchone()


class Database:
	def __init__(self) -> None:
		self.conn = sqlite3.connect('modules/temp/14_february.db')
		self.cursor = self.conn.cursor()
		self.create_tables()
	
	def create_tables(self) -> None:
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER,
				valentine INTEGER DEFAULT '0',
				sent_valentines INTEGER DEFAULT '0',
				obtained_valentines INTEGER DEFAULT '0',
				lucky_dates INTEGER DEFAULT '0',
				unlucky_dates INTEGER DEFAULT '0'
		)''')
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS valentine (
				sender INTEGER,
				receiver INTEGER,
				anonymous INTEGER,
				message TEXT
		)''')
		
	async def register_user(self, user_id: int) -> None:
		if not self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone():
			self.cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
			self.conn.commit()
			
	async def get_info(self, user_id: int) -> tuple:
		await self.register_user(user_id)
		return self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
		
	async def issue_valentine(self, user_id: int, amount: int = 1) -> None:
		await self.register_user(user_id)
		self.cursor.execute('UPDATE users SET valentine = valentine + ? WHERE user_id = ?', (amount, user_id))
		self.conn.commit()
		
	async def new_valentine(self, user_id: int, recipient_id: int, anonymous: int, message: str) -> None:
		await self.register_user(recipient_id)
		self.cursor.execute('INSERT INTO valentine (sender, receiver, anonymous, message) VALUES (?, ?, ?, ?)', (user_id, recipient_id, anonymous, message))
		self.cursor.execute('UPDATE users SET obtained_valentines = obtained_valentines + 1 WHERE user_id = ?', (recipient_id,))
		self.cursor.execute('UPDATE users SET sent_valentines = sent_valentines + 1 WHERE user_id = ?', (user_id,))
		self.cursor.execute('UPDATE users SET valentine = valentine - 1 WHERE user_id = ?', (user_id,))
		self.conn.commit()
		
	async def get_user_valentine(self, user_id: int) -> list:
		return self.cursor.execute('SELECT * FROM valentine WHERE receiver = ?', (user_id,)).fetchall()
	
	async def get_top_valentine(self) -> list:
		return self.cursor.execute('SELECT user_id, obtained_valentines FROM users ORDER BY obtained_valentines LIMIT 10').fetchall()
	
	async def update_date_info(self, user_id: int, amount: int) -> None:
		if amount > 0:
			self.cursor.execute('UPDATE users SET lucky_dates = lucky_dates + 1 WHERE user_id = ?', (user_id,))
		else:
			self.cursor.execute('UPDATE users SET unlucky_dates = unlucky_dates + 1 WHERE user_id = ?', (user_id,))
		self.conn.commit()


db = Database()


@antispam
async def valentine_cmd(message: types.Message, user: BFGuser):
	await message.answer('''💘 <b>Добро пожаловать в мир романтики и сюрпризов!</b> 💘

✨ В честь <b>Дня Святого Валентина</b> мы подготовили для вас увлекательные события, мини-игры и возможность выразить свои чувства особенным образом.

❤️ <b>Что вас ждет?</b>

💌 <b>Подарить валентинку</b> – Сделайте день особенным для друга, отправив ему теплые слова!
📭 <b>Получить валентинку</b> – Бесплатно получайте <b>1 пустую валентинку</b> раз в <b>30 минут</b>.
📜 <b>Мой Валентин</b> – Просмотрите свою статистику: полученные и отправленные валентинки, а также итоги свиданий!
🏆 <b>Топ Валентинок</b> – Узнайте, кто получил больше всех валентинок и стал главным романтиком.
🎲 <b>Мини-игра "Свидание"</b> – Проверьте свою удачу! Играйте с друзьями, находите совпадения и зарабатывайте дополнительные пустые валентинки.
💖 <b>Пригласить на свидание</b> – Бросьте вызов другому игроку! Сможете ли вы удачно завершить свидание?

✨ <b>Дополнительная информация:</b>
🏹 <b>Получить валентинку</b> – Каждые <b>30 минут</b> можно бесплатно получить <b>1 пустую валентинку</b>.
💘 <b>Свидания</b> – Открывайте эмодзи в мини-игре, чтобы получить дополнительные валентинки!
⏳ <b>Ограничения:</b>
- Повторное приглашение на свидание – раз в <b>15 минут</b>.
- Отправка валентинок – раз в <b>10 минут</b>.

🌟 <b>Станьте самым романтичным игроком, отправляя и получая валентинки!</b> 💖''')


@antispam
async def get_valentine_cmd(message: types.Message, user: BFGuser):
	status, wtime = await check_time(get_valentine_time, user.id, 1800)
	
	if status == 1:
		await message.answer(f'⏳ Вы недавно получали бесплатную валентинку! Подождите ещё {wtime//60} мин.')
		return
	
	await db.issue_valentine(user.id)
	await message.answer('🎉 Вы получили 1 пустую валентинку! Используйте её, чтобы отправить другому игроку 💌')
	
	
@antispam
async def give_valentine_cmd(message: types.Message, user: BFGuser):
	data = await db.get_info(user.id)
	
	if message.chat.type != 'private':
		await message.answer('❓ Отправить валентинку можно только в личных сообщениях с ботом.')
		return
	
	if data[1] <= 0:
		await message.answer('📭 У вас нет пустых валентинок!\nЗаработайте их в мини-игре.')
		return
	
	try:
		game_id = int(message.text.split()[2])
	except:
		return
	
	recipient_id = await check_user(game_id)
	
	if not recipient_id:
		await message.answer('❌ Данного игрока не существует. Перепроверьте указанный <b>игровой ID</b>')
		return
	
	if user.id == recipient_id[0]:
		return
	
	last_time = give_valentine_time.get(user.id, 0)
	sl = int(600 - (int(time.time()) - last_time))
	
	if sl > 0:
		await message.answer(f'⏳ Вы недавно отправили валентинку! Подождите ещё {sl//60} мин.')
		return
	
	txt = '''💌 <b>Выберите режим отправки:</b>

🥷 <b>Инкогнито</b> — получатель не узнает, кто отправил.
😍 <b>Признаться открыто</b> — ваш ник будет указан.'''
	
	await message.answer(text=txt, reply_markup=select_mod(recipient_id[0]))


async def reset_state_timeout(chat_id: int, state: FSMContext) -> None:
	await asyncio.sleep(120)
	state_data = await state.get_state()
	
	if state_data == ValentineState.message.state:
		await state.finish()
		await bot.send_message(chat_id, "💘 <b>Время на отправку валентинки вышло</b>.")


async def enter_valentine_message_cmd(call: types.CallbackQuery, state: FSMContext):
	user_id = call.from_user.id
	recipient_id = int(call.data.split('_')[1])
	anonymous = int(call.data.split('_')[2])
	
	await call.message.delete()
	await call.message.answer('<b>💌 Введите текст валентинки (до 50 символов), у вас есть 2 минуты:</b>')
	
	await state.update_data(recipient_id=recipient_id, anonymous=anonymous)
	await ValentineState.message.set()

	asyncio.create_task(reset_state_timeout(user_id, state))
	
	
async def send_valentine_cmd(message: types.Message, state: FSMContext):
	user_id = message.from_user.id
	
	if len(message.text) > 50:
		await message.answer('🚫 Текст валентинки должен содержать не более 50 символов.\n\n🔄 Попробуйте снова:')
		return
	
	info = await db.get_info(user_id)
	data = await state.get_data()
	
	if info[1] <= 0:
		await message.answer('📭 У вас нет пустых валентинок!\nЗаработайте их в мини-игре.')
		return
	
	status, wtime = await check_time(give_valentine_time, user_id, 600)
	
	if status:
		await message.answer(f'⏳ Вы недавно отправили валентинку! Подождите ещё {wtime//60} мин.')
		return
	
	try:
		await bot.send_message(data['recipient_id'], f'💌 <b>Вы получили валентинку!</b>\n\n«{message.text}»')
	except:
		...
	
	await message.answer('✅ Вы успешно отправили валентинку!')
	await db.new_valentine(user_id, data['recipient_id'], data['anonymous'], message.text)
	await state.finish()
	
	
async def get_my_valentine_text(user_id: int) -> str:
	data = await db.get_info(user_id)
	text = f'''<b>💌 {cfg.bot_name} | День Святого Валентина</b>

🌟 <b>Получено Валентинок:</b> {data[3]}
📤 <b>Отправлено Валентинок:</b> {data[2]}
📭 <b>Пустые Валентинки:</b> {data[1]}

🎲 <b>Статистика свиданий:</b>
💞 <b>Всего:</b> {data[4] + data[5]}
✅ <b>Удачных:</b> {data[4]}
❌ <b>Неудачных:</b> {data[5]}

✨ Отправляйте валентинки друзьям и поднимитесь в топ!'''
	
	return text
	
	
@antispam
async def my_valentine_cmd(message: types.Message, user: BFGuser):
	text = await get_my_valentine_text(user.id)
	msg = await message.answer_photo(photo=VALENTINE_PHOTO, caption=text, reply_markup=valentine_menu(user.id))
	await new_earning(msg)
	
	
@antispam_earning
async def my_valentine_call(call: types.CallbackQuery, user: BFGuser):
	text = await get_my_valentine_text(user.id)
	await call.message.edit_caption(caption=text, reply_markup=valentine_menu(user.id))
	
	
@antispam_earning
async def my_valentine_list_cmd(call: types.CallbackQuery, user: BFGuser):
	page = int(call.data.split('_')[1].split('|')[0])
	user_valentine = await db.get_user_valentine(user.id)
	
	if page <= 0 or (len(user_valentine)+4)//5 < page:
		await call.answer('')
		return
	
	text = f'''<b>💝 Ваши валентинки\n\n🌟 Всего получено:</b> {len(user_valentine)}\n\n'''
	
	for i, data in enumerate(user_valentine[(5*page)-5:5*page], start=page*5-5):
		sender = 'Анонима 🥷' if data[2] == 1 else (await get_name(data[0]))
		text += f'{i+1}. <b>От {sender}</b>: «{data[3]}»\n'
	
	await call.message.edit_caption(text, reply_markup=mt_valentine_menu(user.id, page, len(user_valentine)))
	
	
async def get_top_message() -> str:
	data = await db.get_top_valentine()
	ranks = ["🥇", "🥈", "🥉"] + [f"{i}️⃣" for i in range(4, 11)]
	text = "👑 <b>Топ игроков по валентинкам</b>\n\n"
	
	for i, (user_id, valentines) in enumerate(data[::-1]):
		name = await get_name(user_id)
		text += f"{ranks[i]} {name} — {valentines} 💝\n"
	
	return text


@antispam_earning
async def top_valentine_call(call: types.CallbackQuery, user: BFGuser):
	text = await get_top_message()
	await call.message.edit_caption(caption=text, reply_markup=valentine_back(user.id))
	
	
@antispam
async def top_valentine_cmd(message: types.Message, user: BFGuser):
	text = await get_top_message()
	msg = await message.answer_photo(photo=VALENTINE_PHOTO, caption=text, reply_markup=valentine_back(user.id))
	await new_earning(msg)
	
	
@antispam
async def invite_to_date_cmd(message: types.Message, user: BFGuser):
	date, user_key = get_user_date(user.id)
	last_time = date_time.get(user.id, 0)
	sl = int(900 - (int(time.time()) - last_time))

	if date:
		await message.answer('😨 У вас уже идёт свидание.')
		return
	
	if sl > 0:
		await message.answer(f'⏳ Вы недавно приглашали на свидание! Подождите ещё {sl//60} мин.')
		return
	
	if not message.reply_to_message:
		await message.answer('🚫 Вы не указали игрока.\n\n✏️ ответьте на сообщение игрока, которого вы хотите пригласить на свидание.')
		return
	
	rid = message.reply_to_message.from_user.id
	
	if user.id == rid:
		return
	
	rname = await get_name(rid)
	text = f'💌 <b>{user.name}</b> приглашает <b>{rname}</b> на свидание!\n\nВы согласны?'
	
	msg = await message.answer(text=text, reply_markup=invite_to_date(user.id, rid))
	await new_earning(msg)
	
	
class Date:
	def __init__(self, uid, rid, name, rname) -> None:
		self.user1 = {'user_id': uid, 'name': name, 'move': None}
		self.user2 = {'user_id': rid, 'name': rname, 'move': None}
		self.key = random.randint(1, 9**9)
		self.move = random.choice([uid, rid])
		self.board = self.generate()
		
	def generate(self) -> list:
		emojis = ["🌹", "❤️", "💋"] * 3
		random.shuffle(emojis)
		return [emojis[i:i + 3] for i in range(0, 9, 3)]
	
	def make_move(self, user_id: int, move: tuple) -> int| None:
		user = self.user1 if self.user1['user_id'] == user_id else self.user2
		self.move = self.user1['user_id'] if self.move != self.user1['user_id'] else self.user2['user_id']
		user['move'] = move
		
		if self.user1['move'] and self.user2['move']:
			x1, y1 = self.user1['move'] if self.user1['move'] else (0, 0)
			x2, y2 = self.user2['move'] if self.user2['move'] else (1, 1)
			
			if self.board[x1][y1] == self.board[x2][y2]:
				return random.randint(1, 3)
			else:
				return -1
	
	def get_text(self, action=0) -> str:
		move_name = self.user1['name'] if self.user1['user_id'] == self.move else self.user2['name']
		
		text = f'''🎲 <b>Игра "Свидание"</b>

👤 <b>Игрок 1:</b> <code>{self.user1['name']}</code>
👤 <b>Игрок 2:</b> <code>{self.user2['name']}</code>'''
		
		if action:
			if action < 0:
				text += f'\n\n<b>😔 К сожалению, эмодзи не совпали. Попробуйте ещё раз!</b>'
			else:
				text += f'\n\n<b>🎉 Вы отлично сыграли! Оба игрока получили пустые валентинки ({action} шт.) 💝.</b>'
		else:
			text += f'\n\n🕹 <b>Ходит:</b> <code>{move_name}</code>\n\n💬 <i>Выберите ячейку:</i>'
		
		return text
	
	def get_keyboard(self, action=0) -> InlineKeyboardMarkup:
		keyboard = InlineKeyboardMarkup(row_width=3)
		for i in range(3):
			buttons = []
			for j in range(3):
				txt = self.board[i][j] if self.user1['move'] == (i, j) or self.user2['move'] == (i, j) else '⬜️'
				callback_data = f"date-event_{i}_{j}|{self.move}" if not action else "@BFGcopybot"
				buttons.append(InlineKeyboardButton(txt, callback_data=callback_data))
			keyboard.add(*buttons)
		return keyboard
	
	
def get_user_date(user_id: int) -> tuple | None:
	for user_key, date in active_date.items():
		if user_id in user_key:
			return date, user_key
	return None, None
	
	
@antispam_earning
async def start_date_cmd(call: types.CallbackQuery, user: BFGuser):
	rid = int(call.data.split('_')[2].split('|')[0])
	action = call.data.split('_')[1]
	
	if action == 'no':
		await call.message.edit_text('❌ Игрок отказался от свидания.')
		return
	
	rname = await get_name(rid)
	date = Date(user.id, rid, user.name, rname)
	active_date[(user.id, rid)] = date
	date_time[rid] = int(time.time())
	
	asyncio.create_task(reset_date_timeout(user.id, date.key))
	
	await call.message.delete()
	msg = await call.message.answer(text=date.get_text(), reply_markup=date.get_keyboard())
	await new_earning(msg)


@antispam_earning
async def process_date_cmd(call: types.CallbackQuery, user: BFGuser):
	x = int(call.data.split('_')[1])
	y = int(call.data.split('_')[2].split('|')[0])
	
	date, user_key = get_user_date(user.id)
	
	if not date:
		await call.message.delete()
		return
	
	auser = date.user1 if date.user1['user_id'] == user.id else date.user2
	
	if auser['move']:
		await call.answer('❌ Вы уже ходили.')
		return
	
	resulte = date.make_move(user.id, (x, y))
	await call.message.edit_text(text=date.get_text(resulte), reply_markup=date.get_keyboard(resulte))
	
	if resulte:
		del active_date[user_key]
		for user_id in [date.user1['user_id'], date.user2['user_id']]:
			await db.update_date_info(user_id, resulte)
			if resulte > 0:
				await db.issue_valentine(user_id, resulte)


async def reset_date_timeout(user_id: int, key: int) -> None:
	await asyncio.sleep(60)
	date, user_key = get_user_date(user_id)
	
	if date and date.key == key:
		del active_date[user_key]


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(valentine_cmd, lambda message: message.text.lower() == 'валентин')
	dp.register_message_handler(get_valentine_cmd, lambda message: message.text.lower() == 'получить валентинку')
	
	dp.register_message_handler(give_valentine_cmd, lambda message: message.text.lower().startswith('подарить валентинку'))
	dp.register_callback_query_handler(enter_valentine_message_cmd, text_startswith='send-valentine_')
	dp.register_message_handler(send_valentine_cmd, state=ValentineState.message)
	
	dp.register_message_handler(my_valentine_cmd, lambda message: message.text.lower() == 'мой валентин')
	dp.register_callback_query_handler(my_valentine_call, text_startswith='my-valentine-menu')

	dp.register_callback_query_handler(my_valentine_list_cmd, text_startswith='my-valentine')
	dp.register_callback_query_handler(top_valentine_call, text_startswith='valentine-top')
	dp.register_message_handler(top_valentine_cmd, lambda message: message.text.lower() == 'топ валентинок')
	
	dp.register_message_handler(invite_to_date_cmd, lambda message: message.text.lower() == 'пригласить на свидание')
	dp.register_callback_query_handler(start_date_cmd, text_startswith='event-date_')
	dp.register_callback_query_handler(process_date_cmd, text_startswith='date-event_')


MODULE_DESCRIPTION = {
	'name': '💘 Валентин',
	'description': 'Ивент на день святого Валентина (копия бфг)'
}
