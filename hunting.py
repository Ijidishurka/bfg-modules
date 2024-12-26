import asyncio
import random
from bot import bot
from aiogram import types, Dispatcher
from commands.db import conn, cursor, url_name
from commands.games.main import game_check
from assets.transform import transform_int as tr
from assets.antispam import antispam
from decimal import Decimal

from commands.help import CONFIG
from user import BFGuser, BFGconst

CONFIG['help_game'] += '''
   🔫 Охота [ставка]
   🪙 Монетка [орёл/решка] [ставка]
   🎣 Рыбалка [ставка]
   🎲 Рулетка [тип] [ставка]
   🚀 Краш [ставка] [х]'''


async def update_balance(user_id: int, amount: int | str, operation="subtract") -> None:
	balance = cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
	
	if operation == 'add':
		new_balance = Decimal(str(balance)) + Decimal(str(amount))
	else:
		new_balance = Decimal(str(balance)) - Decimal(str(amount))
	
	new_balance = "{:.0f}".format(new_balance)
	cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (str(new_balance), user_id))
	cursor.execute('UPDATE users SET games = games + 1 WHERE user_id = ?', (user_id,))
	conn.commit()


@antispam
async def oxota(message: types.Message, user: BFGuser):
	summ = await game_check(message, user, index=1)
	
	if not summ:
		return
	
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
	
	chance = random.random()
	
	if chance < 0.45:
		su = int(summ * 0.5)
		txt = random.choice(wins).format(tr(su))
		await update_balance(user.user_id, su, operation='add')
	elif chance < 0.5:
		txt = '💥❎ | Вы промазали...  деньги остаются при вас.'
	else:
		txt = random.choice(losses)
		await update_balance(user.user_id, summ, operation='subtract')
	
	msg = await message.answer("💥 | Выстрел... посмотрим в кого вы попали")
	await asyncio.sleep(2)
	await bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=txt)


@antispam
async def monetka(message: types.Message, user: BFGuser):
	win, lose = BFGconst.emj()
	
	try:
		action = message.text.lower().split()[1]
		action = 'орёл' if action == 'орел' else action
	except:
		return
	
	summ = await game_check(message, user, index=2)
	
	if not summ or action not in ['решка', 'орёл']:
		return
	
	win = random.choices(['решка', 'орёл', 'ребро'], weights=[49, 49, 2], k=1)[0]
	win2 = "решку" if win == "решка" else 'орла'
	
	if win == action:
		summ = int(summ * 2)
		await update_balance(user.user_id, summ, operation='add')
		txt = f"🎉 {user.url}, удача на вашей стороне! Монетка упала на {win2}, и вы получили +{tr(summ)}$! {win}"
	elif win == 'ребро':
		txt = f"😲 Невероятно, {user.url}! Монетка упала ребром! Такое случается крайне редко."
	else:
		await update_balance(user.user_id, summ, operation='subtract')
		txt = f"💸 {user.url}, не повезло... Монетка упала на {win2}, и ваш баланс уменьшился на -{tr(summ)}$. {lose}"
	
	msg = await message.answer("🪙 | Подкидываем монетку... затаим дыхание и посмотрим, что выпало!")
	await asyncio.sleep(2)
	await msg.edit_text(text=txt)


