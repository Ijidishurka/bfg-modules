from aiogram import types, Dispatcher
from assets.antispam import antispam
from assets.transform import transform_int as tr
from commands.help import CONFIG
from user import BFGuser, BFGconst

CONFIG['help_rz'] += '''\n\n⛓️‍💥 Крафт:
   ⚡️ Крафты
   📌 Крафт [номер]'''

CRAFTING = {
	1: {
		'name': 'Золотой Айфон',
		'assets': {
			'iron': 2500,
			'gold': 1200,
		},
		'payout': 10_000_000_000
	},
	2: {
		'name': 'Алмазный меч',
		'assets': {
			'gold': 2750,
			'diamond': 1500
		},
		'payout': 200_000_000_000
	},
	3: {
		'name': 'Аметистовая корона',
		'assets': {
			'amestit': 750,
			'emeralds': 250
		},
		'payout': 750_000_000_000
	},
	4: {
		'name': 'Аквамариновый щит',
		'assets': {
			'aquamarine': 200,
			'matter': 100,
		},
		'payout': 1_000_000_000_000
	},
	5: {
		'name': 'Плазменный генератор',
		'assets': {
			'plasma': 150,
			'nickel': 50,
		},
		'payout': 50_00_000_000_000
	},
	6: {
		'name': 'Титановый экзоскелет',
		'assets': {
			'titanium': 50,
			'cobalt': 10,
		},
		'payout': 5_500_000_000_000_000
	},
}

remj = {
	'iron': '⛓️ Железа',
	'gold': '🌕 Золота',
	'diamond': '💎 Алмазов',
	'amestit': '🎆 аметиста',
	'emeralds': '🍀 Изумрудов',
	'aquamarine': '💠 Аквамаринов',
	'matter': '🌌 Материи',
	'plasma': '💥 Плазмы',
	'nickel': '🪙 Никеля',
	'titanium': '⚙️ Титаниума',
	'cobalt': '🧪 Кобальта',
}


@antispam
async def crafts(message: types.Message, user: BFGuser):
	txt = f'{user.url}, доступные крафты:\n'
	
	for num, i in enumerate(CRAFTING.values(), start=1):
		assets = '\n'.join(f"    {remj[res]}: {amount}" for res, amount in i['assets'].items())
		txt += f"\n{num}. {i['name']}:\n{assets}\n"
	
	txt += '\nДля крафта введите "Крафт [номер]"'
	await message.answer(txt)
	
	
	
@antispam
async def craft(message: types.Message, user: BFGuser):
	win, lose = BFGconst.emj()
	
	try:
		n = int(message.text.split()[1])
	except:
		await message.answer(f'{user.url}, вы не ввели номер крафта {lose}')
		return
	
	data = CRAFTING.get(n)
	
	if not data:
		await message.answer(f'{user.url}, такого крафта не существует {lose}')
		return
	
	resources = {
		"iron": user.mine.iron,
		"gold": user.mine.gold,
		"diamond": user.mine.diamond,
		"amethyst": user.mine.amestit,
		"aquamarine": user.mine.aquamarine,
		"emeralds": user.mine.emeralds,
		"matter": user.mine.matter,
		"plasma": user.mine.plasma,
		"nickel": user.mine.nickel,
		"titanium": user.mine.titanium,
		"cobalt": user.mine.cobalt,
	}
	
	for resours, summ in data['assets'].items():
		if int(resources[resours]) < int(summ):
			await message.answer(f'{user.url}, у вас недостаточно <code>{remj[resours]}</code> {lose}')
			return
	
	for resours, summ in data['assets'].items():
		await resources[resours].upd(summ, '-')
	
	await user.balance.upd(data['payout'], '+')
	await message.answer(f'{user.url}, вы успешно обменяли {data["name"]} на {tr(data["payout"])}$ {win}')
	

def register_handlers(dp: Dispatcher):
	dp.register_message_handler(crafts, lambda message: message.text.lower() == 'крафты')
	dp.register_message_handler(craft, lambda message: message.text.lower().startswith('крафт'))


MODULE_DESCRIPTION = {
	'name': '⛓️‍💥 Крафт',
	'description': 'Добавляет рецепты крафта за руду.'
}