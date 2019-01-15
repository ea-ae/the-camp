import discord
from discord.ext import commands
import random
import json


class Player:
    """
    Player-related commands.
    """

    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True)
    async def farm(self, ctx, amount='1'):
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

        if not amount.isdigit():
            await self.client.say('Invalid command!')
            return

        amount = int(amount)

        async with self.client.db.acquire() as conn:
            result = await self.client.utils.get_user_columns(conn, ctx.message.author,
                                                              'inventory', 'food', 'energy', 'last_energy')

            food = amount

            inventory = json.loads(result['inventory'])
            if inventory.get('farmwagon', 0) > 0:
                food *= 2

            result = await self.client.utils.set_resources(conn, ctx.message.author,
                                                           {'food': food, 'energy': -amount},
                                                           {'food': food}, user_result=result)

        if result is True:
            await self.client.say(
                f'You earned **{food}** food ration{"s" if food > 1 else ""} for both yourself and the camp.')
        else:
            await self.client.say(result)

    @commands.command(pass_context=True)
    async def mine(self, ctx, amount='1'):
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

        if not amount.isdigit():
            await self.client.say('Invalid command!')
            return

        amount = int(amount)

        async with self.client.db.acquire() as conn:
            result = await self.client.utils.get_user_columns(conn, ctx.message.author, 'inventory', 'materials',
                                                              'fuel', 'energy', 'last_energy', 'food')

            mats = random.randrange(0, amount + 1)
            fuel = (amount - mats) * 10

            inventory = json.loads(result['inventory'])
            if inventory.get('miningdrill', 0) > 0:
                mats *= 2
                fuel *= 2

            result = await self.client.utils.set_resources(conn, ctx.message.author,
                                                           {'materials': mats, 'fuel': fuel, 'energy': -amount},
                                                           {'materials': mats, 'fuel': fuel}, user_result=result)

        if result is True:
            await self.client.say(
                f'You earned **{mats}** material{"s" if mats > 1 or mats == 0 else ""} and '
                f'**{fuel}** fuel for both yourself and the camp.')
        else:
            await self.client.say(result)

    @commands.command(pass_context=True)
    async def guard(self, ctx, amount='1', work_type=None):
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

        if not amount.isdigit():
            await self.client.say('Invalid command!')
            return

        amount = int(amount)

        if work_type == 'free':
            result = await self.client.utils.set_resources(self.client.db, ctx.message.author, {'energy': -amount},
                                                           {'defense': amount})
        else:
            result = await self.client.utils.set_resources(self.client.db, ctx.message.author,
                                                           {'scrap': amount, 'energy': -amount},
                                                           {'scrap': -amount, 'defense': amount})

        if result is True:
            if work_type == 'free':
                await self.client.say(f'The camp\'s defense increased by **{amount}**. '
                                      f'You were working for free and earned no scrap.')
            else:
                await self.client.say(f'The camp\'s defense increased by **{amount}**. '
                                      f'You were given **{amount}** scrap as payment.')
        else:
            if 'scrap' in result:  # The camp doesn't have enough scrap to pay for guarding
                await self.client.say('The camp doesn\'t have enough scrap to pay for guarding.\n'
                                      'If you would like to work for free, type `!guard <amount> free`.')
            else:
                await self.client.say(result)

    @commands.command(pass_context=True)
    async def scavenge(self, ctx, time='1'):
        user_roles = await self.client.utils.get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' not in user_roles:
            return

        if not time.isdigit():
            await self.client.say('Invalid command!')
            return

        time = int(time)

        async with self.client.db.acquire() as conn:
            # fuel = dict(await self.client.utils.get_user_columns(conn, ctx.message.author, 'fuel'))['fuel']
            fuel_needed = time ** 2
            resources = dict()
            msg = 'You put on your heat armor and ventured outside the camp looking for resources.\n'

            for event in range(time):
                if random.random() > 0.3:  # Find loot
                    r = random.randint(1, 10)
                    if r <= 4:
                        earned_food = random.randint(1, 3)
                        resources['food'] = resources.get('food', 0) + earned_food
                        msg += f'You found some canned {random.choice("soup", "beans", "vegetables", "tuna")} '
                                f'and earned **{earned_food}** food ration{"s" if earned_food > 1}.\n'
                    elif r <= 9:
                        earned_scrap = random.randint(2, 5)
                        resources['scrap'] = resources.get('scrap', 0) + earned_scrap
                        msg += f'You found some {random.choice("junk", "components", "electronics")} and were '
                               f'able to get **{earned_scrap}** scrap out of it.'
                    else:
                        earned_medicine = random.randint(1, 2)
                        resources['medicine'] = resources.get('medicine', 0) + earned_medicine
                        medicine_list = [
                            'pack of bandages',
                            'first aid kit',
                            'bottle of antibiotics',
                            'bottle of painkillers',
                            'bottle of pills',
                            'pack of band-aids',
                            'box of surgical instruments'
                        ]
                        msg += f'You were lucky and found a {random.choice(medicine_list)} just laying around.'
                else:  # Run into a danger
                    pass


        if result is True:
            await self.client.say(
                f'You earned **{food}** food ration{"s" if food > 1 else ""} for both yourself and the camp.')
        else:
            await self.client.say(result)


def setup(client):
    client.add_cog(Player(client))
