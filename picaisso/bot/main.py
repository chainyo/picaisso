# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

import asyncio
import io
import json
import os
import requests
from aiohttp import ClientSession
from dotenv import load_dotenv
from loguru import logger
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


class OpenjourneyBot(discord.Client):
    def __init__(
        self,
        *args,
        web_client: ClientSession,
        intents: Optional[discord.Intents] = None,
    ):
        if intents is None:
            intents = discord.Intents.default()
        intents.members = True
        
        super().__init__(intents=intents)
        self.web_client = web_client
        self.tree = app_commands.CommandTree(self)
        
    
    async def on_ready(self):
        await self.wait_until_ready()
        logger.debug(f"Logged in as {self.user}")
        
    
    async def _authenticate(self):
        async with self.web_client.post(
            f"{os.getenv('API_URL')}/auth",
            headers={
                "Content-Type": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "username": os.getenv("USERNAME"),
                "password": os.getenv("PASSWORD")
            },
        ) as response:
            data = await response.json()
            self.web_client.headers.update({
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {data['access_token']}",
            })
        
    
    async def setup_hook(self):
        await self._authenticate()
        self.tree.add_command(art)
        await self.tree.sync()


    async def generate_art(self, interaction: discord.Interaction, prompt: str):
        try:
            logger.debug(f"Client headers: {self.web_client.headers}")
            async with self.web_client.post(
                f"{os.getenv('API_URL')}/generate",
                headers=self.web_client.headers,
                data=json.dumps({"prompt": prompt, "author": f"discord_{interaction.user}"}),
            ) as response:
                data = await response.read()
                image = discord.File(io.BytesIO(data), filename=f"{prompt}.jpg")
                await interaction.edit_original_response(
                    content=f"Here's your art, {interaction.user.mention} - Art generated from prompt: `{prompt}`",
                    attachments=[image],
                )
        except Exception as e:
            await interaction.edit_original_response(content=f"Something went wrong while generating art: {e}")


@app_commands.command(name="art", description="Generate art")
async def art(
    interaction: discord.Interaction,
    prompt: str,
):
    try:
        if prompt != "":
            await interaction.response.send_message(f"{interaction.user} requested: `{prompt}`")
            interaction.client.loop.create_task(interaction.client.generate_art(interaction, prompt))
        else:
            await interaction.response.send_message("Please provide a prompt")
    except requests.exceptions.HTTPError as e:
        await interaction.client._authenticate()
        logger.error(e)
        return await art(interaction, prompt)
  
   
async def main():
    async with ClientSession() as session:
        async with OpenjourneyBot(commands.when_mentioned, web_client=session) as client:
            await client.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
