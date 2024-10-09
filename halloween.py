import asyncio
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from assets.transform import transform_int as tr
from decimal import Decimal
from assets.antispam import antispam
from datetime import datetime
from bot import bot
import time
import sqlite3
import random

from commands import db as gdb
from commands.db import conn as conngdb, cursor as cursorgdb

from commands.main import CONFIG as HELLO_CONFIG
from commands.help import CONFIG as HELP_CONFIG

atacktime = dict()


async def atack_time(id):
	utime = 60
	dnow = datetime.now()
	last = atacktime.get(id)

	if not last:
		atacktime[id] = dnow
		last = datetime.fromtimestamp(0)
	if last:
		delta_seconds = (dnow - last).total_seconds()
		sl = int(utime - delta_seconds)

		if sl > 0:
			left = sl
			return 1, left
		else:
			atacktime[id] = dnow
			return 0, 0


MONSTERS = [
	('ВІДЬМА', 500, 'https://img.freepik.com/premium-photo/scary-halloween-witch-with-pumpkin-smoke-dark-background_924727-4391.jpg'),
	('ОБОРОТЕНЬ', 350, 'https://img1.akspic.ru/crops/8/8/6/3/4/143688/143688-uzhas-art-illustracia-psovye-vampir-1920x1080.jpg'),
	('ЗЛАЯ ТЫКВА', 150, 'https://img.goodfon.ru/original/1920x1408/7/36/halloween-evil-pumpkins-bats-4911.jpg'),
	('ПРИЗРАК', 750, 'https://png.pngtree.com/thumb_back/fw800/background/20230611/pngtree-halloween-ghost-wallpaper-4k-5k-image_2927454.jpg'),
	('РУКА', 50, 'https://jump24.com.ua/content/images/15/480x480l50nn0/ruka-z-serialu-wednesday-uensdei-thing-rich-z-lateksu-sv2522-32770514615611.png'),
	('ПИРАТ', 222, 'https://www.nme.com/wp-content/uploads/2022/09/Sea-Of-Thieves.jpg')
	
]

MONSTER = {'name': '', 'hp': 0, 'time': 0, 'url': '', 'max_hp': 0}


