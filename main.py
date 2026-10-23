import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio
import os
import re
import aiohttp

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot Online 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ==========================================
# RICHIESTA DOCUMENTO
# ==========================================

# Tieni questo canale privato: contiene dati personali.
ID_CANALE_LOG_RICHIESTA_DOCUMENTO = 1563240758390030517
ID_RUOLO_APPROVA_DOCUMENTO = 1562507751975035065
TITOLO_RICHIESTA_IN_ATTESA = "📄 Nuova richiesta documento"
_lock_richieste_documento = {}


async def cerca_avatar_roblox(nome_utente: str):
    timeout = aiohttp.ClientTimeout(total=12)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            "https://users.roblox.com/v1/usernames/users",
            json={
                "usernames": [nome_utente],
                "excludeBannedUsers": True,
            },
        ) as response:
            response.raise_for_status()
            utenti = (await response.json()).get("data", [])

        if not utenti:
            return None

        roblox_id = utenti[0]["id"]

        async with session.get(
            "https://thumbnails.roblox.com/v1/users/avatar-headshot",
            params={
                "userIds": str(roblox_id),
                "size": "150x150",
                "format": "Png",
                "isCircular": "true",
            },
        ) as response:
            response.raise_for_status()
            avatar = (await response.json()).get("data", [])

        if not avatar:
            return None

        return avatar[0].get("imageUrl")


class ViewApprovazioneRichiestaDocumento(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        membro = interaction.user

        if not isinstance(membro, discord.Member):
            await interaction.response.send_message(
                "Questi pulsanti si possono usare solo nel server.",
                ephemeral=True,
            )
            return False

        if not any(
            ruolo.id == ID_RUOLO_APPROVA_DOCUMENTO
            for ruolo in membro.roles
        ):... 
