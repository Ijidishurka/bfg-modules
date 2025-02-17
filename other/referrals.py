import sqlite3
from decimal import Decimal

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from assets.classes import CastomEvent

from assets.antispam import antispam, admin_only, antispam_earning
from assets.transform import transform_int as tr
from bot import bot
from commands.help import CONFIG
import config as cfg

from commands.db import cursor as cursorgdb
from user import BFGuser
import assets.kb


class SetRefSummState(StatesGroup):
	column = State()
	summ = State()
	

CONFIG['help_osn'] += '\n   👥 Реф'

CONFIG_VALUES = {
    'balance': ['user.balance', '$', ['', '', ''], '💰 Деньги'],
    'energy': ['user.energy', '⚡️', ['энергия', 'энергии', 'энергий'], '⚡️ Энергия'],
    'yen': ['user.yen', '💴', ['йена', 'йены', 'йен'], '💴 Йены'],
    'exp': ['user.exp', '💡', ['опыт', 'опыта', 'опытов'], '💡 Опыт'],
    'ecoins': ['user.bcoins', '💳', ['B-coin', 'B-coins', 'B-coins'], '💳 B-coins'],
    'corn': ['user.corn', '🥜', ['зерно', 'зерна', 'зёрен'], '🥜 Зерна'],
    'biores': ['user.biores', '☣️', ['биоресурс', 'биоресурса', 'биоресурсов'], '☣️ Биоресурсы'],
    'matter': ['user.mine.matter', '🌌', ['материя', 'материи', 'материй'], '🌌 Материя'],
}

original_kb = assets.kb.top


def get_form(number: int, forms: list[str]) -> str:
	number = abs(int(number)) % 100
	if 11 <= number <= 19:
		return forms[2]
	last_digit = number % 10
	if last_digit == 1:
		return forms[0]
	if 2 <= last_digit <= 4:
		return forms[1]
	return forms[2]


def freward(key: str, amount: int) -> str:
	config = CONFIG_VALUES[key]
	symbol, forms = config[1], config[2]
	word_form = get_form(amount, forms)
	return f"{tr(amount)}{symbol} {word_form}"


def settings_kb(top) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=1)
	txt = '➕ Добавить топ рефаводов' if top == 0 else '❌ Удалить топ рефаводов'
	keyboards.add(InlineKeyboardButton("✍️ Изменить награду", callback_data='ref-edit-prize'))
	keyboards.add(InlineKeyboardButton(txt, callback_data='ref-edit-top'))
	return keyboards


def select_values() -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=3)
	buttons = []
	
	for key, value in CONFIG_VALUES.items():
		buttons.append(InlineKeyboardButton(value[3], callback_data=f'ref-set-prize_{key}'))
	
	keyboards.add(*buttons)
	keyboards.add(InlineKeyboardButton("❌ Закрыть", callback_data='ref-dell'))
	return keyboards


def top_substitution_kb(user_id, tab) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup(row_width=2)
	buttons = [
		InlineKeyboardButton("👑 Топ рейтинга", callback_data=f"top-rating|{user_id}|{tab}"),
		InlineKeyboardButton("💰 Топ денег", callback_data=f"top-balance|{user_id}|{tab}"),
		InlineKeyboardButton("🧰 Топ ферм", callback_data=f"top-cards|{user_id}|{tab}"),
		InlineKeyboardButton("🗄 Топ бизнесов", callback_data=f"top-bsterritory|{user_id}|{tab}"),
		InlineKeyboardButton("🏆 Топ опыта", callback_data=f"top-exp|{user_id}|{tab}"),
		InlineKeyboardButton("💴 Топ йен", callback_data=f"top-yen|{user_id}|{tab}"),
		InlineKeyboardButton("📦 Топ обычных кейсов", callback_data=f"top-case1|{user_id}|{tab}"),
		InlineKeyboardButton("🏵 Топ золотых кейсов", callback_data=f"top-case2|{user_id}|{tab}"),
		InlineKeyboardButton("🏺 Топ рудных кейсов", callback_data=f"top-case3|{user_id}|{tab}"),
		InlineKeyboardButton("🌌 Топ материальных кейсов", callback_data=f"top-case4|{user_id}|{tab}"),
		InlineKeyboardButton("👥 Топ рефаводов", callback_data=f"ref-top|{user_id}|{tab}"),
	]
	
	keyboards.add(*buttons)
	return keyboards


