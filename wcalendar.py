import asyncio

from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from assets.transform import transform_int as tr
from assets.antispam import antispam, antispam_earning, new_earning, admin_only
from datetime import datetime
import sqlite3

from commands.main import CONFIG as HELLO_CONFIG
from commands.help import CONFIG as HELP_CONFIG
from user import BFGuser


class SetSummState(StatesGroup):
	day = State()
	column = State()
	summ = State()
	

DEFOULT_PRIZES = {
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

PRIZES_CONFIG = {
	'balance': '💰 Денег',
	'btc': '🌐 Биткоинов',
	'energy': '⚡️ Энергии',
	'yen': '💴 Йен',
	'exp': '💡 Опыта',
	'ecoins': '💳 B-coins',
	'case1': '📦 Обычный кейс',
	'case2': '🏵 Золотой кейс',
	'case3': '🏺 Рудный кейс',
	'case4': '🌌 Материальный кейс',
	'rating': '👑 Рейтинга',
	'corn': '🥜 Зёрна',
	'biores': '☣️ Биоресурсов',
	'titanium': '⚙️ Титана',
	'palladium': '⚗️ Палладий',
	'matter': '🌌 Материи',
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
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS prize (
				day INTEGER,
				column TEXT,
				summ INTEGER,
				info TEXT
			)''')
		self.conn.commit()
		
		if not self.cursor.execute('SELECT * FROM info').fetchone():
			self.cursor.execute('INSERT INTO info (day) VALUES (?)', (1,))
			self.conn.commit()
			
		self.creat_prizes_list()
		
	def creat_prizes_list(self) -> None:
		if not self.cursor.execute('SELECT * FROM prize').fetchone():
			for day, i in DEFOULT_PRIZES.items():
				self.cursor.execute('INSERT INTO prize (day, column, summ, info) VALUES (?, ?, ?, ?)', (day, i[0], i[1], i[2]))
			self.conn.commit()
			
	async def upd_prize(self, day, column, summ) -> None:
		info = PRIZES_CONFIG[column]
		self.cursor.execute('UPDATE prize SET column = ?, summ = ?, info = ? WHERE day = ?', (column, summ, info, day))
		self.conn.commit()
			
	async def get_prizes(self) -> dict:
		data = self.cursor.execute('SELECT * FROM prize').fetchall()
		return {item[0]: list(item[1:]) for item in data}

	async def get_day(self) -> int:
		return self.cursor.execute('SELECT day FROM info').fetchone()[0]

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


def info_prizes_kb(data, lday, user_id) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=1)
	
	for day, i in data.items():
		txt = '📍 |' if day == lday else ''
		keyboards.add(InlineKeyboardButton(f"{txt} {tr(i[1])} {i[2]}", callback_data=f"winter-edit-prize_{day}|{user_id}"))
	return keyboards


def edit_prizes_kb(day) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=3)
	buttons = []
	
	for key, item in PRIZES_CONFIG.items():
		buttons.append(InlineKeyboardButton(item, callback_data=f"winter-set-prize_{day}_{key}"))
		
	keyboards.add(*buttons)
	keyboards.add(InlineKeyboardButton("❌ Отмена", callback_data="winter-dell"))
	return keyboards


@antispam
async def event_calendar_cmd(message: types.Message, user: BFGuser):
	day = await db.get_day()
	prize = await db.get_prizes()
	prize = prize.get(day)
	
	if not prize:
		await message.answer(f'{user.url}, две недели подарков подошли к концу! Возвращайтесь в следующем году 🎅')
		return
	
	msg = await message.answer(f'{user.url}, сегодняшний подарок <b>({day}/14)</b>: {tr(prize[1])} {prize[2]}', reply_markup=get_prize_kb())
	await new_earning(msg)


@antispam_earning
async def event_calendar_call(call: types.CallbackQuery, user: BFGuser):
	day = await db.get_day()
	user_day = await db.get_user_day(user.user_id)
	prize = await db.get_prizes()
	prize = prize.get(day)

	if user_day >= day or not prize:
		await call.answer(f'{user.name}, Вы уже забрали свой подарок! 🎅')
		return

	upd_list = {
		'balance': user.balance,
		'btc': user.btc,
		'energy': user.energy,
		'yen': user.yen,
		'exp': user.expe,
		'ecoins': user.bcoins,
		'case1': user.case[1],
		'case2': user.case[2],
		'case3': user.case[3],
		'case4': user.case[4],
		'rating': user.rating,
		'corn': user.corn,
		'biores': user.biores,
		'titanium': user.mine.titanium,
		'palladium': user.mine.palladium,
		'matter': user.mine.matter,
	}

	await upd_list[prize[0]].upd(prize[1], '+')
	await call.answer(show_alert=True, text=f'{user.name}, Вы получили {tr(prize[1])} {prize[2]} 🎅')
	await db.prize_received(user.user_id)


@antispam
@admin_only(private=True)
async def edit_prizes_cmd(message: types.Message, user: BFGuser):
	day = await db.get_day()
	prize = await db.get_prizes()
	
	await message.answer('🎅 <b>ХО-ХО-ХО! Новогодняя доставка! Получите и распишитесь:</b>', reply_markup=info_prizes_kb(prize, day, user.user_id))
	
	
async def edit_prize_kb(call: types.CallbackQuery):
	day = int(call.data.split('_')[1].split('|')[0])
	await call.message.edit_text(f'🎅 Выберите новую награду для дня <b>#{day}</b>:', reply_markup=edit_prizes_kb(day))
	
	
async def edit_summ_kb(call: types.CallbackQuery, state: FSMContext):
	day = int(call.data.split('_')[1])
	prize = call.data.split('_')[2].split('|')[0]
	await call.message.edit_text(f'🎅 Введите сумму для дня <b>#{day} ({PRIZES_CONFIG[prize]})</b>:\n\n<i>Для отмены введите "-"</i>')
	await state.update_data(column=prize, day=day)
	await SetSummState.summ.set()
	
	
async def dell_message_kb(call: types.CallbackQuery):
	try:
		await call.message.delete()
	except Exception as e:
		print(e)
		
		
async def set_summ_cmd(message: types.Message, state: FSMContext):
	if message.text == '-':
		await state.finish()
		await message.answer('Отменено.')
		return
	
	try:
		summ = int(message.text)
	except:
		await message.answer('Введите целое число.')
		return
	
	if summ <= 0:
		await message.answer('Ты серьёзно?')
		return
	
	data = await state.get_data()
	await db.upd_prize(data['day'], data['column'], summ)
	
	txt = PRIZES_CONFIG[data['column']]
	await message.answer(f'🎅 Установленна новая награда на <b>#{data["day"]}</b> день: <code>{tr(summ)} {txt}</code>')
	await state.finish()


async def check() -> None:
	while True:
		now = datetime.now()
		if now.hour == 00 and now.minute == 00:
			await db.upd_day()
			await asyncio.sleep(120)
		await asyncio.sleep(15)


loop = asyncio.get_event_loop()
loop.create_task(check())


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(event_calendar_cmd, lambda message: message.text.lower() == 'календарь')
	dp.register_callback_query_handler(event_calendar_call, text='winter-event-get-prize')
	dp.register_message_handler(edit_prizes_cmd, commands='wcalendar')
	dp.register_callback_query_handler(edit_prize_kb, text_startswith='winter-edit-prize_')
	dp.register_callback_query_handler(edit_summ_kb, text_startswith='winter-set-prize_')
	dp.register_callback_query_handler(dell_message_kb, text_startswith='winter-dell')
	dp.register_message_handler(set_summ_cmd, state=SetSummState.summ)
	edit_event_message()


MODULE_DESCRIPTION = {
	'name': '☃️ Winter calendar',
	'description': '''Ивент-модуль зима:
- Новое оформление
- Ивент календарь (команда "календарь")

* Модуль использует собственную базу данных"
* Для настройки наград введите /wcalendar (лс)'''
}