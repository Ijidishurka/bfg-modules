import sqlite3
from decimal import Decimal

from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from commands.main import event_manager

from assets.antispam import antispam, admin_only
from assets.transform import transform as trt
from assets.transform import transform_int as tr
from bot import bot
from commands.help import CONFIG
import config as cfg

from commands import db as gdb
from commands.db import conn as conngdb, cursor as cursorgdb

CONFIG['help_osn'] += '\n   👥 Реф'

games = {}


def settings_kb():
	keyboards = InlineKeyboardMarkup(row_width=1)
	keyboards.add(InlineKeyboardButton("✍️ Ввести значение", switch_inline_query_current_chat="referal-set-summ "))
	return keyboards


class Database:
	def __init__(self):
		self.conn = sqlite3.connect('modules/temp/referrals.db')
		self.cursor = self.conn.cursor()
		self.create_tables()
	
	def create_tables(self):
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER,
				ref INTEGER DEFAULT '0',
				balance TEXT DEFAULT '0'
			)''')
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS settings (
				summ TEXT
			)''')
		if not self.cursor.execute('SELECT summ FROM settings').fetchone():
			summ = 1_000_000_000_000_000
			self.cursor.execute('INSERT INTO settings (summ) VALUES (?)', (summ,))
		self.conn.commit()
	
	async def reg_user(self, user_id):
		ex = self.cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)).fetchone()
		if not ex:
			self.cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
			self.conn.commit()
	
	async def get_info(self, user_id):
		await self.reg_user(user_id)
		return self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
	
	async def get_summ(self):
		return self.cursor.execute('SELECT summ FROM settings').fetchone()[0]
	
	async def upd_summ(self, summ):
		summ = "{:.0f}".format(summ)
		self.cursor.execute('UPDATE settings SET summ = ?', (summ,))
		self.conn.commit()
		
	async def get_game_id(self, user_id):
		return cursorgdb.execute('SELECT game_id FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
	
	async def new_ref(self, user_id, summ):
		await self.reg_user(user_id)
		balance = cursorgdb.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
		rbalance = self.cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
		
		new_balance = Decimal(str(balance)) + Decimal(str(summ))
		new_rbalance = Decimal(str(rbalance)) + Decimal(str(summ))
		new_balance = "{:.0f}".format(new_balance)
		new_rbalance = "{:.0f}".format(new_rbalance)
		
		cursorgdb.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
		self.cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_rbalance, user_id))
		self.cursor.execute('UPDATE users SET ref = ref + 1 WHERE user_id = ?', (user_id,))
		conngdb.commit()
		self.conn.commit()
		

db = Database()


@admin_only(private=True)
async def settings(message: types.Message):
	user_id = message.from_user.id
	name = await gdb.url_name(user_id)
	summ = await db.get_summ()
	await message.answer(f'{name}, текущая награда за реферала - {tr(summ)}$', reply_markup=settings_kb())
	
	
@admin_only(private=True)
async def ref_new_summ(message: types.Message):
	user_id = message.from_user.id
	name = await gdb.url_name(user_id)
	
	try:
		summ = message.text.split()[2].replace('е', 'e')
		summ = int(float(summ))
	except:
		await message.answer(f'{name}, вы не ввели новую награду за реферала\nПример: @{cfg.bot_username} referal-set-summ 1e20')
		return
	
	await db.upd_summ(summ)
	await message.answer(f'{name}, установлена новая награда за реферала - {tr(summ)}$')
	

@antispam
async def ref(message: types.Message):
	user_id = message.from_user.id
	name = await gdb.url_name(user_id)
	summ = await db.get_summ()
	data = await db.get_info(user_id)
	game_id = await db.get_game_id(user_id)
	await message.answer(f'''https://t.me/{cfg.bot_username}?start=r{game_id}
<code>·······························</code>
{name}, твоя реферальная ссылка, можешь поделиться и получить {trt(summ)}$

👥 <i>Твои рефералы</i>
<b>• {data[1]} чел.</b>
✨ <i>Заработано с рефералов:</i>
<b>• {trt(data[2])}$</b>''')


async def on_start_event(event, *args):
	try:
		message = args[0]['message']
		user_id = message.from_user.id
		r_id = int(message.text.split('/start r')[1])
		summ = await db.get_summ()
		
		user = cursorgdb.execute('SELECT game_id FROM users WHERE user_id = ?', (user_id,)).fetchone()
		real_id = cursorgdb.execute('SELECT user_id FROM users WHERE game_id = ?', (r_id,)).fetchone()
		
		if user_id == r_id or not real_id or user:
			return
		
		await db.new_ref(real_id[0], summ)
		await bot.send_message(real_id[0], f'🥰 <b>Спасибо за приглашение!</b>\nНа ваш баланс зачислено {tr(summ)}$')
	except:
		pass


event_manager.subscribe('start_event', on_start_event)


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(settings, commands='refsetting')
	dp.register_message_handler(ref_new_summ, lambda message: message.text.lower().startswith(f'@{cfg.bot_username.lower()} referal-set-summ'))
	dp.register_message_handler(ref, lambda message: message.text.lower() == 'реф')


MODULE_DESCRIPTION = {
	'name': '👥 Реферальная система',
	'description': 'Реферальная система\nЕсть возможность настроить награду за реферала\nКоманда /refsetting'
}