def upd_keyboards(rtop: int) -> None:
	if rtop == 0:
		assets.kb.top = original_kb
	else:
		assets.kb.top = top_substitution_kb


class Database:
	def __init__(self):
		self.conn = sqlite3.connect('modules/temp/referrals.db')
		self.cursor = self.conn.cursor()
		self.create_tables()
	
	def create_tables(self) -> None:
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER,
				ref INTEGER DEFAULT '0',
				balance TEXT DEFAULT '0'
			)''')
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS settings (
				summ TEXT,
				column TEXT,
				rtop INTEGER DEFAULT '1'
			)''')
		
		rtop = self.cursor.execute('SELECT rtop FROM settings').fetchone()
		if not rtop:
			summ = 1_000_000_000_000_000
			self.cursor.execute('INSERT INTO settings (summ, column) VALUES (?, ?)', (summ, 'balance'))
			rtop = 1
		else:
			rtop = rtop[0]
		self.conn.commit()
		
		upd_keyboards(rtop)
		
	async def upd_settings(self, summ, column):
		self.cursor.execute('UPDATE settings SET summ = ?, column = ?', (summ, column))
		self.cursor.execute('UPDATE users SET balance = 0')
		self.conn.commit()
		
	async def upd_rtop(self, rtop):
		self.cursor.execute('UPDATE settings SET rtop = ?', (rtop,))
		self.conn.commit()
		
	async def get_rtop(self) -> int:
		return self.cursor.execute('SELECT rtop FROM settings').fetchone()[0]
	
	async def reg_user(self, user_id) -> None:
		ex = self.cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)).fetchone()
		if not ex:
			self.cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
			self.conn.commit()
	
	async def get_info(self, user_id) -> tuple:
		await self.reg_user(user_id)
		return self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
	
	async def get_summ(self) -> tuple:
		return self.cursor.execute('SELECT summ, column FROM settings').fetchone()
	
	async def upd_summ(self, summ) -> None:
		summ = "{:.0f}".format(summ)
		self.cursor.execute('UPDATE settings SET summ = ?', (summ,))
		self.conn.commit()
		
	async def new_ref(self, user_id, summ) -> None:
		await self.reg_user(user_id)
		rbalance = self.cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
		
		new_rbalance = Decimal(str(rbalance)) + Decimal(str(summ))
		new_rbalance = "{:.0f}".format(new_rbalance)
		
		self.cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_rbalance, user_id))
		self.cursor.execute('UPDATE users SET ref = ref + 1 WHERE user_id = ?', (user_id,))
		self.conn.commit()
		
	async def get_top(self) -> list:
		data = self.cursor.execute('SELECT user_id, ref FROM users ORDER BY ref DESC LIMIT 10').fetchall()
		users = []
		
		for user_id, ref in data:
			name = cursorgdb.execute("SELECT name FROM users WHERE user_id = ?", (user_id,)).fetchone()
			if name:
				users.append((user_id, ref, name[0]))
		return users
		

db = Database()
	

@antispam
async def ref(message: types.Message, user: BFGuser):
	summ, column = await db.get_summ()
	data = await db.get_info(user.id)
	await message.answer(f'''https://t.me/{cfg.bot_username}?start=r{user.game_id}
<code>·······························</code>
{user.url}, твоя реферальная ссылка, можешь поделиться и получить {freward(column, summ)}

👥 <i>Твои рефералы</i>
<b>• {data[1]} чел.</b>
✨ <i>Заработано с рефералов:</i>
<b>• {freward(column, data[2])}</b>''')


