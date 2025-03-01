"""Twitchbot module for AILinux.

This module provides functionality for the AILinux system.
"""
from twitchio.ext import commands
import os

class Bot(commands.Bot):
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
"""
Beschreibung für Klasse Bot.
"""
    def __init__(self):
        token = os.getenv("TWITCH_BOT_TOKEN")
        channels = os.getenv("derleiti.de", "#default_channel").split(",")

        super().__init__(
            token=token,
            prefix='!',
            initial_channels=channels
        )

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        print(f'{message.author.name}: {message.content}')
        await self.handle_commands(message)

    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send(f'Hello {ctx.author.name}!')

if __name__ == "__main__":
    bot = Bot()
    bot.run()
