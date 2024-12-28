import os
import sqlite3

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType

from assets.antispam import antispam, admin_only, antispam_earning
from assets.transform import transform_int as tr
from bot import bot
from commands.help import CONFIG

from user import BFGuser, BFGconst


class SetAvaState(StatesGroup):
	avatar = State()


CONFIG['help_osn'] += '\n   🖼 Аватарка'

if not os.path.exists('modules/temp/avatars'):
    os.makedirs('modules/temp/avatars')
	
	
def set_avatar(user_id, avatar) -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup()
	txt = '⚡️ Установить аватарку' if not avatar else '❌ Удалить аватарку'
	keyboards.add(InlineKeyboardButton(txt, callback_data=f"set-avatar|{user_id}"))
	return keyboards


def cancel() -> InlineKeyboardMarkup:
	keyboards = InlineKeyboardMarkup()
	keyboards.add(InlineKeyboardButton("❌ Отмена", callback_data=f"cancel-set-avatar"))
	return keyboards


def check_kb(user_id):
	keyboards = InlineKeyboardMarkup()
	keyboards.add(
		InlineKeyboardButton("👍", callback_data=f"set-adm-avatar_1|{user_id}"),
		InlineKeyboardButton("👎", callback_data=f"set-adm-avatar_0|{user_id}"),
	)
	return keyboards
	

class Database:
	def __init__(self):
		self.conn = sqlite3.connect('modules/temp/avatar.db')
		self.cursor = self.conn.cursor()
		self.create_tables()
	
	def create_tables(self) -> None:
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER,
				action INTEGER
			)''')
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS settings (
				chat INTEGER
			)''')
		
		rtop = self.cursor.execute('SELECT * FROM settings').fetchone()
		if not rtop:
			self.cursor.execute('INSERT INTO settings (chat) VALUES (?)', (0,))
		self.conn.commit()
	
	async def get_chat(self):
		return self.cursor.execute('SELECT chat FROM settings').fetchone()[0]
	
	async def upd_chat(self, chat_id):
		self.cursor.execute('UPDATE settings SET chat = ?', (chat_id,))
		self.conn.commit()
	
	async def get_avatar(self, user_id):
		check = self.cursor.execute('SELECT action FROM users WHERE user_id = ?', (user_id,)).fetchone()
		return check[0] if check else None
	
	async def new_photo(self, user_id):
		self.cursor.execute('INSERT INTO users (user_id, action) VALUES (?, ?)', (user_id, 0))
		self.conn.commit()
		
	async def callback_photo(self, user_id, action):
		if action == 1:
			self.cursor.execute('UPDATE users SET action = 1 WHERE user_id = ?', (user_id,))
		else:
			self.cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
		self.conn.commit()
		

db = Database()

	
@antispam
async def balance_cmd(message: types.Message, user: BFGuser):
	avatar = await db.get_avatar(user.id)
	
	txt = f'''👫 Ник: {user.name}
💰 Деньги: {user.balance.tr()}$
💴 Йены: {user.yen.tr()}¥
🏦 Банк: {user.bank.tr()}$
💽 Биткоины: {user.btc.tr()}🌐

{BFGconst.ads}'''
	
	if not avatar or avatar == 0:
		await message.answer(txt, disable_web_page_preview=True)
	else:
		try:
			with open(f'modules/temp/avatars/{user.id}.png', 'rb') as photo:
				await message.answer_photo(photo=photo, caption=txt)
		except Exception as e:
			await db.callback_photo(user.id, 0)
			print('Не удалось отправить аватарку - ', e)
			await message.answer(txt, disable_web_page_preview=True)


