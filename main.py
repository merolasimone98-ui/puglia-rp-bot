import os
import json
import asyncio
import datetime
from flask import Flask
from threading import Thread

import discord
from discord import app_commands
from discord.ext import commands

# ==========================================
# 🌐 WEBSERVER FLASK (KEEP ALIVE PER RENDER)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot Puglia RP attivo 24/7!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ==========================================
# ⚙️ CONFIGURAZIONE BOT & INTENTI
# ==========================================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="/", intents=intents)

# 📌 CONFIGURAZIONE ID RUOLI E CANALI
ROLE_STAFF_BASE_ID = 1562507751975035065
ID_RUOLO_CITTADINO = 1562894350135066674
ID_RUOLO_PORTO_DARMI = 1562894902428442695

RUOLI_PATENTI = {
    'A': 1562894624597479555,
    'B': 1562894703081431090,
    'C': 1562894760878800897,
    'D': 1562894822983860364
}

ID_FORUM_DOCUMENTI = 1562891782415450183

ID_CANALE_COMANDO_RECENSIONI = 123456789012345678  # Sostituisci con l'ID del canale recensioni
ID_CANALE_LOG_RECENSIONI = 1563176554786463894      # Canale Forum Recensioni
LINK_IMMAGINE_RECENSIONE = "https://media.discordapp.net/attachments/1561284670883242086/1563156338580652072/1792755906447.jpg?ex=6adc9a49&is=6adb48c9&hm=889b0be762da4780fd7225ff6632c4ae457b26a5d1b1f6bfdadb3c413816c642&=&format=webp"

ID_CANALE_REGISTRO_ARRESTI = 1524685772995690607
ID_CANALE_REGISTRO_MULTE = 1563215066411696299
ID_CANALE_CONTO_BANCARIO = 1563216017851949227

