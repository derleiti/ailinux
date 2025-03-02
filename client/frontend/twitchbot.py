"""Twitchbot module for AILinux.

This module provides functionality for the AILinux system to interact with Twitch chat.
"""
from twitchio.ext import commands
import os

class Bot(commands.Bot):
    """Twitch bot implementation for AILinux.
    
    This class extends TwitchIO's Bot class to provide chat interaction capabilities.
    """
    def __init__(self):
        """Initialize the Twitch bot with configuration from environment variables."""
        token = os.getenv("TWITCH_BOT_TOKEN")
        channels = os.getenv("TWITCH_CHANNELS", "#default_channel").split(",")

        super().__init__(
            token=token,
            prefix='!',
            initial_channels=channels
        )

    async def event_ready(self):
        """Handle the bot ready event when successfully connected to Twitch."""
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        """Process each incoming message from Twitch chat.
        
        Args:
            message: Message object from TwitchIO
        """
        print(f'{message.author.name}: {message.content}')
        await self.handle_commands(message)

    @commands.command(name='hello')
    async def hello(self, ctx):
        """Respond to the '!hello' command in chat.
        
        Args:
            ctx: Command context from TwitchIO
        """
        await ctx.send(f'Hello {ctx.author.name}!')

if __name__ == "__main__":
    bot = Bot()
    bot.run()
