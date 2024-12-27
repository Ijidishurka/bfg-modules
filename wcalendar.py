import asyncio

from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from assets.transform import transform_int as tr
from assets.antispam import antispam, antispam_earning, new_earning
from datetime import datetime
import sqlite3

from commands.main import CONFIG as HELLO_CONFIG
from commands.help import CONFIG as HELP_CONFIG
from user import BFGuser

PRIZES = {
	1: ['balance', 1_000_000_000_000, '💰 Денег'],
	2: ['btc', 1_000_000_000, '🌐 Биткоинов'],
	3: ['energy', 30, '⚡️ Энергии'],
	4: ['balance', 5_000_000_000_000, '💰 Денег'],
	5: ['yen', 100_000_000, '💴 Йен'],
	6: ['matter', 300, '🌌 Материи'],
	7: ['palladium', 1, '⚗️ Палладиум'],
	8: ['balance', 5_000_000_000_000, '💰 Денег'],
	9: ['matter', 500, '🌌 Материи'],
	10: ['energy', 30, '⚡️ Энергии'],
	11: ['exp', 3000, '💡 Опыта'],
	12: ['balance', 100_000_000_000_000, '💰 Денег'],
	13: ['balance', 500_000_000_000_000, '💰 Денег'],
	14: ['ecoins', 20, '💳 B-coins'],
}


class Database:
	def __init__(self):
		self.conn = sqlite3.connect('modules/temp/winter_calendar.db')
		self.cursor = self.conn.cursor()
		self.create_tables()
	
	def create_tables(self) -> None:
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER,
				day INTEGER DEFAULT '0'
			)''')
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS info (
				day INTEGER
			)''')
		self.conn.commit()
		
		if not self.cursor.execute('SELECT * FROM info').fetchone():
			self.cursor.execute('INSERT INTO info (day) VALUES (?)', (1,))
			self.conn.commit()
			
	async def get_user_day(self, user_id) -> int:
		day = self.cursor.execute('SELECT day FROM users WHERE user_id = ?', (user_id,)).fetchone()
		if not day:
			self.cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
			self.conn.commit()
			return 0
		return day[0]
	
	async def prize_received(self, user_id) -> None:
		day = self.cursor.execute('SELECT day FROM info').fetchone()[0]
		self.cursor.execute('UPDATE users SET day = ? WHERE user_id = ?', (day, user_id))
		self.conn.commit()
		
	async def get_day(self) -> int:
		return self.cursor.execute('SELECT day FROM info').fetchone()[0]
	
	async def upd_day(self) -> None:
		self.cursor.execute('UPDATE info SET day = day + 1')
		self.conn.commit()


def edit_event_message():
	HELLO_CONFIG['sticker_id'] = [
		'CAACAgIAAxkBAAENUydnXbenashbCQpIjm2xRtZkAyywcgACZRQAAhMdSUryE1c7F5PylTYE',
		'CAACAgQAAxkBAAENZhtnbv18pHlf1XpB7gfY7K3-Luc_gQACvhAAAhihOFCGYokJ7qckjDYE',
		'CAACAgIAAxkBAAENZh1nbv4IOnvS3gABWYUI87luDn3kHgUAAncBAAIiN44EAAHKirUTyZWxNgQ',
	]
	
	HELLO_CONFIG['hello_text'] = HELLO_CONFIG['hello_text'].replace('🤖', '☃️').replace('💙', '🎄')
	HELLO_CONFIG['hello_text2'] = HELLO_CONFIG['hello_text2'].replace('🚀', '🎅')
	HELP_CONFIG['help_cmd'] = HELP_CONFIG['help_cmd'].replace('💬', '🎅')
	HELP_CONFIG['help_osn'] += '\n   🎁 Календарь'


db = Database()


def get_prize_kb() -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=1)
	keyboards.add(InlineKeyboardButton("🎁 Получить", callback_data="winter-event-get-prize"))
	return keyboards


@antispam
async def event_calendar_cmd(message: types.Message, user: BFGuser):
	day = await db.get_day()
	prize = PRIZES.get(day)
	
	if not prize:
		await message.answer(f'{user.url}, две недели подарков подошли к концу! Возвращайтесь в следующем году 🎅')
		return
	
	msg = await message.answer(f'{user.url}, сегодняшний подарок <b>({day}/14)</b>: {tr(prize[1])} {prize[2]}', reply_markup=get_prize_kb())
	await new_earning(msg)


@antispam_earning
async def event_calendar_call(call: types.CallbackQuery, user: BFGuser):
	day = await db.get_day()
	user_day = await db.get_user_day(user.user_id)
	prize = PRIZES.get(day)
	
	if user_day >= day or not prize:
		await call.answer(f'{user.name}, Вы уже забрали свой подарок! 🎅')
		return
	
	upd_list = {
		'balance': user.balance,
		'btc': user.btc,
		'energy': user.energy,
		'yen': user.yen,
		'matter': user.mine.matter,
		'palladium': user.mine.palladium,
		'exp': user.expe,
		'ecoins': user.bcoins,
	}
	
	await upd_list[prize[0]].upd(prize[1], '+')
	await call.answer(show_alert=True, text=f'{user.name}, Вы получили {tr(prize[1])} {prize[2]} 🎅')
	await db.prize_received(user.user_id)
	
	
async def check() -> None:
	while True:
		now = datetime.now()
		if now.hour == 22 and now.minute == 13:
			await db.upd_day()
			await asyncio.sleep(120)
		await asyncio.sleep(15)


loop = asyncio.get_event_loop()
loop.create_task(check())


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(event_calendar_cmd, lambda message: message.text.lower() == 'календарь')
	dp.register_callback_query_handler(event_calendar_call, text='winter-event-get-prize')
	edit_event_message()


MODULE_DESCRIPTION = {
	'name': '☃️ Winter calendar',
	'description': '''Ивент-модуль зима:
- Новое оформление
- Ивент календарь (команда "календарь")

* Модуль использует собственную базу данных"'''
}