# ==========================================
# 💾 GESTIONE PERSISTENZA DATI (JSON)
# ==========================================
DATA_FILE = "staff_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "economy": {}, "duty": {}, "rp_names": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Errore lettura {DATA_FILE}: {e}")
        return {"users": {}, "economy": {}, "duty": {}, "rp_names": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Errore salvataggio {DATA_FILE}: {e}")

def get_user_eco(user_id_str):
    data = load_data()
    if "economy" not in data:
        data["economy"] = {}
    if user_id_str not in data["economy"]:
        data["economy"][user_id_str] = {"bank": 0, "cash": 0, "has_account": False}
        save_data(data)
    return data["economy"][user_id_str]

def update_user_eco(user_id_str, eco_data):
    data = load_data()
    if "economy" not in data:
        data["economy"] = {}
    data["economy"][user_id_str] = eco_data
    save_data(data)

def get_user_duty(user_id_str):
    data = load_data()
    if "duty" not in data:
        data["duty"] = {}
    if user_id_str not in data["duty"]:
        data["duty"][user_id_str] = {"total_seconds": 0, "last_start": None, "on_duty": False}
        save_data(data)
    return data["duty"][user_id_str]

def update_user_duty(user_id_str, duty_data):
    data = load_data()
    if "duty" not in data:
        data["duty"] = {}
    data["duty"][user_id_str] = duty_data
    save_data(data)

# ==========================================
# 🎃 MODULO: PANNELLO DOCUMENTI (CON APPROVAZIONE STAFF)
# ==========================================
ID_CANALE_ACCETTAZIONE_STAFF = 1562891209675116544

# --- Vista con Bottoni Accetta / Rifiuta per lo Staff ---
class VistaApprovazioneStaff(discord.ui.View):
    def __init__(self, tipo_documento, nome_rp, roblox_user, eta_rp, cat_patente=None, motivazione=None, target_user_id=None):
        super().__init__(timeout=None)
        self.tipo_documento = tipo_documento
        self.nome_rp = nome_rp
        self.roblox_user = roblox_user
        self.eta_rp = eta_rp
        self.cat_patente = cat_patente
        self.motivazione = motivazione
        self.target_user_id = target_user_id

    @discord.ui.button(label="Accetta Documento", style=discord.ButtonStyle.success, emoji="🟢", custom_id="btn_accetta_doc")
    async def btn_accetta(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Controllo Staff Base / Admin
        role_staff = interaction.guild.get_role(ROLE_STAFF_BASE_ID)
        if role_staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ **Solo lo Staff può accettare i documenti!**", ephemeral=True)
            return

        await interaction.response.defer()

        # 1. Invia la richiesta approvata nel Forum Documenti
        forum = interaction.guild.get_channel(ID_FORUM_DOCUMENTI)
        target_member = interaction.guild.get_member(self.target_user_id)
        mention_str = target_member.mention if target_member else f"<@{self.target_user_id}>"

        if forum and isinstance(forum, discord.ForumChannel):
            embed_forum = discord.Embed(
                title=f"📑 DOCUMENTO APPROVATO: {self.tipo_documento.upper()}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed_forum.add_field(name="👤 Utente Discord", value=mention_str, inline=True)
            embed_forum.add_field(name="📜 Nome RP", value=f"`{self.nome_rp}`", inline=True)
            embed_forum.add_field(name="🎮 Roblox", value=f"`{self.roblox_user}`", inline=True)
            embed_forum.add_field(name="🎂 Età RP", value=f"`{self.eta_rp} anni`", inline=True)
            embed_forum.add_field(name="👮 Approvato da", value=interaction.user.mention, inline=False)

            if self.cat_patente:
                embed_forum.add_field(name="🚗 Categoria", value=f"**Patente {self.cat_patente}**", inline=False)
            if self.motivazione:
                embed_forum.add_field(name="📋 Motivazione", value=f"```\n{self.motivazione}\n```", inline=False)

            titolo_post = f"✅ [{self.tipo_documento}] {self.nome_rp}"
            try:
                await forum.create_thread(name=titolo_post, embed=embed_forum)
            except Exception as e:
                print(f"Errore creazione post forum: {e}")

        # 2. Assegnazione automatica del ruolo
        if target_member:
            try:
                if self.tipo_documento == "Cittadinanza":
                    ruolo = interaction.guild.get_role(ID_RUOLO_CITTADINO)
                    if ruolo: await target_member.add_roles(ruolo)
                elif self.tipo_documento.startswith("Patente") and self.cat_patente:
                    ruolo_id = RUOLI_PATENTI.get(self.cat_patente)
                    if ruolo_id:
                        ruolo = interaction.guild.get_role(ruolo_id)
                        if ruolo: await target_member.add_roles(ruolo)
                elif self.tipo_documento == "Porto d'Armi":
                    ruolo = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)
                    if ruolo: await target_member.add_roles(ruolo)
            except Exception as e:
                print(f"Errore aggiunta ruolo: {e}")

        # 3. Disabilita i bottoni e aggiorna il messaggio nel canale staff
        for child in self.children:
            child.disabled = True

        embed_orig = interaction.message.embeds[0]
        embed_orig.color = discord.Color.green()
        embed_orig.title = f"✅ DOCUMENTO ACCETTATO DA {interaction.user.display_name}"
        await interaction.message.edit(embed=embed_orig, view=self)


    @discord.ui.button(label="Rifiuta Documento", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="btn_rifiuta_doc")
    async def btn_rifiuta(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_staff = interaction.guild.get_role(ROLE_STAFF_BASE_ID)
        if role_staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ **Solo lo Staff può rifiutare i documenti!**", ephemeral=True)
            return

        await interaction.response.defer()

        # Disabilita bottoni e aggiorna stato
        for child in self.children:
            child.disabled = True

        embed_orig = interaction.message.embeds[0]
        embed_orig.color = discord.Color.red()
        embed_orig.title = f"❌ DOCUMENTO RIFIUTATO DA {interaction.user.display_name}"
        await interaction.message.edit(embed=embed_orig, view=self)


# --- Modale Cittadinanza ---
class ModalCittadinanza(discord.ui.Modal, title="🎃 Registrazione Cittadinanza"):
    nome_cognome = discord.ui.TextInput(label="📜 Nome e Cognome RP", placeholder="Es. Mario Rossi", required=True, max_length=40)
    roblox_user = discord.ui.TextInput(label="🎮 Username Roblox", placeholder="Es. MarioRoblox123", required=True, max_length=40)
    eta_rp = discord.ui.TextInput(label="🎂 Età RP", placeholder="Es. 25", required=True, max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        
        data = load_data()
        if "rp_names" not in data:
            data["rp_names"] = {}
        data["rp_names"][user_id_str] = self.nome_cognome.value.strip()
        save_data(data)

        canale_staff = interaction.guild.get_channel(ID_CANALE_ACCETTAZIONE_STAFF)
        if not canale_staff:
            await interaction.followup.send("❌ **Errore:** Canale staff per l'approvazione non trovato!", ephemeral=True)
            return

        embed = discord.Embed(
            title="📥 NUOVA RICHIESTA: CITTADINANZA",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 Utente Discord", value=interaction.user.mention, inline=True)
        embed.add_field(name="📜 Nome RP", value=f"`{self.nome_cognome.value}`", inline=True)
        embed.add_field(name="🎮 Account Roblox", value=f"`{self.roblox_user.value}`", inline=True)
        embed.add_field(name="🎂 Età RP", value=f"`{self.eta_rp.value} anni`", inline=True)

        view_staff = VistaApprovazioneStaff(
            tipo_documento="Cittadinanza",
            nome_rp=self.nome_cognome.value,
            roblox_user=self.roblox_user.value,
            eta_rp=self.eta_rp.value,
            target_user_id=interaction.user.id
        )

        await canale_staff.send(embed=embed, view=view_staff)
        await interaction.followup.send("🎃 **Richiesta di Cittadinanza inviata allo Staff per la revisione!** 👻", ephemeral=True)


# --- Modale Patente ---
class ModalPatente(discord.ui.Modal, title="🏎️ Licenza di Guida Spettrale"):
    nome_cognome = discord.ui.TextInput(label="📜 Nome e Cognome RP", placeholder="Es. Mario Rossi", required=True, max_length=40)
    roblox_user = discord.ui.TextInput(label="🎮 Username Roblox", placeholder="Es. MarioRoblox123", required=True, max_length=40)
    eta_rp = discord.ui.TextInput(label="🎂 Età RP", placeholder="Es. 25", required=True, max_length=10)
    categoria = discord.ui.TextInput(
        label="🚗 Categoria Patente (A, B, C o D)", 
        placeholder="A, B, C oppure D", 
        max_length=1, 
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id_str = str(interaction.user.id)
        data = load_data()
        rp_names = data.get("rp_names", {})

        if user_id_str not in rp_names:
            await interaction.followup.send(
                "🧙‍♂️ **Non hai ancora la Cittadinanza!** Devi prima compilare il modulo per la **Cittadinanza Ufficiale** 📜.",
                ephemeral=True
            )
            return

        nome_registrato = rp_names[user_id_str].lower()
        nome_inserito = self.nome_cognome.value.strip().lower()

        if nome_inserito != nome_registrato:
            await interaction.followup.send(
                f"🚫 **Nome RP Errato!**\nIl nome inserito (`{self.nome_cognome.value}`) non corrisponde a quello della tua Cittadinanza (`{rp_names[user_id_str]}`) 🧟‍♂️.",
                ephemeral=True
            )
            return

        cat_upper = self.categoria.value.strip().upper()
        if cat_upper not in ['A', 'B', 'C', 'D']:
            await interaction.followup.send(
                "❌ **Categoria Non Valida!** Puoi inserire solo una tra queste categorie: **A**, **B**, **C** o **D** 🏍️🚗🚛🚌.", 
                ephemeral=True
            )
            return

        canale_staff = interaction.guild.get_channel(ID_CANALE_ACCETTAZIONE_STAFF)
        if not canale_staff:
            await interaction.followup.send("❌ **Errore:** Canale staff per l'approvazione non trovato!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📥 NUOVA RICHIESTA: PATENTE {cat_upper}",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 Utente Discord", value=interaction.user.mention, inline=True)
        embed.add_field(name="📜 Nome RP", value=f"`{self.nome_cognome.value}`", inline=True)
        embed.add_field(name="🎮 Account Roblox", value=f"`{self.roblox_user.value}`", inline=True)
        embed.add_field(name="🎂 Età RP", value=f"`{self.eta_rp.value} anni`", inline=True)
        embed.add_field(name="🛞 Categoria", value=f"**Patente {cat_upper}**", inline=False)

        view_staff = VistaApprovazioneStaff(
            tipo_documento=f"Patente {cat_upper}",
            nome_rp=self.nome_cognome.value,
            roblox_user=self.roblox_user.value,
            eta_rp=self.eta_rp.value,
            cat_patente=cat_upper,
            target_user_id=interaction.user.id
        )

        await canale_staff.send(embed=embed, view=view_staff)
        await interaction.followup.send(f"🧟 **Richiesta per la Patente {cat_upper} inviata allo Staff per l'approvazione!** 🏁", ephemeral=True)


# --- Modale Porto d'Armi ---
class ModalPortoDArmi(discord.ui.Modal, title="🪦 Licenza Porto d'Armi Legale"):
    nome_cognome = discord.ui.TextInput(label="📜 Nome e Cognome RP", placeholder="Es. Mario Rossi", required=True, max_length=40)
    roblox_user = discord.ui.TextInput(label="🎮 Username Roblox", placeholder="Es. MarioRoblox123", required=True, max_length=40)
    eta_rp = discord.ui.TextInput(label="🎂 Età RP", placeholder="Es. 25", required=True, max_length=10)
    motivazione = discord.ui.TextInput(
        label="📋 Motivazione della Richiesta", 
        style=discord.TextStyle.paragraph, 
        placeholder="Spiega dettagliatamente il motivo della richiesta...", 
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id_str = str(interaction.user.id)
        data = load_data()
        rp_names = data.get("rp_names", {})

        if user_id_str not in rp_names:
            await interaction.followup.send(
                "🧙‍♂️ **Non hai ancora la Cittadinanza!** Devi prima compilare il modulo per la **Cittadinanza Ufficiale** 📜.",
                ephemeral=True
            )
            return

        nome_registrato = rp_names[user_id_str].lower()
        nome_inserito = self.nome_cognome.value.strip().lower()

        if nome_inserito != nome_registrato:
            await interaction.followup.send(
                f"🚫 **Nome RP Errato!**\nIl nome inserito (`{self.nome_cognome.value}`) non corrisponde a quello della tua Cittadinanza (`{rp_names[user_id_str]}`) 🧟‍♂️.",
                ephemeral=True
            )
            return

        canale_staff = interaction.guild.get_channel(ID_CANALE_ACCETTAZIONE_STAFF)
        if not canale_staff:
            await interaction.followup.send("❌ **Errore:** Canale staff per l'approvazione non trovato!", ephemeral=True)
            return

        embed = discord.Embed(
            title="📥 NUOVA RICHIESTA: PORTO D'ARMI",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 Utente Discord", value=interaction.user.mention, inline=True)
        embed.add_field(name="📜 Nome RP", value=f"`{self.nome_cognome.value}`", inline=True)
        embed.add_field(name="🎮 Account Roblox", value=f"`{self.roblox_user.value}`", inline=True)
        embed.add_field(name="🎂 Età RP", value=f"`{self.eta_rp.value} anni`", inline=True)
        embed.add_field(name="📋 Motivazione RP", value=f"```\n{self.motivazione.value}\n```", inline=False)

        view_staff = VistaApprovazioneStaff(
            tipo_documento="Porto d'Armi",
            nome_rp=self.nome_cognome.value,
            roblox_user=self.roblox_user.value,
            eta_rp=self.eta_rp.value,
            motivazione=self.motivazione.value,
            target_user_id=interaction.user.id
        )

        await canale_staff.send(embed=embed, view=view_staff)
        await interaction.followup.send("🩸 **Richiesta di Porto d'Armi inviata allo Staff per l'approvazione!** 🗡️", ephemeral=True)


# --- Vista dei Pulsanti ---
class VistaPannelloDocumenti(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cittadinanza Ufficiale", style=discord.ButtonStyle.primary, emoji="🎃", custom_id="btn_cittadinanza")
    async def btn_cittadinanza(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalCittadinanza())

    @discord.ui.button(label="Patente (A/B/C/D)", style=discord.ButtonStyle.success, emoji="🏎️", custom_id="btn_patente")
    async def btn_patente(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalPatente())

    @discord.ui.button(label="Porto d'Armi Legale", style=discord.ButtonStyle.danger, emoji="🪦", custom_id="btn_armi")
    async def btn_armi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalPortoDArmi())


# --- Comando Slash /pannello ---
@bot.tree.command(name="pannello", description="Manda il pannello principale per i documenti (Halloween Edition)")
@app_commands.checks.has_permissions(administrator=True)
async def pannello_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎃 CENTRO SERVIZI PUGLIA RP - HALLOWEEN EDITION 🏴‍☠️",
        description=(
            "🧟‍♂️ **Benvenuto nella Motorizzazione & Anagrafe Ufficiale!** 👻\n"
            "Clicca sui pulsanti in basso per inviare le tue richieste ufficiali.\n\n"
            "📜 **1. Cittadinanza Ufficiale** 🎃\n"
            "• **Descrizione:** Registrazione all'Anagrafe del server.\n"
            "• **Requisiti:** Inserisci Nome e Cognome RP realistici.\n\n"
            "🚗 **2. Licenza di Guida / Patenti (A, B, C, D)** 🏎️\n"
            "• **Descrizione:** Registrazione veicolo e licenza di guida.\n"
            "• **Categorie:** 🏍️ **A** (Moto) | 🚗 **B** (Auto) | 🚛 **C** (Camion) | 🚌 **D** (Bus)\n"
            "• **Nota:** Il Nome RP deve essere **identico** alla Cittadinanza!\n\n"
            "🔫 **3. Licenza Porto d'Armi** 🪦\n"
            "• **Descrizione:** Licenza per detenzione e uso armi legale.\n"
            "• **Requisiti:** Visita psicofisica idonea e motivazione RP.\n\n"
            "⚠️ **Regolamento e Note Importanti** 🕸️\n"
            "1️⃣ Assicurati di non possedere già il documento.\n"
            "2️⃣ In caso di **rifiuto**, attendere **10 minuti di cooldown** ⏳.\n"
            "3️⃣ Compila i moduli con serietà: no troll o nomi irrealistici 🍬."
        ),
        color=discord.Color.from_rgb(230, 126, 34)
    )

    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    embed.set_footer(
        text="🍂 Puglia RP - Sistema Automazione Documenti • Dolcetto o Scherzetto? 🎃",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    await interaction.response.send_message(embed=embed, view=VistaPannelloDocumenti())

# ==========================================
# 💳 MODULO: ECONOMIA & BANCA
# ==========================================
class ModalApriConto(discord.ui.Modal, title="🏦 Apertura Conto Corrente - Puglia RP"):
    nome_cognome = discord.ui.TextInput(label="Nome e Cognome RP", placeholder="Es. Mario Rossi", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        eco = get_user_eco(user_id_str)

        if eco.get("has_account"):
            await interaction.followup.send("❌ Possiedi già un conto corrente attivo!", ephemeral=True)
            return

        eco["bank"] += 1000
        eco["has_account"] = True
        update_user_eco(user_id_str, eco)

        embed = discord.Embed(
            title="🏦 CONTO BANCARIO APERTO CON SUCCESSO!",
            description=f"Congratulazioni **{self.nome_cognome.value}**!\n🎁 **Bonus Benvenuto:** `€ 1.000` accreditati.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


class VistaContoBancario(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💳 Apri Conto Bancario", style=discord.ButtonStyle.success, custom_id="btn_apri_conto")
    async def btn_apri_conto(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id_str = str(interaction.user.id)
        eco = get_user_eco(user_id_str)

        if eco.get("has_account"):
            await interaction.response.send_message("❌ Hai già aperto un conto corrente bancario!", ephemeral=True)
            return

        await interaction.response.send_modal(ModalApriConto())


@bot.tree.command(name="pannello-contobancario", description="Invia il pannello per l'apertura del conto bancario (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def pannello_conto_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏦 BANCA DI PUGLIA RP — APERTURA CONTO",
        description="Clicca sul pulsante sottostante per registrare il tuo conto corrente e ricevere subito **€ 1.000**!",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=VistaContoBancario())


@bot.tree.command(name="saldo", description="Visualizza il tuo saldo bancario e i contanti in tuo possesso")
async def saldo_cmd(interaction: discord.Interaction, utente: discord.Member = None):
    target = utente or interaction.user
    eco = get_user_eco(str(target.id))

    embed = discord.Embed(title=f"💰 PORTAFOGLIO & CONTO — {target.display_name}", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
    embed.add_field(name="💵 Contanti", value=f"`€ {eco['cash']:,}`", inline=True)
    embed.add_field(name="🏦 Saldo Bancario", value=f"`€ {eco['bank']:,}`", inline=True)
    embed.add_field(name="💳 Stato Conto", value="✅ Attivo" if eco["has_account"] else "❌ Non Attivo", inline=False)

    if target.display_avatar:
        embed.set_thumbnail(url=target.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="preleva", description="Preleva denaro dal tuo conto bancario per metterlo in contanti")
async def preleva_cmd(interaction: discord.Interaction, importo: int):
    if importo <= 0:
        await interaction.response.send_message("❌ Inserisci un importo valido!", ephemeral=True)
        return

    user_id_str = str(interaction.user.id)
    eco = get_user_eco(user_id_str)

    if not eco.get("has_account"):
        await interaction.response.send_message("❌ Non possiedi un conto bancario attivo!", ephemeral=True)
        return

    if eco["bank"] < importo:
        await interaction.response.send_message(f"❌ Saldo insufficiente (**€ {eco['bank']:,}**).", ephemeral=True)
        return

    eco["bank"] -= importo
    eco["cash"] += importo
    update_user_eco(user_id_str, eco)

    await interaction.response.send_message(
        f"🏧 **PRELIEVO EFFETTUATO!**\nHai prelevato **€ {importo:,}**.\n"
        f"• Saldo Banco: `€ {eco['bank']:,}`\n• Contanti: `€ {eco['cash']:,}`",
        ephemeral=True
    )


@bot.tree.command(name="deposita", description="Deposita contanti sul tuo conto corrente bancario")
async def deposita_cmd(interaction: discord.Interaction, importo: int):
    if importo <= 0:
        await interaction.response.send_message("❌ Inserisci un importo valido!", ephemeral=True)
        return

    user_id_str = str(interaction.user.id)
    eco = get_user_eco(user_id_str)

    if not eco.get("has_account"):
        await interaction.response.send_message("❌ Non possiedi un conto bancario attivo!", ephemeral=True)
        return

    if eco["cash"] < importo:
        await interaction.response.send_message(f"❌ Non hai abbastanza contanti (**€ {eco['cash']:,}**).", ephemeral=True)
        return

    eco["cash"] -= importo
    eco["bank"] += importo
    update_user_eco(user_id_str, eco)

    await interaction.response.send_message(
        f"🏦 **DEPOSITO EFFETTUATO!**\nHai versato **€ {importo:,}**.\n"
        f"• Saldo Banco: `€ {eco['bank']:,}`\n• Contanti: `€ {eco['cash']:,}`",
        ephemeral=True
    )


@bot.tree.command(name="paga", description="Paga o dai contanti ad un altro cittadino in RP")
async def paga_cmd(interaction: discord.Interaction, destinatario: discord.Member, importo: int):
    if destinatario.id == interaction.user.id:
        await interaction.response.send_message("❌ Non puoi pagare te stesso!", ephemeral=True)
        return

    if importo <= 0:
        await interaction.response.send_message("❌ Inserisci un importo valido!", ephemeral=True)
        return

    mittente_id = str(interaction.user.id)
    dest_id = str(destinatario.id)

    eco_mittente = get_user_eco(mittente_id)
    eco_dest = get_user_eco(dest_id)

    if eco_mittente["cash"] < importo:
        await interaction.response.send_message(f"❌ Non hai abbastanza contanti in tasca (**€ {eco_mittente['cash']:,}**).", ephemeral=True)
        return

    eco_mittente["cash"] -= importo
    eco_dest["cash"] += importo

    update_user_eco(mittente_id, eco_mittente)
    update_user_eco(dest_id, eco_dest)

    embed = discord.Embed(
        title="🤝 TRANSAZIONE IN CONTANTI",
        description=f"Hai consegnato con successo **€ {importo:,}** in contanti a {destinatario.mention}.",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="aggiungi-soldi", description="Aggiungi denaro a un utente (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(dove=[
    app_commands.Choice(name="🏦 Banca", value="bank"),
    app_commands.Choice(name="💵 Contanti", value="cash")
])
async def add_money_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int, dove: app_commands.Choice[str]):
    user_id_str = str(utente.id)
    eco = get_user_eco(user_id_str)

    eco[dove.value] += importo
    update_user_eco(user_id_str, eco)

    luogo = "Banca" if dove.value == "bank" else "Contanti"
    await interaction.response.send_message(f"✅ Aggiunti **€ {importo:,}** in **{luogo}** per {utente.mention}.", ephemeral=True)

# ==========================================
# 🆔 MODULO: IDENTIFICAZIONE STAFF & REVOCA
# ==========================================
class ModalIdentificazione(discord.ui.Modal, title="🆔 Registrazione Staffer"):
    roblox_name = discord.ui.TextInput(label="Nome Account Roblox", placeholder="Es. Player123", required=True)
    grado = discord.ui.TextInput(label="Grado Staff", placeholder="Es. Helper, Mod, Admin", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        data = load_data()

        data["users"][user_id_str] = {
            "roblox_name": self.roblox_name.value,
            "grado": self.grado.value,
            "data_registrazione": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_data(data)

        role = interaction.guild.get_role(ROLE_STAFF_BASE_ID)
        if role and role not in interaction.user.roles:
            try:
                await interaction.user.add_roles(role)
            except Exception as e:
                print(f"Errore ruolo: {e}")

        embed = discord.Embed(
            title="✅ IDENTIFICAZIONE COMPLETATA",
            description=f"Sei stato identificato come **{self.roblox_name.value}** ({self.grado.value}).",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="identificami", description="Apri il modulo di identificazione Staff di Puglia RP")
async def identificami_cmd(interaction: discord.Interaction):
    await interaction.response.send_modal(ModalIdentificazione())


@bot.tree.command(name="lista-staff", description="Mostra la lista di tutti i membri dello Staff identificati")
@app_commands.checks.has_permissions(administrator=True)
async def lista_staff_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    data = load_data()
    users = data.get("users", {})

    if not users:
        await interaction.followup.send("⚠️ Nessun membro dello staff salvato.", ephemeral=True)
        return

    embed = discord.Embed(title="📋 LISTA STAFF REGISTRATI", color=discord.Color.blue())
    for uid, info in users.items():
        member = interaction.guild.get_member(int(uid))
        mention = member.mention if member else f"ID: {uid}"
        embed.add_field(
            name=f"👤 {info.get('roblox_name', 'N/D')}",
            value=f"**Discord:** {mention}\n**Grado:** {info.get('grado', 'N/D')}",
            inline=False
        )
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="revoca", description="Revoca un documento o l'identificazione Staff ad un utente (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(utente="L'utente a cui revocare", tipo="Cosa revocare")
@app_commands.choices(tipo=[
    app_commands.Choice(name="🆔 Identificazione Staff", value="staff"),
    app_commands.Choice(name="🇮🇹 Cittadinanza", value="cittadinanza"),
    app_commands.Choice(name="🚗 Patente A", value="patente_a"),
    app_commands.Choice(name="🚗 Patente B", value="patente_b"),
    app_commands.Choice(name="🚗 Patente C", value="patente_c"),
    app_commands.Choice(name="🚗 Patente D", value="patente_d"),
    app_commands.Choice(name="🔫 Porto d'Armi", value="armi")
])
async def revoca_cmd(interaction: discord.Interaction, utente: discord.Member, tipo: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)

    if tipo.value == "staff":
        role_staff = interaction.guild.get_role(ROLE_STAFF_BASE_ID)
        if role_staff and role_staff in utente.roles:
            try:
                await utente.remove_roles(role_staff)
            except Exception:
                pass
        data = load_data()
        if str(utente.id) in data.get("users", {}):
            del data["users"][str(utente.id)]
            save_data(data)
        await interaction.followup.send(f"⚠️ Identificazione Staff revocata a {utente.mention}.", ephemeral=True)
        return

    ruolo_da_rimuovere = None
    if tipo.value == "cittadinanza":
        ruolo_da_rimuovere = interaction.guild.get_role(ID_RUOLO_CITTADINO)
    elif tipo.value.startswith("patente_"):
        lettera = tipo.value.split("_")[1].upper()
        ruolo_da_rimuovere = interaction.guild.get_role(RUOLI_PATENTI.get(lettera))
    elif tipo.value == "armi":
        ruolo_da_rimuovere = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)

    if ruolo_da_rimuovere and ruolo_da_rimuovere in utente.roles:
        try:
            await utente.remove_roles(ruolo_da_rimuovere)
        except Exception as e:
            print(f"Errore revoca: {e}")

    await interaction.followup.send(f"🚫 Revocato **{tipo.name}** a {utente.mention}.", ephemeral=True)

# ==========================================
# ⏱️ MODULO: GESTIONE SERVIZIO STAFF
# ==========================================
class VistaServizioStaff(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Entra in Servizio", style=discord.ButtonStyle.success, custom_id="btn_start_duty")
    async def btn_start_duty(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id_str = str(interaction.user.id)
        duty = get_user_duty(user_id_str)

        if duty.get("on_duty"):
            await interaction.response.send_message("⚠️ Sei già in servizio!", ephemeral=True)
            return

        duty["on_duty"] = True
        duty["last_start"] = datetime.datetime.now().timestamp()
        update_user_duty(user_id_str, duty)

        await interaction.response.send_message("🟢 **Sei entrato in Servizio Staff!** Buon lavoro.", ephemeral=True)

    @discord.ui.button(label="🔴 Esci dal Servizio", style=discord.ButtonStyle.danger, custom_id="btn_stop_duty")
    async def btn_stop_duty(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id_str = str(interaction.user.id)
        duty = get_user_duty(user_id_str)

        if not duty.get("on_duty"):
            await interaction.response.send_message("⚠️ Non sei in servizio al momento!", ephemeral=True)
            return

        now_ts = datetime.datetime.now().timestamp()
        session_seconds = now_ts - duty.get("last_start", now_ts)
        duty["total_seconds"] += session_seconds
        duty["on_duty"] = False
        duty["last_start"] = None
        update_user_duty(user_id_str, duty)

        ore = int(session_seconds // 3600)
        minuti = int((session_seconds % 3600) // 60)
        await interaction.response.send_message(f"🔴 **Sei uscito dal Servizio Staff.** Turno attuale: `{ore}h {minuti}m`.", ephemeral=True)


@bot.tree.command(name="servizio", description="Apri il tuo pannello personale di gestione Servizio Staff")
async def servizio_cmd(interaction: discord.Interaction):
    duty = get_user_duty(str(interaction.user.id))
    tot_sec = duty.get("total_seconds", 0)
    ore = int(tot_sec // 3600)
    minuti = int((tot_sec % 3600) // 60)
    stato = "🟢 In Servizio" if duty.get("on_duty") else "🔴 Non in Servizio"

    embed = discord.Embed(title=f"🛡️ GESTIONE SERVIZIO — {interaction.user.display_name}", color=discord.Color.purple())
    embed.add_field(name="📌 Stato Attuale", value=f"**{stato}**", inline=False)
    embed.add_field(name="⏱️ Ore Accumulate", value=f"`{ore} ore e {minuti} minuti`", inline=False)

    await interaction.response.send_message(embed=embed, view=VistaServizioStaff(), ephemeral=True)


@bot.tree.command(name="leaderboard-staff", description="Visualizza la classifica settimanale delle ore Staff")
async def leaderboard_staff_cmd(interaction: discord.Interaction):
    data = load_data()
    duty_data = data.get("duty", {})

    if not duty_data:
        await interaction.response.send_message("⚠️ Nessun dato presente per la classifica staff.", ephemeral=True)
        return

    sorted_staff = sorted(duty_data.items(), key=lambda x: x[1].get("total_seconds", 0), reverse=True)

    embed = discord.Embed(title="🏆 CLASSIFICA ORE SERVIZIO STAFF", color=discord.Color.gold())
    for i, (uid, info) in enumerate(sorted_staff[:10], 1):
        member = interaction.guild.get_member(int(uid))
        name = member.mention if member else f"ID: {uid}"
        sec = info.get("total_seconds", 0)
        ore = int(sec // 3600)
        min = int((sec % 3600) // 60)
        embed.add_field(name=f"#{i} {member.display_name if member else 'Staff'}", value=f"{name} — `{ore}h {min}m`", inline=False)

    await interaction.response.send_message(embed=embed)

# ==========================================
# 📢 MODULO: ANNUNCI SESSIONI RP
# ==========================================
@bot.tree.command(name="sessione", description="Annuncia l'apertura della sessione di Puglia RP con grafica avanzata")
@app_commands.checks.has_permissions(administrator=True)
async def sessione_cmd(interaction: discord.Interaction, orario: str = "ORA"):
    embed = discord.Embed(
        title="🌆 PUGLIA RP — SESSIONE APERTA!",
        description=f"La sessione di gioco di **Puglia RP** è ufficialmente **ONLINE**!\n\n🕒 **Orario Apertura:** `{orario}`\n🎮 Entra subito nel server e rispetta il regolamento!",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.set_footer(text="Puglia RP • Sessione Ufficiale")

    await interaction.response.send_message("@everyone", embed=embed)


@bot.tree.command(name="sessione-offline", description="Manda direttamente l'annuncio di sessione offline")
@app_commands.checks.has_permissions(administrator=True)
async def sessione_offline_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌙 PUGLIA RP — SESSIONE CHIUSA",
        description="La sessione di gioco è giunta al termine.\nGrazie a tutti i cittadini e allo Staff per la partecipazione!",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    await interaction.response.send_message(embed=embed)

# ==========================================
# ⭐ MODULO: RECENSIONS STAFF (FORUM)
# ==========================================
@bot.tree.command(name="recensisci-staff", description="Invia una recensione per un membro dello Staff di Puglia RP")
@app_commands.describe(staffer="Lo staffer da recensire", valutazione="Valutazione 1-10", motivo="Motivazione")
@app_commands.choices(valutazione=[
    app_commands.Choice(name="⭐ 1 / 10", value=1),
    app_commands.Choice(name="⭐⭐ 2 / 10", value=2),
    app_commands.Choice(name="⭐⭐⭐ 3 / 10", value=3),
    app_commands.Choice(name="⭐⭐⭐⭐ 4 / 10", value=4),
    app_commands.Choice(name="⭐⭐⭐⭐⭐ 5 / 10", value=5),
    app_commands.Choice(name="⭐⭐⭐⭐⭐⭐ 6 / 10", value=6),
    app_commands.Choice(name="⭐⭐⭐⭐⭐⭐⭐ 7 / 10", value=7),
    app_commands.Choice(name="⭐⭐⭐⭐⭐⭐⭐⭐ 8 / 10", value=8),
    app_commands.Choice(name="⭐⭐⭐⭐⭐⭐⭐⭐⭐ 9 / 10", value=9),
    app_commands.Choice(name="🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟 10 / 10", value=10)
])
async def recensisci_staff_cmd(interaction: discord.Interaction, staffer: discord.Member, valutazione: app_commands.Choice[int], motivo: str):
    if interaction.channel.id != ID_CANALE_COMANDO_RECENSIONI:
        await interaction.response.send_message(f"❌ Puoi rilasciare recensioni solo in <#{ID_CANALE_COMANDO_RECENSIONI}>.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    forum_channel = interaction.guild.get_channel(ID_CANALE_LOG_RECENSIONI)

    if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
        await interaction.followup.send("❌ Canale Forum recensioni non trovato.", ephemeral=True)
        return

    stelle_grafiche = "⭐" * valutazione.value
    embed = discord.Embed(
        title="🌟 NUOVA RECENSIONE STAFF — PUGLIA RP 🌟",
        color=discord.Color.from_rgb(230, 126, 34),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="👮 Staffer", value=staffer.mention, inline=True)
    embed.add_field(name="👤 Utente", value=interaction.user.mention, inline=True)
    embed.add_field(name="⭐ Valutazione", value=f"**{valutazione.value}/10**\n{stelle_grafiche}", inline=False)
    embed.add_field(name="💬 Motivazione", value=f"```{motivo}```", inline=False)

    if staffer.display_avatar:
        embed.set_thumbnail(url=staffer.display_avatar.url)
    if LINK_IMMAGINE_RECENSIONE:
        embed.set_image(url=LINK_IMMAGINE_RECENSIONE)

    titolo_post = f"⭐ [{valutazione.value}/10] Recensione Staff - {staffer.display_name}"
    try:
        await forum_channel.create_thread(name=titolo_post, embed=embed)
        await interaction.followup.send(f"✅ Recensione pubblicata nel Forum per {staffer.mention}!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Errore invio forum: `{e}`", ephemeral=True)

# ==========================================
# 🚨 MODULO: ARRESTI & MULTE
# ==========================================
@bot.tree.command(name="arresta", description="Emetti un mandato di arresto per un utente")
@app_commands.describe(utente="L'utente da arrestare", durata="Durata della pena", motivo="Motivazione dell'arresto")
async def arresta_cmd(interaction: discord.Interaction, utente: discord.Member, durata: str, motivo: str):
    await interaction.response.defer(ephemeral=True)
    canale_arresti = interaction.guild.get_channel(ID_CANALE_REGISTRO_ARRESTI)
    if not canale_arresti:
        await interaction.followup.send("❌ Canale registro arresti non trovato!", ephemeral=True)
        return

    embed = discord.Embed(title="🚨 REGISTRO ARRESTI — PUGLIA RP", color=discord.Color.dark_red(), timestamp=discord.utils.utcnow())
    embed.add_field(name="👤 Utente", value=utente.mention, inline=True)
    embed.add_field(name="👮 Agente/Staff", value=interaction.user.mention, inline=True)
    embed.add_field(name="⏱️ Durata", value=f"`{durata}`", inline=False)
    embed.add_field(name="📋 Motivazione", value=f"```{motivo}```", inline=False)

    if utente.display_avatar:
        embed.set_thumbnail(url=utente.display_avatar.url)

    await canale_arresti.send(embed=embed)
    await interaction.followup.send(f"✅ Arresto registrato per {utente.mention}.", ephemeral=True)


@bot.tree.command(name="multa", description="Emetti una sanzione pecuniaria (multa) a un utente")
@app_commands.describe(utente="L'utente da multare", importo="Importo sanzione", motivo="Motivazione della multa")
async def multa_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int, motivo: str):
    await interaction.response.defer(ephemeral=True)
    canale_multe = interaction.guild.get_channel(ID_CANALE_REGISTRO_MULTE)
    if not canale_multe:
        await interaction.followup.send("❌ Canale registro multe non trovato!", ephemeral=True)
        return

    embed = discord.Embed(title="💸 NOTIFICA DI SANZIONE / MULTA — PUGLIA RP", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
    embed.add_field(name="👤 Sanzionato", value=utente.mention, inline=True)
    embed.add_field(name="👮 Emessa da", value=interaction.user.mention, inline=True)
    embed.add_field(name="💰 Importo", value=f"**€ {importo:,}**", inline=False)
    embed.add_field(name="📋 Motivazione", value=f"```{motivo}```", inline=False)

    if utente.display_avatar:
        embed.set_thumbnail(url=utente.display_avatar.url)

    await canale_multe.send(embed=embed)
    await interaction.followup.send(f"✅ Multa di **€ {importo}** emessa a {utente.mention}.", ephemeral=True)

# ==========================================
# 👥 MODULO: LISTA PLAYER (STAFF)
# ==========================================
@bot.tree.command(name="lista-player", description="Visualizza l'elenco e il conteggio dei player online e offline nel server")
async def lista_player_cmd(interaction: discord.Interaction):
    role_staff = interaction.guild.get_role(ROLE_STAFF_BASE_ID)
    if role_staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ **Comando riservato allo Staff di Puglia RP!**", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    online_members = []
    offline_members = []

    for member in guild.members:
        if member.bot:
            continue
        if member.status != discord.Status.offline:
            online_members.append(member)
        else:
            offline_members.append(member)

    total_players = len(online_members) + len(offline_members)

    online_str = ", ".join([m.mention for m in online_members[:15]]) if online_members else "Nessuno"
    if len(online_members) > 15:
        online_str += f" ...e altri {len(online_members) - 15}"

    offline_str = ", ".join([m.mention for m in offline_members[:15]]) if offline_members else "Nessuno"
    if len(offline_members) > 15:
        offline_str += f" ...e altri {len(offline_members) - 15}"

    embed = discord.Embed(
        title="📊 STATO PLAYER — PUGLIA RP",
        description=f"👥 **Totale Cittadini nel Server:** `{total_players}`",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(name=f"🟢 Online / Attivi (`{len(online_members)}`)", value=online_str, inline=False)
    embed.add_field(name=f"⚪ Offline (`{len(offline_members)}`)", value=offline_str, inline=False)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.set_footer(text="Puglia RP • Pannello Riservato Staff", icon_url=interaction.user.display_avatar.url)

    await interaction.followup.send(embed=embed, ephemeral=True)

# ==========================================
# 🚀 EVENTO ON_READY & AVVIO BOT
# ==========================================
@bot.event
async def on_ready():
    print(f'🤖 Bot connesso come {bot.user}')
    
    bot.add_view(VistaPannelloDocumenti())
    bot.add_view(VistaContoBancario())
    bot.add_view(VistaServizioStaff())

    try:
        synced = await bot.tree.sync()
        print(f"⚡ Sincronizzati {len(synced)} comandi slash a livello globale!")

        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)

    except Exception as e:
        print(f"❌ Errore sincronizzazione: {e}")

    print('✅ Il bot di Puglia RP è ONLINE e pronto!')

keep_alive()

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ERRORE: DISCORD_TOKEN non trovato!")