class Database:
	def __init__(self):
		self.conn = sqlite3.connect('modules/temp/halloween.db')
		self.cursor = self.conn.cursor()
		self.create_tables()

	def create_tables(self):
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER,
				candies INTEGER DEFAULT '0',
				mask INTEGER DEFAULT '3',
				pumpkins INTEGER DEFAULT '0'
			)''')
		self.conn.commit()
		
	async def reg_user(self, user_id):
		ex = self.cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)).fetchone()
		if not ex:
			self.cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
			self.conn.commit()
			
	async def get_balance(self, user_id):
		await self.reg_user(user_id)
		return self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
	
	async def upd_candies(self, user_id, summ):
		await self.reg_user(user_id)
		self.cursor.execute('UPDATE users SET candies = candies + ? WHERE user_id = ?', (summ, user_id))
		self.conn.commit()
		
	async def upd_pumpkins(self, user_id, summ):
		await self.reg_user(user_id)
		self.cursor.execute('UPDATE users SET pumpkins = pumpkins + ? WHERE user_id = ?', (summ, user_id))
		self.conn.commit()
		
	async def upd_mask(self, user_id, summ):
		await self.reg_user(user_id)
		self.cursor.execute('UPDATE users SET mask = mask + ? WHERE user_id = ?', (summ, user_id))
		self.conn.commit()
		
	async def upd_money(self, user_id, summ):
		await self.reg_user(user_id)
		balance = cursorgdb.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
		new_balance = Decimal(str(balance)) + Decimal(str(summ))
		new_balance = "{:.0f}".format(new_balance)
		cursorgdb.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
		conngdb.commit()
		
	async def upd_ecoins(self, user_id, summ):
		await self.reg_user(user_id)
		cursorgdb.execute('UPDATE users SET ecoins = ecoins + ? WHERE user_id = ?', (summ, user_id))
		conngdb.commit()


def edit_halloween_message():
	HELLO_CONFIG['sticker_id'] = [
		'CAACAgIAAxkBAAEM6yhnAAEa69j7Y4Dk8dz_3nWvaHPDNkYAAssCAAJWnb0KT093_26cvR02BA',
		'CAACAgIAAxkBAAEM6ypnAAEbBN3gbp6Z1VogNIEIaI06VeIAAswAAzDUnRG4NAgyDgkxzDYE',
		'CAACAgIAAxkBAAEM6yxnAAEbaL52iMg8wNb-Wcws3OVZYv8AAhoAAw220hmJ4kTBILxkLzYE',
		'CAACAgIAAxkBAAEM6y5nAAEbap_g2uAS40mfo18ufDSB7KsAArcAAzDUnRGaP4Ps5KISTzYE',
		'CAACAgIAAxkBAAEM6zBnAAEbbpwDjXb_P-IdnsGMY-M9FdgAAlUAA8A2TxMidkHNKTnRTTYE'
	]
	
	HELLO_CONFIG['hello_text'] = HELLO_CONFIG['hello_text'].replace('🤖', '👻').replace('💙', '🎃')
	HELLO_CONFIG['hello_text2'] = HELLO_CONFIG['hello_text2'].replace('🚀', '😈')
	HELP_CONFIG['help_cmd'] = HELP_CONFIG['help_cmd'].replace('💬', '👽')
	HELP_CONFIG['help_game'] += '\n   👻 Джекпот'
	

def new_monster():
	global MONSTER
	monster = MONSTER['name']
	while True:
		new_monster = random.choice(MONSTERS)
		if monster != new_monster[0]:
			break
	
	ntime = int(time.time()) + 3600
	MONSTER	= {'name': new_monster[0], 'hp': new_monster[1], 'time': ntime, 'url': new_monster[2], 'max_hp': new_monster[1]}


db = Database()
new_monster()


def atack_kb():
	keyboards = InlineKeyboardMarkup(row_width=1)
	keyboards.add(InlineKeyboardButton("🔫 Атаковать", callback_data="event-monster-atack"))
	return keyboards


def format_time(seconds):
	seconds = seconds - int(time.time())
	
	def pluralize(value, singular, plural1, plural2):
		if value % 10 == 1 and value % 100 != 11:
			return f"{value} {singular}"
		elif 2 <= value % 10 <= 4 and (value % 100 < 10 or value % 100 >= 20):
			return f"{value} {plural1}"
		else:
			return f"{value} {plural2}"

	if seconds >= 60:
		minutes = seconds // 60
		return pluralize(minutes, "минута", "минуты", "минут")
	else:
		return pluralize(seconds, "секунда", "секунды", "секунд")
	
	
async def check_monster():
	if time.time() > MONSTER['time'] or MONSTER['hp'] <= 0:
		new_monster()
	

@antispam
async def bag(message: types.Message):
	user_id = message.from_user.id
	name = await gdb.url_name(user_id)
	data = await db.get_balance(user_id)
	await message.answer(f'{name}, в вашем мешочке:\n🍬 Конфеты: {data[1]}\n🎃 Тыквы: {data[3]}\n🎭 Маски: {data[2]}')
	

@antispam
async def monster(message: types.Message):
	await check_monster()
	txt = f'''<b>👻 Монстр {MONSTER['name']}</b>
