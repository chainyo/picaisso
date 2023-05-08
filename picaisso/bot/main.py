# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

import asyncio
import io
import json
import os
from collections import OrderedDict
from typing import Optional

import discord
from aiohttp import ClientSession
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger


IMPLEMENTED_TASKS = OrderedDict(
    [
        ("image_to_image", False),
        ("image_variation", False),
        ("super_resolution", False),
        ("text_to_image", True),
    ]
)


class OpenjourneyBot(discord.Client):
    def __init__(
        self,
        *args,
        web_client: ClientSession,
        intents: Optional[discord.Intents] = None,
    ) -> None:
        if intents is None:
            intents = discord.Intents.default()
        intents.members = True

        super().__init__(intents=intents)
        self.web_client = web_client
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self) -> None:
        """When the bot is ready."""
        await self.wait_until_ready()
        logger.debug(f"Logged in as {self.user}")

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """
        On guild join.

        Args:
            guild (discord.Guild): The guild that the bot joined.
        """
        await self.tree.sync(guild=guild)

    async def _authenticate(self) -> None:
        """Authenticate with the API."""
        async with self.web_client.post(
            f"{os.getenv('API_URL')}/auth",
            headers={
                "Content-Type": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "username": os.getenv("USERNAME"),
                "password": os.getenv("PASSWORD"),
            },
        ) as response:
            data = await response.json()
            self.web_client.headers.update(
                {
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {data['access_token']}",
                }
            )

    async def _get_api_task(self) -> str:
        """Get the task of the loaded pipeline for the API."""
        async with self.web_client.get(
            f"{os.getenv('API_URL')}/task",
            headers=self.web_client.headers,
        ) as response:
            data = await response.json()
            return data["task"]

    async def setup_hook(self) -> None:
        """Setup the bot at startup."""
        await self._authenticate()
        self.tree.add_command(art)
        await self.tree.sync()

    async def generate_art(self, interaction: discord.Interaction, prompt: str) -> None:
        """
        Generate art from prompt and send it to the user.

        Args:
            interaction (discord.Interaction): The interaction that triggered the command.
            prompt (str): The prompt to generate art from.

        Raises:
            Exception: If something went wrong while generating art.
        """
        try:
            # Check if the task is implemented for the bot
            api_task = await self._get_api_task()
            if not IMPLEMENTED_TASKS[api_task]:
                raise Exception(f"Task {api_task} is not implemented for the bot")

            async with self.web_client.post(
                f"{os.getenv('API_URL')}/generate",
                headers=self.web_client.headers,
                data=json.dumps({"prompt": prompt, "author": f"discord_{interaction.user}"}),
            ) as response:
                # Handle response status
                if response.status == 200:
                    data = await response.read()
                    image = discord.File(io.BytesIO(data), filename=f"{prompt}.jpg")

                    await interaction.edit_original_response(
                        content=f"Here's your art, {interaction.user.mention} - Art generated from prompt: `{prompt}`",
                        attachments=[image],
                    )

                elif response.status == 401:
                    await self._authenticate()
                    await self.generate_art(interaction, prompt)

                elif response.status == 500:
                    raise Exception("Internal server error")

        except Exception as e:
            await interaction.edit_original_response(content=f"Something went wrong while generating art: {e}")


@app_commands.command(name="art", description="Generate art")
async def art(interaction: discord.Interaction, prompt: str) -> None:
    """
    Command to generate art from prompt for the user.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command.
        prompt (str): The prompt to generate art from.

    Raises:
        requests.exceptions.HTTPError: If something went wrong while generating art.
    """
    if prompt != "":
        await interaction.response.send_message(f"{interaction.user} requested: `{prompt}`")
        interaction.client.loop.create_task(interaction.client.generate_art(interaction, prompt))
    else:
        await interaction.response.send_message("Please provide a prompt")


async def main():
    """Main loop.""" ""
    async with ClientSession() as session:
        async with OpenjourneyBot(commands.when_mentioned, web_client=session) as client:
            await client.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