@antispam
async def fishing(message: types.Message, user: BFGuser):
	summ = await game_check(message, user, index=1)
	
	if not summ:
		return
	
	wins = [
		"🎣🐟 | Поздравляем! Вам удалось поймать великолепного лосося, ваша награда: {}$",
		"🎣🐠 | Ура! Вы поймали крупного карпа, вот ваша награда: {}$",
		"🎣🐡 | Браво! Вам попался редкий морской окунь, вот ваша награда: {}$",
		"🎣🐬 | Отлично! Вы поймали дельфина, и за это ваша награда: {}$",
		"🎣🦈 | Вау! Вам удалось поймать акулу, вот ваша награда: {}$",
		"🎣🦑 | Здорово! Вы поймали удивительного кальмара, ваша награда: {}$",
		"🎣🐊 | Успех! Вы поймали аллигатора, ваша награда: {}$",
		"🎣🦐 | Поздравляем! Вам удалось поймать редкую креветку, вот ваша награда: {}$",
		"🎣🐚 | Прекрасно! Вы нашли красивую ракушку, вот ваша награда: {}$",
		"🎣🐋 | Ура! Вы поймали огромного кита, ваша награда: {}$"
	]
	
	losses = [
		"🎣🪱 | Упс! Ваши наживки были съедены червем. Попробуйте снова!",
		"🎣🌿 | Увы! Вы поймали только водоросли. В следующий раз повезет больше!",
		"🎣🗑️ | Какой кошмар! Вы вытащили старую игрушку. Пора менять место!",
		"🎣🐢 | Ой! Вам попалась черепаха. Она явно не в настроении.",
		"🎣🐍 | О нет! Вместо рыбы вы поймали змею. Лучше отпустите ее!",
		"🎣🌧️ | Увы! Начался дождь, и рыбалка сорвалась. Вернитесь позже!",
		"🎣🌊 | О, нет! Волны слишком сильные, вам лучше вернуться на берег.",
		"🎣🐸 | Упс! Вместо рыбы вы поймали лягушку. Не беда, попробуйте еще раз!",
		"🎣🎈 | О нет! Ваша наживка улетела в облака! Это не ваш день.",
		"🎣🛶 | Увы! Ваша лодка застряла в камышах. Нужно немного помочь!"
	]
	
	chance = random.random()
	
	if chance < 0.45:
		su = int(summ * 0.5)
		txt = random.choice(wins).format(tr(su))
		await update_balance(user.user_id, su, operation='add')
	elif chance < 0.5:
		txt = '🎣❎ | Вы забыли удочку...  деньги остаются при вас.'
	else:
		txt = random.choice(losses)
		await update_balance(user.user_id, summ, operation='subtract')
	
	msg = await message.answer("🎣 | Закидываем удочку... давайте посмотрим, что ждет нас на дне!")
	await asyncio.sleep(2)
	await msg.edit_text(text=txt)


@antispam
async def roulette_ruless(message: types.Message, user: BFGuser):
	await message.answer(f'''<b>Инструкция по игре в рулетку</b>

Доступные ставки:
К (красное): Ставка на красные числа. (x2)
Ч (черное): Ставка на черные числа. (x2)
Чет: Ставка на четные числа. (x2)
Нечет: Ставка на нечетные числа. (x2)
1-12, 12-26, 26-36: Ставка на диапазоны чисел.(x3)
1-36: Ставка на конкретные числа от 1 до 36 (x36)

Пример: рулетка к 100''')


bets_ruletka = ['к', 'ч', 'чет', 'нечет', '1-12', '12-26', '26-36'] + [str(i) for i in range(1, 37)] + ['0']

colors_ruletka = {0: 'з'}
for i in range(1, 37):
	colors_ruletka[i] = 'к' if i % 2 != 0 else 'ч'

stickers_ruletka = {
	'к': [
		'CAACAgIAAxkBAAEMk7FmqmZgtnl1R-JkJEwRfQLdNz6ZLAACFyAAAq8VIEsjVUg0lrkmmTUE',
		'CAACAgIAAxkBAAEMk7tmqm_BKqgUdm0dKwAB0Yh5ZRevxl8AAtMhAALqFBhLET8AAYNDnvm4NQQ',
		'CAACAgIAAxkBAAEMk79mqm_1R3Mh3RyD6uqVvrSVfugZ8wACWCUAAqqoGUvWgNnF1LMYKDUE',
		'CAACAgIAAxkBAAEMk8NmqnAjvnSr8xyq8EB9G6Nlp2EQNgACgR4AAlrOGUurvYiC23KzDDUE',
		'CAACAgIAAxkBAAEMk8dmqnBR9SBNjL-dtR1yP60ueQFDSwACXSEAAmlUGEt80Rcq4SL85jUE',
		'CAACAgIAAxkBAAEMk8tmqnCORfasBPHzh1PuGeNV68VgzQACNSQAAgZiGEtbqp5yJJxuGTUE'
	],
	'з': [
		'CAACAgIAAxkBAAEMk61mqmY5j0d_UEDae0AvfvKZEoax8wACZhkAApC9IUtsfJ-2uiU4izUE'
	],
	'ч': [
		'CAACAgIAAxkBAAEMk69mqmZZF10-ZR9YxY4qXR1j2scK-AACEx0AArcIGUuEI9r6o_yNuTUE',
		'CAACAgIAAxkBAAEMk7lmqm9lkP4C2hk0qtpEU8JIOmG-GwACkxwAAugyGUvna4QpJ1UJGzUE',
		'CAACAgIAAxkBAAEMk71mqm_WQqPVyzrWfQIjBQWNYBaQ-gACRikAAhU5GUuFKr8wGVrZzjUE',
		'CAACAgIAAxkBAAEMk8FmqnALUmlANSfVHxp4AWxo1xkS1gACsiEAAuZFGEtTID7Mrd681DUE',
		'CAACAgIAAxkBAAEMk8VmqnA8oe2QlJCIhVJLdZRBCR2iQQAC2CIAAmSNGEs-Z2XuB7CSjjUE',
		'CAACAgIAAxkBAAEMk8lmqnBzJE7zX9et0fimZsrRsTvAFgACtiEAAjIZGUsIhaOXuETEMzUE'
	]
}