async def on_start_event(event, *args):
	try:
		message = args[0]['message']
		user_id = message.from_user.id
		r_id = int(message.text.split('/start r')[1])
		summ, column = await db.get_summ()
		
		user = cursorgdb.execute('SELECT game_id FROM users WHERE user_id = ?', (user_id,)).fetchone()
		real_id = cursorgdb.execute('SELECT user_id FROM users WHERE game_id = ?', (r_id,)).fetchone()
		
		if user_id == r_id or not real_id or user:
			return
		
		user = BFGuser(not_class=real_id[0])
		await user.update()
		
		await eval(CONFIG_VALUES[column][0]).upd(summ, '+')
		await db.new_ref(real_id[0], summ)
		
		await bot.send_message(real_id[0], f'🥰 <b>Спасибо за приглашение!</b>\nНа ваш баланс зачислено {freward(column, summ)}')
	except Exception as e:
		print('ref error: ', e)
	

@antispam
@admin_only(private=True)
async def settings_cmd(message: types.Message, user: BFGuser):
	summ, column = await db.get_summ()
	top = await db.get_rtop()
	await message.answer(f'{user.url}, текущая награда за реферала - {freward(column, summ)}', reply_markup=settings_kb(top))
	
	
async def dell_message_kb(call: types.CallbackQuery):
	try:
		await call.message.delete()
	except Exception as e:
		print(e)
		
		
async def select_prize_kb(call: types.CallbackQuery):
	await call.message.edit_text('👥 <b>Выберите валюту для награды:</b>', reply_markup=select_values())
	

async def edit_prize_kb(call: types.CallbackQuery, state: FSMContext):
	prize = call.data.split('_')[1]
	await call.message.edit_text(f'👥 Введите сумму награды ({CONFIG_VALUES[prize][3]}):\n\n<i>Для отмены введите "-"</i>')
	await state.update_data(column=prize)
	await SetRefSummState.summ.set()
	
	
async def enter_summ_cmd(message: types.Message, state: FSMContext):
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
	await db.upd_settings(summ, data['column'])
	
	await state.finish()
	await message.answer(f'✅ Установлена новая награда за реферала: {freward(data["column"], summ)}')
	
	
async def edit_top_kb(call: types.CallbackQuery):
	top = await db.get_rtop()
	new_top = 1 if top == 0 else 0
	upd_keyboards(new_top)
	await db.upd_rtop(new_top)
	await call.message.edit_reply_markup(settings_kb(new_top))


@antispam_earning
async def ref_top_kb(call: types.CallbackQuery, user: BFGuser):
	top = await db.get_top()
	tab = call.data.split('|')[2]
	
	if tab == 'ref':
		return
	
	top_message = f"{user.url}, топ 10 игроков бота по рефералам:\n"
	emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "1️⃣0️⃣"]
	
	for i, player in enumerate(top[:10], start=1):
		emj = emojis[i - 1]
		top_message += f"{emj} {player[2]} — {player[1]}👥\n"
	
	await call.message.edit_text(text=top_message, reply_markup=assets.kb.top(user.id, 'ref'), disable_web_page_preview=True)


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(ref, lambda message: message.text.lower() in ['реф', '/ref'])
	dp.register_message_handler(settings_cmd, commands='refsetting')
	dp.register_callback_query_handler(dell_message_kb, text='ref-dell')
	dp.register_callback_query_handler(select_prize_kb, text='ref-edit-prize')
	dp.register_callback_query_handler(edit_prize_kb, text_startswith='ref-set-prize_')
	dp.register_message_handler(enter_summ_cmd, state=SetRefSummState.summ)
	dp.register_callback_query_handler(edit_top_kb, text_startswith='ref-edit-top')
	dp.register_callback_query_handler(ref_top_kb, text_startswith='ref-top')
	CastomEvent.subscribe('start_event', on_start_event)


MODULE_DESCRIPTION = {
	'name': '👥 Реферальная система',
	'description': 'Реферальная система\nЕсть возможность настроить награду за реферала\nКоманда /refsetting'
}