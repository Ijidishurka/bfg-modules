import asyncio
import random
from bot import bot
from aiogram import types, Dispatcher
from commands.db import conn, cursor, url_name, get_balance
from commands.games.db import gametime
from commands.main import win_luser
from assets.antispam import antispam
from decimal import Decimal


wins = [
	"💥🐗 | Отлично! Вы попали в кабана, вот ваша награда: {}$",
	"💥🐊 | Отлично! Вы попали в крокодила, вот ваша награда: {}$",
	"💥🐿️🌲 | Отлично! Вы попали в бобра, вот ваша награда: {}$",
	"💥🐰 | Отлично! Вы попали в зайца, вот ваша награда: {}$",
	"💥🐅 | Отлично! Вы попали в рысь, вот ваша награда: {}$",
	"💥🐘 | Отлично! Вы попали в слона, вот ваша награда: {}$"
]

losses = [
	"💥🦔 | Звезда этот ёжик! Вы даже не сообразили, что точно попали в цель. Но вот теперь стоит держать свое оружие и идти дальше, ведь зазвездился - проиграл!",
	"💥😷 | Вот к черту, вы заразились в больнице! Этот раунд лучше пропустить, сидите дома и лечитесь.",
	"💥💀 | Попали по нефору... Теперь у вас дурной привык, и вы тусите каждый вечер в одной из местных грязных бардаков.",
	"💥🐻 | Большой и сильный медведь... только кажется, что попадания не было. Но вот он, на вас смотрит глазами, наполненными гневом!",
	"💥🐺 | Волки - наши братья меньшие. На этот раз вам не удалось их победить, но можно попробовать еще разок.",
	"💥🦊 | Попадание в лису - это успех! Но будет лучше, если вы не смените свое направление и не пойдете на охоту на этих милых зверьков в нашем мире."
]


async def upd_balance(uid, summ, type):
	balance = cursor.execute('SELECT balance FROM users WHERE user_id = ?', (uid,)).fetchone()[0]
	if type == "win":
		summ = Decimal(balance) + Decimal(summ)
	else:
		summ = Decimal(balance) - Decimal(summ)

	cursor.execute(f"UPDATE users SET balance = ? WHERE user_id = ?", (str(summ), uid))
	cursor.execute(f"UPDATE users SET games = games + 1 WHERE user_id = ?", (uid,))
	conn.commit()


@antispam
async def game(message: types.Message):
	uid = message.from_user.id
	rwin, rloser = await win_luser()
	balance = await get_balance(uid)
	url = await url_name(uid)

	try:
		if message.text.lower().split()[1] in ['все', 'всё']:
			summ = balance
		else:
			summ = message.text.split()[1].replace('е', 'e')
			summ = int(float(summ))
	except:
		await message.answer(f'{url}, вы не ввели ставку для игры {rloser}')
		return

	gt = await gametime(uid)
	if gt == 1:
		await message.answer(f'{url}, играть можно каждые 5 секунд. Подождите немного {rloser}')
		return

	if summ < 100:
		await message.answer(f'{url}, ваша ставка не может быть меньше 100$ {rloser}')
		return

	if balance < summ:
		await message.answer(f'{url}, у вас недостаточно денег {rloser}')
		return

	chance = random.random()

	if chance < 0.45:
		su = summ * 0.5
		c2 = '{:,}'.format(int(su)).replace(',', '.')
		txt = random.choice(wins).format(c2)
		await upd_balance(uid, su, 'win')
	elif chance < 0.50:
		txt = '💥❎ | Вы промазали...  деньги остаются при вас.'
	else:
		txt = random.choice(losses)
		await upd_balance(uid, summ, 'lose')

	msg = await message.answer("💥 | Выстрел... посмотрим в кого вы попали")
	await asyncio.sleep(2)
	await bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=txt)


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(game, lambda message: message.text.lower().startswith('охота'))