@antispam
async def roulette(message: types.Message, user: BFGuser):
	win, lose = BFGconst.emj()
	summ = await game_check(message, user, index=2)
	
	if not summ:
		return
	
	try:
		bet = message.text.lower().split()[1]
		if bet not in bets_ruletka:
			await message.answer(f'{user.url}, вы ввели не корректную ставку {lose}')
			return
	except:
		await message.answer(f'{user.url}, вы не ввели ставку для игры {lose}')
		return
	
	if bet in ['к', 'ч']:
		win_conditions = [i for i in range(1, 37) if colors_ruletka[i] == ('к' if bet == 'к' else 'ч')]
	elif bet == 'чет':
		win_conditions = [i for i in range(1, 37) if i % 2 == 0]
	elif bet == 'нечет':
		win_conditions = [i for i in range(1, 37) if i % 2 != 0]
	elif bet in ['1-12', '13-24', '25-36']:
		start, end = map(int, bet.split('-'))
		win_conditions = list(range(start, end + 1))
	else:
		win_conditions = [int(bet)]
	
	winning_number = random.randint(0, 36)
	win = winning_number in win_conditions
	
	color = colors_ruletka[winning_number]
	stxt = '🔴 Красный' if color == 'к' else ('⚫️ Черный' if color == 'ч' else '🟢 Зеленый')
	
	if win:
		multiplier = 2 if bet in ['к', 'ч', 'чет', 'нечет'] else (3 if bet in ['1-12', '13-24', '25-36'] else 36)
		su = int(summ * multiplier)
		txt = f"{user.url}, шарик остановился на {winning_number} ({stxt}). Вы выиграли {tr(su)}$"
		await update_balance(user.user_id, su, operation='add')
	else:
		txt = f"{user.url}, шарик остановился на {winning_number} ({stxt}). Вы проиграли -{tr(summ)}$"
		await update_balance(user.user_id, summ, operation='subtract')
	
	sticker = random.choice(stickers_ruletka[color])
	msg = await bot.send_sticker(message.chat.id, sticker=sticker)
	await asyncio.sleep(2)
	await message.answer(txt, reply=msg.message_id)


@antispam
async def crash(message: types.Message, user: BFGuser):
	win, lose = BFGconst.emj()
	summ = await game_check(message, user, index=1)
	
	if not summ:
		return
	
	try:
		bet = round(float(message.text.lower().split()[2]), 2)
		if not (1.01 <= bet <= 10):
			await message.answer(f'''🥶 {user.url}, <i>ты ввел что-то неправильно!</i>
<code>·····················</code>
📈 <b>Краш [ставка] [1.01-10]</b>

Пример: <code>краш 100 1.1</code>
Пример: <code>краш 100 4</code>''')
			return
		
	except:
		await message.answer(f'{user.url}, вы не ввели ставку для игры {lose}')
		return
	
	bet2 = bet+1 if bet < 4 else (bet+3 if bet <= 7 else 10)
	rnumber = round(random.uniform(1.01, bet2), 2)
	
	if bet < rnumber:
		summ = int(bet*summ)
		await message.answer(f'🚀 {user.url}, ракета остановилась на x{rnumber} 📈\n✅ Ты выиграл! Твой выигрыш составил {tr(summ)}$')
		await update_balance(user.user_id, summ, operation='add')
	else:
		await message.answer(f'🚀 {user.url}, ракета упала на x{rnumber} 📉\n❌ Ты проиграл {tr(summ)}$')
		await update_balance(user.user_id, summ, operation='subtract')
	

def register_handlers(dp: Dispatcher):
	dp.register_message_handler(oxota, lambda message: message.text.lower().startswith('охота'))
	dp.register_message_handler(monetka, lambda message: message.text.lower().startswith('монетка'))
	dp.register_message_handler(fishing, lambda message: message.text.lower().startswith('рыбалка'))
	dp.register_message_handler(roulette_ruless, lambda message: message.text.lower() == 'рулетка')
	dp.register_message_handler(roulette, lambda message: message.text.lower().startswith('рулетка'))
	dp.register_message_handler(crash, lambda message: message.text.lower().startswith('краш'))


MODULE_DESCRIPTION = {
	'name': '🎮 Новые игры',
	'description': 'Модуль добавляет новые игры:\n- Монетка\n- Охота\n- Рыбалка\n- Рулетка\n - Краш'
}