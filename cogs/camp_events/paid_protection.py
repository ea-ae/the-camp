from .. import events
import random
import datetime as dt


async def paid_protection(client, title):
    msg = (f'**{title}**\n'
           f'A group of mercenaries have offered their services to us. They said that they are temporarily '
           f'passing by and ran out of food. They offered to protect us from any bandit attacks '
           f'(giving us **1000** defense points) if we give them **500** food rations. We have to make a '
           f'decision in six hours. What should we do?\n'
           f'1\u20e3 Agree and give them 500 food rations.\n'
           f'2\u20e3 Decline their offer.')

    return await client.send_message(client.channels['town-hall'], msg)


async def paid_protection_end(client, title, choice):
    async with client.db.acquire() as conn:
        msg = f'**{title}**\n'
        food = dict(await client.utils.get_camp_data(conn, 'food'))['food']

        if choice == 0 and food >= 500:
            msg += 'We agreed with their offer and paid them **500** food rations. '
            if random.random() > 0.5:
                msg += 'The mercenaries honored their part of the deal and we received **1000** defense.'
                await client.utils.set_camp_data(conn, {'food': -500, 'defense': 1000})
            else:
                msg += 'Suddenly, the supposed mercenaries disappeared with the food and never came back.'
                await client.utils.set_camp_data(conn, {'food': -500})
        else:
            if food >= 500:
                msg += 'We decided to decline their offer. '
            else:
                msg += ('We decided to decline their offer and told them we did not have enough food to '
                        'pay them. ')

            if random.random() > 0.75:
                msg += 'The mercenaries were not happy to hear that. Desperate for food, they attacked us. '
                result = await client.utils.set_camp_data(conn, {'defense': -1000})

                if result == 'The camp doesn\'t have enough defense.':
                    msg += ('We were not able to withstand their attack and they got into our city. They took '
                            'as many resources from our warehouse as they could carry and left.')
                    await client.utils.set_camp_data(conn, {'food': -1000,
                                                            'medicine': -100,
                                                            'scrap': -1000},
                                                     negative_to_zero=True)
                else:
                    msg += ('We were able to withstand their attack, but lost **1000** defense. Soon enough '
                            'they gave up and left.')
            else:
                msg += 'The mercenaries left in disappointment and we never saw them again.'

    await client.send_message(client.channels['town-hall'], msg)


def add_event():
    events.Event(title='Paid Protection',
                 type='vote',
                 options=2,
                 length=dt.timedelta(hours=6),
                 start=paid_protection,
                 end=paid_protection_end)
