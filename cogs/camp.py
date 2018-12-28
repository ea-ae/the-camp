import discord
from discord.ext import commands


class Camp:
    """
    Commands related to the camp.
    """

    def __init__(self, client):
        self.client = client

    async def generate_status_message(self):
        # Temporary fake data
        population = 100
        hours = 60
        temperature = -33
        defense = 5411

        food = 725
        fuel = 205
        medicine = 60
        materials = 2509
        scrap = 9487

        status_embed = discord.Embed(color=0x128f39)
        status_embed.add_field(name='Population', value=population, inline=False)
        status_embed.add_field(name='Time Survived',
                               value=f'{int(hours / 24)} days and {hours % 24} hours', inline=False)
        status_embed.add_field(name='Temperature', value=f'{temperature}°C', inline=False)
        status_embed.add_field(name='Defense Points', value=defense, inline=False)

        warehouse_embed = discord.Embed(color=0xe59b16)
        warehouse_embed.add_field(name='Food', value=food, inline=False)
        warehouse_embed.add_field(name='Fuel', value=fuel, inline=False)
        warehouse_embed.add_field(name='Medicine', value=medicine, inline=False)
        warehouse_embed.add_field(name='Materials', value=materials, inline=False)
        warehouse_embed.add_field(name='Scrap', value=scrap, inline=False)

        i = 0
        async for message in self.client.logs_from(channels['camp-status']):
            if message.author == self.client.user:
                if i == 0:
                    await self.client.edit_message(message, new_content='**Warehouse**', embed=warehouse_embed)
                elif i == 1:
                    await self.client.edit_message(message, new_content='**Camp Status**', embed=status_embed)
                i += 1


def setup(client):
    client.add_cog(Camp(client))