@antispam
async def avatarka_cmd(message: types.Message, user: BFGuser):
	avatar = await db.get_avatar(user.id)
	
	if avatar and avatar == 1:
		try:
			with open(f'modules/temp/avatars/{user.id}.png', 'rb') as photo:
				await message.answer_photo(photo=photo, caption=f'🖼 {user.url}, вот ваша аватарка.', reply_markup=set_avatar(user.id, avatar))
				return
		except Exception as e:
			await db.callback_photo(user.id, 0)
			print('Не удалось отправить аватарку - ', e)
	
	await message.answer(f'🖼 {user.url}, у вас нету аватарки :(', reply_markup=set_avatar(user.id, avatar))


async def set_avatar_kb(call: types.CallbackQuery, state: FSMContext):
	user_id = call.from_user.id
	data_id = int(call.data.split('|')[1])
	
	if user_id != data_id:
		return
	
	avatar = await db.get_avatar(user_id)
	
	if avatar:
		os.remove(f'modules/temp/avatars/{user_id}.png')
		await call.message.edit_caption('🗑 <b>Аватарка удалена!</b>')
	else:
		if avatar == 0:
			await call.message.edit_text('🔄 <b>Ваша аватарка проходит модерацию!</b>')
			return
		
		await call.message.edit_text('📥 Пришлите боту аватарку:', reply_markup=cancel())
		await SetAvaState.avatar.set()
	

async def cancel_avatar_kb(call: types.CallbackQuery, state: FSMContext):
	await state.finish()
	await call.message.delete()


async def catcher_photo_cmd(message: types.Message, state: FSMContext):
	user_id = message.from_user.id
	admin_chat = await db.get_chat()
	photo = message.photo[-1]
	file_path = f'modules/temp/avatars/{user_id}.png'
	
	await photo.download(destination_file=file_path)
	await state.finish()
	
	try:
		with open(file_path, 'rb') as photo:
			txt = f'🖼 Новая аватарка от <code>{user_id}</code>'
			await bot.send_photo(chat_id=admin_chat, photo=photo, caption=txt, reply_markup=check_kb(user_id))
		
		await db.new_photo(user_id)
	except:
		await message.answer("Невозможно проверить фотографию. Попробуйте позже...")
		return
	
	await message.answer("Аватарка отправлена на проверку.")


@admin_only()
async def set_admin_chat(message: types.Message):
	chat_id = message.chat.id
	await message.answer(f"✅ Установлен чат для проверки аватарок - {chat_id}")
	await db.upd_chat(chat_id)
	
	
async def set_avatar_admin_kb(call: types.CallbackQuery):
	action = int(call.data.split('_')[1].split('|')[0])
	user_id = int(call.data.split('|')[1])
	
	if action == 1:
		txt = f'✅ Аватарка для игрока <code>{user_id}</code> добавлена.'
	else:
		txt = f'❌ Аватарка для игрока <code>{user_id}</code> отклонена.'
		os.remove(f'modules/temp/avatars/{user_id}.png')
	
	await db.callback_photo(user_id, action)
	await call.message.edit_caption(caption=txt, reply_markup=None)
	

def register_handlers(dp: Dispatcher):
	dp.register_message_handler(avatarka_cmd, lambda message: message.text.lower() == 'ава')
	dp.register_message_handler(balance_cmd, lambda message: message.text in ['б', 'Б', 'Баланс', 'баланс'])
	dp.register_callback_query_handler(set_avatar_kb, text_startswith='set-avatar')
	dp.register_callback_query_handler(cancel_avatar_kb, text='cancel-set-avatar', state=SetAvaState.avatar)
	dp.register_message_handler(catcher_photo_cmd, content_types=ContentType.PHOTO, state=SetAvaState.avatar)
	dp.register_message_handler(set_admin_chat, commands='set_avatar_chat')
	dp.register_callback_query_handler(set_avatar_admin_kb, text_startswith='set-adm-avatar_')


MODULE_DESCRIPTION = {
	'name': '🖼 Аватар',
	'description': 'Система аватарок\nДобавлена команда "ава"\nДля настройки админ чата отправьте /set_avatar_chat в админ чат'
}