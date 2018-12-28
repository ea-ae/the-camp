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
        user_roles = await get_user_roles(self.client.server, ctx.message.author)
        if 'Alive' in user_roles:
            await self.client.say('You have already joined the camp.')
        elif 'Dead' in user_roles:
            await self.client.say('You have already joined this game. Since you are dead, you have to wait till '
                                  'someone revives you or the next game starts.')
        else:
            async with self.client.db.acquire() as conn:
                tr = conn.transaction()
                await tr.start()
                try:
                    query = '''SELECT EXISTS(SELECT 1 FROM players WHERE user_id = $1);'''
                    result = await self.client.db.fetchval(query, ctx.message.author.id)

                    if result:
                        await self.client.say(
                            'Welcome back to **The Camp**!\n'
                            'Remember to spend the XP gained from your previous game using `!upgrade`.\n'
                            'To see a list of available commands, type `!help`.')
                        pass  # TODO: Set row back to default values
                    else:
                        print('No result tonight!')
                        query = '''INSERT INTO players (user_id, status) VALUES ($1, 'normal')'''
                        await self.client.db.execute(query, ctx.message.author.id)

                        await self.client.say(
                            'Welcome to **The Camp**!\n'
                            'Since it is your first time here, I\'d recommend reading the tutorial.\n'
                            'To see a list of available commands, type `!help`.')
                except Exception as e:
                    await tr.rollback()
                    await self.client.say('Something went wrong!')
                    print(e)
                else:
                    await tr.commit()

                    alive_role = discord.utils.get(self.client.server.roles, name='Alive')
                    survivor_role = discord.utils.get(self.client.server.roles, name='Survivor')  # TODO: XP-based role
                    member = self.client.server.get_member(ctx.message.author.id)
                    await self.client.add_roles(member, alive_role, survivor_role)


def setup(client):
    client.add_cog(Ranks(client))