❤️ Здоровье: {MONSTER['hp']}/{MONSTER['max_hp']}
⌛️ До смены монстра: {format_time(MONSTER['time'])}'''
	await bot.send_photo(message.chat.id, photo=MONSTER['url'], caption=txt, reply_markup=atack_kb())
	

async def atack(call: types.CallbackQuery):
	user_id = call.from_user.id
	name = await gdb.url_name(user_id)
	status, time = await atack_time(user_id)
	await check_monster()
	
	if status == 1:
		await bot.answer_callback_query(call.id, text=f'👻 Попробуйте снова через {time} секунд.')
		return
	
	txt = ''
	hp = random.randint(1, 3)
	MONSTER['hp'] = MONSTER['hp'] - hp
	
	await bot.answer_callback_query(call.id, text='')
	
	if MONSTER['hp'] <= 0:
		await call.message.answer(f'{name}, вы победили монстра!\nВаша награда: 3🎃')
		await db.upd_pumpkins(user_id, 3)
		new_monster()
	else:
		if random.randint(1, 3) == 1:
			candy = random.randint(1, 3)
			await db.upd_candies(user_id, candy)
			txt = f', +{candy}🍬'
			
		await call.message.answer(f'{name}, вы нанесли удар по монстру!\n-{hp}❤️{txt}')
		
		
@antispam
async def startle(message: types.Message):
	user_id = message.from_user.id
	name = await gdb.url_name(user_id)
	info = await db.get_balance(user_id)
	
	if info[2] <= 0:
		await message.answer(f'😢 {name}, у вас недостаточно масок для участия. Найдите или купите новые!')
		return
	
	if not message.reply_to_message:
		await message.answer(f'{name}, вы должны ответить на сообщение пользователя! 👻')
		return
	
	win_messages = [
		'🫨 БУ-ГА-ГА! Вас напугал игрок {}!',
		'😱 УХ ТЫ! {} выпрыгнул из-за угла и испугал вас!',
		'👻 ОЙ! {} произнес: "БУ!" и вы едва не упали от страха!',
		'😨 БУ-ГА-ГА! {} неожиданно появился рядом и заставил вас вздрогнуть!',
		'🤯 ВАУ! {} напугал вас до мурашек своим неожиданным появлением!',
		'🫣 О-О! {} выскочил из-за угла с криком и заставил вас трястись от страха!',
		'🫥 ХОП! {} неожиданно объявился и заставил вас вскрикнуть от неожиданности!',
		'😳 УЖАС! {} закричал "БУ!" и вы чуть не потеряли сознание!',
		'🤭 ХА-ХА! {} напугал вас до смерти! Удачно сыграно!'
	]
	
	lose_messages = [
		'😅 Упс! {} попытался вас напугать, но вы лишь усмехнулись!',
		'😏 Ой! {} кричал "БУ!", но это вызвало у вас только улыбку!',
		'😂 Попытка не удалась! {} испугал только самого себя!',
		'😆 Вы только посмеялись! {} пытался вас напугать, но его крики звучали слишком забавно!',
		'🤷‍♂️ Не получилось! {} так и не смог вас напугать, даже с криками "БУ!"',
		'🙈 Ха-ха! {} хотел вас напугать, но вы просто развернулись и ушли!',
		'😜 Ой, не так-то просто напугать вас! {} зря старался!',
		'🙃 Попытка не удалась! {} потратил много сил, но вы остались невозмутимы',
		'🤭 Зато это было весело! {} пытался вас напугать, но вы просто рассмеялись!',
	]
	
	if random.random() < 0.5:
		msg = random.choice(win_messages) + f'\n\n<i>Вы получили 1🎃</i>'
		await db.upd_pumpkins(user_id, 1)
	else:
		msg = random.choice(lose_messages)
	
	await message.answer(msg.format(name), reply=message.reply_to_message.message_id)
	await db.upd_mask(user_id, -1)
	
	
@antispam
async def shop(message: types.Message):
	user_id = message.from_user.id
	name = await gdb.url_name(user_id)
	await message.answer(f'''{name}, добро пожаловать в наш магазин:

Маски: 25🍬 - 1🎭
Деньги: 1🍬 - 1е5$

