from .. import events
import random


async def surprise_attack(client, title):
    difficulty = 100  # TEMP

    attack = random.randint(int(difficulty / 2), difficulty)
    scrap = random.randint(int(attack / 2), int(attack * 1.5))
    result = await client.utils.set_camp_data(client.db,
                                              {'defense': -attack, 'scrap': scrap},
                                              negative_to_zero=True)

    msg = (f'**{title}**\n'
           f'A group of bandits has launched a surprise attack against our camp!\n')

    if result == 'The camp doesn\'t have enough defense.':
        msg += (f'We weren\'t able to hold them back and they got over our walls. '
                f'They raided our warehouse and stole as many of our resources as they could carry. '
                f'They also robbed some of our residents out of all their resources.')
        await client.utils.set_camp_data(client.db,
                                         {'food': randint(int(attack / 2), attack),
                                          'materials': randint(int(attack / 2), attack),
                                          'medicine': randint(int(attack / 4), int(attack / 2)),
                                          'scrap': randint(int(attack / 2), attack)},
                                         negative_to_zero=True)
    else:
        msg += (f'Luckily we were able to withstand their attack. We killed some of them and looted their '
                f'bodies, earning **{scrap}** scrap. We lost **{attack}** defense due to their attack.')

    return await client.send_message(client.channels['town-hall'], msg)


def add_event():
    events.Event(title='Surprise Attack',
                 type='announcement',
                 start=surprise_attack)
