import discord
from discord.ext import commands

from .utils import get_user_roles


class Ranks:
    """
    Manages ranks of players.
    """

    def __init__(self, client):
        self.client = client

    # TODO: Assign roles
    @commands.command(pass_context=True)
    async def join(self, ctx):
        async def add_player(alive, new_player, energy):
            """
            Add a player to the camp by wiping his resources and giving him necessary roles.
            """

            tr = conn.transaction()
            await tr.start()

            try:
                if new_player:
                    query = '''INSERT INTO players (user_id, status) VALUES ($1, 'normal')'''
                    await conn.execute(query, ctx.message.author.id)
                else:
                    query = '''UPDATE players SET energy = $1, food = default, fuel = default,
                    medicine = default, materials = default, scrap = default, house_upgrades = NULL,
                    till_normal = NULL, last_crime = NULL, status = 'normal', last_energy = default
                    WHERE user_id = $2'''

                    await conn.execute(query, energy, ctx.message.author.id)
            except Exception as e:
                await tr.rollback()
                await self.client.say('Something went wrong! Please type `!join` again.')
                print(e)
                return False
            else:
                await tr.commit()
            print('Adding roles...')

            if alive:
                status_role = discord.utils.get(self.client.server.roles, name='Alive')
            else:
                status_role = discord.utils.get(self.client.server.roles, name='Dead')

            survivor_role = discord.utils.get(self.client.server.roles, name='Survivor')  # TODO: Make it xp-based
            member = self.client.server.get_member(ctx.message.author.id)
            await self.client.add_roles(member, status_role, survivor_role)
            print('Roles added!')

        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' in user_roles:
            await self.client.say('You have already joined the camp.')
        elif 'Dead' in user_roles:
            await self.client.say('You have already joined this game. Since you are dead, you have to wait for the '
                                  'next game to start.')
        else:
            max_energy = 12

            async with self.client.db.acquire() as conn:
                query = '''SELECT status FROM players WHERE user_id = $1;'''
                result = await conn.fetch(query, ctx.message.author.id)

                if len(result) > 0 and result[0]['status'] in ('normal', None):
                    await self.client.say(
                        'Welcome back to **The Camp**!\n'
                        'Remember to spend the XP gained from your previous game using `!upgrade`.\n'
                        'To see a list of available commands, type `!help`.')

                    if result[0]['status'] == 'normal':
                        energy = 0
                    else:
                        energy = max_energy
                    await add_player(True, False, energy)

                elif len(result) == 0:
                    await self.client.say(
                        'Welcome to **The Camp**!\n'
                        'Since it is your first time here, I\'d recommend reading the tutorial.\n'
                        'To see a list of available commands, type `!help`.')
                    await add_player(True, True, 12)

                elif len(result) > 0 and result[0]['status'] == 'dead':
                    await self.client.say('You have already died this game! Please wait for the next one to start.')
                    await add_player_roles(False, False, 0)

                else:
                    await self.client.say('Something went wrong!')


def setup(client):
    client.add_cog(Ranks(client))