❗️ Для покупки введите:
Купить маску (кол-во)
Открыть конфеты (кол-во)''')


@antispam
async def buy(message: types.Message):
	user_id = message.from_user.id
	name = await gdb.url_name(user_id)
	info = await db.get_balance(user_id)
	
	try:
		summ = int(message.text.split()[2])
	except:
		return
	
	if summ <= 0:
		return
	
	if message.text.lower().startswith('купить'):
		summ2 = summ * 25
		if summ2 > info[1]:
			await message.answer(f'{name}, у вас недостаточно конфет 😳')
			return
		
		await db.upd_mask(user_id, summ)
		await db.upd_candies(user_id, (summ2*-1))
		await message.answer(f'{name}, вы успешно купили {summ}🎭 за {summ2}🍬')
	else:
		if summ > info[1]:
			await message.answer(f'{name}, у вас недостаточно конфет 😳')
			return
		
		summ2 = summ * 1000000
		await db.upd_candies(user_id, (summ*-1))
		await db.upd_money(user_id, summ2)
		await message.answer(f'{name}, вы успешно обменяли {summ}🍬 на {tr(summ2)}$ 👻')


@antispam
async def jackpot(message: types.Message):
	user_id = message.from_user.id
	name = await gdb.url_name(user_id)
	info = await db.get_balance(user_id)
	
	if info[3] <= 0:
	    await message.answer(f'{name}, у вас нету тыковок 👻')
	    return
	
	await db.upd_pumpkins(user_id, -1)
	
	rewards = {'💸': 0, '🍬': 0, '🎭': 0, '💳': 0}
	emoji_list = ['💸', '🍬', '🎭', '💳']
	emoji_weights = [70, 20, 8, 2]
	
	emojis = random.choices(emoji_list, weights=emoji_weights, k=3)
	
	for emj in emojis:
		if emj == '💸':
			rewards['💸'] += 1000000000000
		elif emj == '🍬':
			rewards['🍬'] += 50
		elif emj == '🎭':
			rewards['🎭'] += 3
		elif emj == '💳':
			rewards['💳'] += 1
	
	txt = ''
	if rewards['💸'] > 0:
		txt += f'\n+{tr(rewards["💸"])}$ 💰'
		await db.upd_money(user_id, rewards["💸"])
	if rewards['🍬'] > 0:
		txt += f'\n+{rewards["🍬"]}🍬'
		await db.upd_candies(user_id, rewards["🍬"])
	if rewards['🎭'] > 0:
		txt += f'\n+{rewards["🎭"]}🎭'
		await db.upd_mask(user_id, rewards["🎭"])
	if rewards['💳'] > 0:
		txt += f'\n+{rewards["💳"]}💳 B-coin'
		await db.upd_ecoins(user_id, rewards["💳"])
	
	msg = await message.reply(f"{name}, ❓|❓|❓")
	
	try:
		for i in range(0, 3):
			await asyncio.sleep(0.45)
			new_text = f'{name}, ' + '|'.join(emojis[:i + 1] + ['❓'] * (len(emojis) - (i + 1)))
			await msg.edit_text(new_text)
		
		await asyncio.sleep(0.8)
		await msg.edit_text(f"{name}, {'|'.join(emojis)}\n<i>{txt}</i>")
	except:
		await message.reply(f"{name}, {'|'.join(emojis)}\n<i>{txt}</i>")
	
	
@antispam
async def event(message: types.Message):
	await message.answer(f'''<b>Ивент Хэллоуин 🎃</b>
<i>Добро пожаловать на Хэллоуинское событие! Жуткие приключения ждут вас, и каждый участник сможет проявить себя в различных конкурсах и заданиях. Мы подготовили крутые призы, которые можно выиграть!</i>

<b>Основные задания:</b>

🎃 <b>Тыквенная Лотерея</b> (<code>Джекпот</code>)
Каждый может испытать удачу! В лотерее доступны случайные награды, такие как деньги, конфеты, B-coins 🎭. Не упустите шанс сорвать куш!

👹 <b>Победи монстра</b> (<code>Монстр</code>)
Встреться с монстрами и побеждай их, чтобы получить уникальные трофеи!

🍬 <b>Обмен конфет</b> (<code>Магазин</code>)
Собранные конфеты можно обменять на крутые призы в магазине. Чем больше конфет, тем ценнее награды!

👻 <b>Возможность пугать игроков</b> (<code>Напугать</code>)
Используйте страшные маски, чтобы пугать других игроков и зарабатывать дополнительные бонусы!''')


def register_handlers(dp: Dispatcher):
	dp.register_message_handler(bag, lambda message: message.text.lower() == 'мешок')
	dp.register_message_handler(monster, lambda message: message.text.lower() == 'монстр')
	dp.register_callback_query_handler(atack, text_startswith='event-monster-atack')
	dp.register_message_handler(startle, lambda message: message.text.lower() == 'напугать')
	dp.register_message_handler(shop, lambda message: message.text.lower() == 'магазин')
	dp.register_message_handler(buy, lambda message: message.text.lower().startswith(('купить маску', 'открыть конфеты')))
	dp.register_message_handler(jackpot, lambda message: message.text.lower() == 'джекпот')
	dp.register_message_handler(event, lambda message: message.text.lower() == 'хэллоуин')
	edit_halloween_message()


MODULE_DESCRIPTION = {
	'name': '👻 Halloween',
	'description': '''Ивент-модуль хэллоуин:
- Новое оформление
- Новый ивент "монстры"
- Новая игра
- Новые игровые валюты

* Модуль использует собственную базу данных
* Помощью по модулю введите "хеллоуин"'''
}