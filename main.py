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

ID_CANALE_COMANDO_RECENSIONI = 1563156712679145502  # Sostituisci con l'ID del canale recensioni
ID_CANALE_LOG_RECENSIONI = 1563194331320557768     # Canale Forum Recensioni
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
# --- Vista con Bottoni Accetta / Rifiuta per lo Staff ---
class VistaApprovazioneStaff(discord.ui.View):
    def __init__(self, tipo_documento, nome_rp, roblox_user, eta_rp=None, cat_patente=None, modello_veicolo=None, targa_veicolo=None, tipo_arma=None, motivazione=None, target_user_id=None):
        super().__init__(timeout=None)
        self.tipo_documento = tipo_documento
        self.nome_rp = nome_rp
        self.roblox_user = roblox_user
        self.eta_rp = eta_rp
        self.cat_patente = cat_patente
        self.modello_veicolo = modello_veicolo
        self.targa_veicolo = targa_veicolo
        self.tipo_arma = tipo_arma
        self.motivazione = motivazione
        self.target_user_id = target_user_id

    @discord.ui.button(label="Accetta Documento", style=discord.ButtonStyle.success, emoji="🟢", custom_id="btn_accetta_doc")
    async def btn_accetta(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_staff = interaction.guild.get_role(ROLE_STAFF_BASE_ID)
        if role_staff not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ **Solo lo Staff può accettare i documenti!**", ephemeral=True)
            return

        await interaction.response.defer()

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
            if self.eta_rp:
                embed_forum.add_field(name="🎂 Età RP", value=f"`{self.eta_rp} anni`", inline=True)
            
            if self.cat_patente:
                embed_forum.add_field(name="🚗 Categoria", value=f"**Patente {self.cat_patente}**", inline=True)
            if self.modello_veicolo:
                embed_forum.add_field(name="🚘 Modello Veicolo", value=f"`{self.modello_veicolo}`", inline=True)
            if self.targa_veicolo:
                embed_forum.add_field(name="🔢 Targa Veicolo", value=f"`{self.targa_veicolo}`", inline=True)
            if self.tipo_arma:
                embed_forum.add_field(name="🔫 Tipo di Arma", value=f"`{self.tipo_arma}`", inline=True)
            if self.motivazione:
                embed_forum.add_field(name="📋 Motivazione", value=f"```\n{self.motivazione}\n```", inline=False)

            embed_forum.add_field(name="👮 Approvato da", value=interaction.user.mention, inline=False)

            titolo_post = f"✅ [{self.tipo_documento}] {self.nome_rp}"
            try:
                await forum.create_thread(name=titolo_post, embed=embed_forum)
            except Exception as e:
                print(f"Errore creazione post forum: {e}")

        # Assegnazione automatica del ruolo
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
        user_id_str = str(interaction.user.id)
        data = load_data()
        cittadinanze = data.get("cittadinanze", {})
        ruolo_cittadino = interaction.guild.get_role(ID_RUOLO_CITTADINO)

        # 🚫 Controllo se possiede già la Cittadinanza
        if (ruolo_cittadino and ruolo_cittadino in interaction.user.roles) or user_id_str in cittadinanze:
            await interaction.response.send_message(
                "⚠️ **Possiedi già la Cittadinanza Ufficiale!** Non puoi richiederne un'altra.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Salva TUTTI i dati della Cittadinanza nel database
        if "cittadinanze" not in data:
            data["cittadinanze"] = {}
            
        data["cittadinanze"][user_id_str] = {
            "nome_rp": self.nome_cognome.value.strip(),
            "roblox_user": self.roblox_user.value.strip(),
            "eta_rp": self.eta_rp.value.strip()
        }
        
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


# --- Modale Patente (Ordinata e Senza Roblox) ---
class ModalPatente(discord.ui.Modal, title="🏎️ Licenza di Guida Spettrale"):
    nome_cognome = discord.ui.TextInput(
        label="📜 Nome e Cognome RP", 
        placeholder="Es. Mario Rossi", 
        required=True, 
        max_length=40
    )
    categoria = discord.ui.TextInput(
        label="🚗 Categoria Patente (A, B, C o D)", 
        placeholder="A, B, C oppure D", 
        max_length=1, 
        required=True
    )
    modello_veicolo = discord.ui.TextInput(
        label="🚘 Modello Veicolo", 
        placeholder="Es. Wolfsburg Marin", 
        required=True, 
        max_length=40
    )
    targa_veicolo = discord.ui.TextInput(
        label="🔢 Targa Veicolo", 
        placeholder="Es. AB/CD/10", 
        required=True, 
        max_length=15
    )
    motivazione = discord.ui.TextInput(
        label="📋 Motivazione della Richiesta", 
        placeholder="Es. Per uso lavorativo", 
        required=True, 
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        cat_upper = self.categoria.value.strip().upper()

        # 1. Controllo Categoria (A, B, C, D)
        if cat_upper not in ['A', 'B', 'C', 'D']:
            await interaction.response.send_message(
                "❌ **Categoria Non Valida!** Inserisci solo la lettera **A**, **B**, **C** oppure **D** 🏍️🚗🚛🚌.", 
                ephemeral=True
            )
            return

        # 2. Controllo Possesso Ruolo Patente
        ruolo_patente_id = RUOLI_PATENTI.get(cat_upper)
        ruolo_patente = interaction.guild.get_role(ruolo_patente_id) if ruolo_patente_id else None

        if ruolo_patente and ruolo_patente in interaction.user.roles:
            await interaction.response.send_message(
                f"⚠️ **Possiedi già la Patente Categoria {cat_upper}!** Non puoi richiederla nuovamente.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        user_id_str = str(interaction.user.id)
        data = load_data()
        cittadinanze = data.get("cittadinanze", {})

        # 3. Verifico la presenza della Cittadinanza
        if user_id_str not in cittadinanze:
            await interaction.followup.send(
                "🧙‍♂️ **Non hai ancora compilato la Cittadinanza!** Devi prima inviare il modulo per la **Cittadinanza Ufficiale** 📜.",
                ephemeral=True
            )
            return

        dati_reg = cittadinanze[user_id_str]
        
        # 4. Controllo corrispondenza Nome RP
        if self.nome_cognome.value.strip().lower() != dati_reg["nome_rp"].lower():
            await interaction.followup.send(
                "❌ **Nome RP non corrispondente alla Cittadinanza!**\n"
                f"Il nome inserito deve essere identico a quello registrato: `{dati_reg['nome_rp']}`.",
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
        embed.add_field(name="🎮 Account Roblox", value=f"`{dati_reg.get('roblox_user', 'N/D')}`", inline=True)
        embed.add_field(name="🛞 Categoria", value=f"**Patente {cat_upper}**", inline=True)
        embed.add_field(name="🚘 Modello Veicolo", value=f"`{self.modello_veicolo.value}`", inline=True)
        embed.add_field(name="🔢 Targa Veicolo", value=f"`{self.targa_veicolo.value}`", inline=True)
        embed.add_field(name="📋 Motivazione", value=f"```\n{self.motivazione.value}\n```", inline=False)

        view_staff = VistaApprovazioneStaff(
            tipo_documento=f"Patente {cat_upper}",
            nome_rp=self.nome_cognome.value,
            roblox_user=dati_reg.get('roblox_user', 'N/D'),
            cat_patente=cat_upper,
            modello_veicolo=self.modello_veicolo.value,
            targa_veicolo=self.targa_veicolo.value,
            motivazione=self.motivazione.value,
            target_user_id=interaction.user.id
        )

        await canale_staff.send(embed=embed, view=view_staff)
        await interaction.followup.send(f"🧟 **Richiesta per la Patente {cat_upper} inviata allo Staff per l'approvazione!** 🏁", ephemeral=True)


# --- Modale Porto d'Armi (Con Tipo di Arma) ---
class ModalPortoDArmi(discord.ui.Modal, title="🪦 Licenza Porto d'Armi Legale"):
    nome_cognome = discord.ui.TextInput(label="📜 Nome e Cognome RP", placeholder="Es. Mario Rossi", required=True, max_length=40)
    roblox_user = discord.ui.TextInput(label="🎮 Username Roblox", placeholder="Es. MarioRoblox123", required=True, max_length=40)
    tipo_arma = discord.ui.TextInput(label="🔫 Tipo di Arma", placeholder="Es. Glock-17", required=True, max_length=40)
    motivazione = discord.ui.TextInput(
        label="📋 Motivazione della Richiesta", 
        style=discord.TextStyle.paragraph, 
        placeholder="Spiega dettagliatamente il motivo della richiesta...", 
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        ruolo_armi = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)
        if ruolo_armi and ruolo_armi in interaction.user.roles:
            await interaction.response.send_message(
                "⚠️ **Possiedi già la Licenza del Porto d'Armi!** Non puoi richiederla nuovamente.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        user_id_str = str(interaction.user.id)
        data = load_data()
        cittadinanze = data.get("cittadinanze", {})

        if user_id_str not in cittadinanze:
            await interaction.followup.send(
                "🧙‍♂️ **Non hai ancora compilato la Cittadinanza!** Devi prima inviare il modulo per la **Cittadinanza Ufficiale** 📜.",
                ephemeral=True
            )
            return

        dati_reg = cittadinanze[user_id_str]
        
        nome_errato = self.nome_cognome.value.strip().lower() != dati_reg["nome_rp"].lower()
        roblox_errato = self.roblox_user.value.strip().lower() != dati_reg["roblox_user"].lower()

        if nome_errato or roblox_errato:
            await interaction.followup.send(
                "❌ **Dati non corrispondenti alla Cittadinanza!**\n"
                "I dati inseriti devono essere **identici** a quelli inviati nella tua Cittadinanza Ufficiale:\n"
                f"• **Nome RP salvato:** `{dati_reg['nome_rp']}`\n"
                f"• **Account Roblox salvato:** `{dati_reg['roblox_user']}`",
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
        embed.add_field(name="🔫 Tipo di Arma", value=f"`{self.tipo_arma.value}`", inline=True)
        embed.add_field(name="📋 Motivazione RP", value=f"```\n{self.motivazione.value}\n```", inline=False)

        view_staff = VistaApprovazioneStaff(
            tipo_documento="Porto d'Armi",
            nome_rp=self.nome_cognome.value,
            roblox_user=self.roblox_user.value,
            tipo_arma=self.tipo_arma.value,
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
# 💸 MODULO ECONOMIA AVANZATO (CITTADINI & STAFF)
# ==========================================

# 1. /portafoglio (e /soldi)
@bot.tree.command(name="portafoglio", description="Visualizza il tuo saldo attuale (o quello di un altro utente se sei Staff)")
@app_commands.describe(utente="L'utente di cui vuoi verificare il saldo (Solo per lo Staff)")
async def portafoglio_cmd(interaction: discord.Interaction, utente: discord.Member = None):
    await interaction.response.defer(ephemeral=True)

    # Se l'utente specifica un altro utente, controlliamo che sia Staff
    if utente and utente.id != interaction.user.id:
        if not interaction.user.guild_permissions.manage_messages:  # Permesso Staff base
            await interaction.followup.send("❌ **Solo i membri dello Staff** possono visualizzare il portafoglio degli altri utenti!", ephemeral=True)
            return
        target_user = utente
    else:
        target_user = interaction.user

    user_id_str = str(target_user.id)
    eco = get_user_eco(user_id_str)

    embed = discord.Embed(
        title=f"💳 ESTRATTO CONTO — {target_user.display_name}",
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="💵 Portafoglio (Contanti)", value=f"`€ {eco['cash']:,}`", inline=True)
    
    if eco.get("has_account"):
        embed.add_field(name="🏦 Conto Bancario", value=f"`€ {eco['bank']:,}`", inline=True)
    else:
        embed.add_field(name="🏦 Conto Bancario", value="`Non Posseduto ❌`", inline=True)

    if target_user.display_avatar:
        embed.set_thumbnail(url=target_user.display_avatar.url)

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="soldi", description="Alias per visualizzare il portafoglio")
@app_commands.describe(utente="L'utente di cui vuoi verificare il saldo (Solo per lo Staff)")
async def soldi_cmd(interaction: discord.Interaction, utente: discord.Member = None):
    await portafoglio_cmd(interaction, utente)


# 2. /paga (Scambio Contanti)
@bot.tree.command(name="paga", description="Paga o dai contanti ad un altro cittadino")
@app_commands.describe(utente="Il cittadino da pagare", importo="Quantità di contanti da dare")
async def paga_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ L'importo deve essere maggiore di zero!", ephemeral=True)
        return

    if utente.id == interaction.user.id:
        await interaction.followup.send("❌ Non puoi pagare te stesso!", ephemeral=True)
        return

    mittente_eco = get_user_eco(str(interaction.user.id))

    if mittente_eco["cash"] < importo:
        await interaction.followup.send("❌ **Contanti insufficienti!** Non hai abbastanza soldi in portafoglio.", ephemeral=True)
        return

    ricevente_eco = get_user_eco(str(utente.id))

    mittente_eco["cash"] -= importo
    ricevente_eco["cash"] += importo

    update_user_eco(str(interaction.user.id), mittente_eco)
    update_user_eco(str(utente.id), ricevente_eco)

    await interaction.followup.send(f"💵 Hai dato **€ {importo:,}** in contanti a {utente.mention}!", ephemeral=True)


# 3. /bonifico (Trasferimento Bancario)
@bot.tree.command(name="bonifico", description="Effettua un bonifico bancario ad un altro cittadino")
@app_commands.describe(utente="Il destinatario del bonifico", importo="Importo da inviare")
async def bonifico_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ L'importo deve essere maggiore di zero!", ephemeral=True)
        return

    if utente.id == interaction.user.id:
        await interaction.followup.send("❌ Non puoi fare un bonifico a te stesso!", ephemeral=True)
        return

    mittente_eco = get_user_eco(str(interaction.user.id))
    if not mittente_eco.get("has_account"):
        await interaction.followup.send("❌ Non puoi fare bonifici perché non possiedi un conto corrente bancario!", ephemeral=True)
        return

    ricevente_eco = get_user_eco(str(utente.id))
    if not ricevente_eco.get("has_account"):
        await interaction.followup.send(f"❌ {utente.mention} non possiede un conto corrente bancario attivo!", ephemeral=True)
        return

    if mittente_eco["bank"] < importo:
        await interaction.followup.send("❌ **Fondi bancari insufficienti!**", ephemeral=True)
        return

    mittente_eco["bank"] -= importo
    ricevente_eco["bank"] += importo

    update_user_eco(str(interaction.user.id), mittente_eco)
    update_user_eco(str(utente.id), ricevente_eco)

    await interaction.followup.send(f"🏛️ Bonifico bancario di **€ {importo:,}** inviato con successo a {utente.mention}!", ephemeral=True)


# 4. /preleva (Da Banca a Contanti)
@bot.tree.command(name="preleva", description="Preleva fondi dal tuo conto bancario trasformandoli in contanti")
@app_commands.describe(importo="Importo da prelevare")
async def preleva_cmd(interaction: discord.Interaction, importo: int):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ L'importo deve essere maggiore di zero!", ephemeral=True)
        return

    user_id_str = str(interaction.user.id)
    eco = get_user_eco(user_id_str)

    if not eco.get("has_account"):
        await interaction.followup.send("❌ Non possiedi un conto corrente bancario!", ephemeral=True)
        return

    if eco["bank"] < importo:
        await interaction.followup.send("❌ **Fondi insufficienti in banca!**", ephemeral=True)
        return

    eco["bank"] -= importo
    eco["cash"] += importo
    update_user_eco(user_id_str, eco)

    await interaction.followup.send(f"🏧 Hai prelevato **€ {importo:,}** dal tuo conto bancario! Ora sono nel tuo portafoglio.", ephemeral=True)


# 5. /deposita (Da Contanti a Banca)
@bot.tree.command(name="deposita", description="Versa i contanti dal tuo portafoglio al tuo conto bancario")
@app_commands.describe(importo="Importo da depositare")
async def deposita_cmd(interaction: discord.Interaction, importo: int):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ L'importo deve essere maggiore di zero!", ephemeral=True)
        return

    user_id_str = str(interaction.user.id)
    eco = get_user_eco(user_id_str)

    if not eco.get("has_account"):
        await interaction.followup.send("❌ Non possiedi un conto corrente bancario dove depositare il denaro!", ephemeral=True)
        return

    if eco["cash"] < importo:
        await interaction.followup.send("❌ **Contanti insufficienti nel tuo portafoglio!**", ephemeral=True)
        return

    eco["cash"] -= importo
    eco["bank"] += importo
    update_user_eco(user_id_str, eco)

    await interaction.followup.send(f"📥 Hai depositato **€ {importo:,}** sul tuo conto bancario!", ephemeral=True)


# 6. /aggiungi-soldi (Solo Staff)
@bot.tree.command(name="aggiungi-soldi", description="Aggiungi soldi ad un utente in Banca o in Contanti (Solo Staff)")
@app_commands.describe(utente="L'utente a cui aggiungere denaro", importo="Importo da aggiungere", dove="Dove aggiungere i soldi")
@app_commands.choices(dove=[
    app_commands.Choice(name="💵 Portafoglio (Contanti)", value="cash"),
    app_commands.Choice(name="🏦 Conto Bancario", value="bank")
])
@app_commands.checks.has_permissions(manage_messages=True)
async def aggiungi_soldi_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int, dove: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ L'importo deve essere maggiore di zero!", ephemeral=True)
        return

    user_id_str = str(utente.id)
    eco = get_user_eco(user_id_str)

    if dove.value == "bank" and not eco.get("has_account"):
        await interaction.followup.send(f"❌ {utente.mention} non ha un conto corrente attivo!", ephemeral=True)
        return

    eco[dove.value] += importo
    update_user_eco(user_id_str, eco)

    dove_testo = "Portafoglio" if dove.value == "cash" else "Conto Bancario"
    await interaction.followup.send(f"✅ Aggiunti **€ {importo:,}** in **{dove_testo}** a {utente.mention}!", ephemeral=True)


# 7. /rimuovi-soldi (Solo Staff)
@bot.tree.command(name="rimuovi-soldi", description="Rimuovi soldi ad un utente da Banca o Contanti (Solo Staff)")
@app_commands.describe(utente="L'utente a cui rimuovere denaro", importo="Importo da rimuovere", dove="Da dove rimuovere i soldi")
@app_commands.choices(dove=[
    app_commands.Choice(name="💵 Portafoglio (Contanti)", value="cash"),
    app_commands.Choice(name="🏦 Conto Bancario", value="bank")
])
@app_commands.checks.has_permissions(manage_messages=True)
async def rimuovi_soldi_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int, dove: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ L'importo deve essere maggiore di zero!", ephemeral=True)
        return

    user_id_str = str(utente.id)
    eco = get_user_eco(user_id_str)

    eco[dove.value] -= importo
    update_user_eco(user_id_str, eco)

    dove_testo = "Portafoglio" if dove.value == "cash" else "Conto Bancario"
    await interaction.followup.send(f"✅ Rimossi **€ {importo:,}** dal **{dove_testo}** di {utente.mention}!", ephemeral=True)

# ==========================================
# 💳 MODULO: ECONOMIA, BANCA & MULTE
# ==========================================

class ModalApriConto(discord.ui.Modal, title="🏦 Apertura Conto Corrente"):
    nome_cognome = discord.ui.TextInput(label="📜 Nome e Cognome RP", placeholder="Es. Mario Rossi", required=True, max_length=40)
    eta_rp = discord.ui.TextInput(label="🎂 Età RP", placeholder="Es. 25", required=True, max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        data = load_data()
        cittadinanze = data.get("cittadinanze", {})
        rp_names = data.get("rp_names", {})

        # 1. Controlliamo se l'utente ha la Cittadinanza registrata
        if user_id_str not in cittadinanze and user_id_str not in rp_names:
            await interaction.followup.send(
                "🧙‍♂️ **Non hai ancora la Cittadinanza!** Devi prima compilare il modulo nel canale apposito "
                f"<#1562891119824601258> per ottenere la **Cittadinanza Ufficiale** prima di poter aprire un conto bancario 📜.",
                ephemeral=True
            )
            return

        # 2. Recuperiamo il Nome RP registrato ufficialmente
        if user_id_str in cittadinanze:
            nome_rp_registrato = cittadinanze[user_id_str].get("nome_rp", "").strip()
        else:
            nome_rp_registrato = rp_names.get(user_id_str, "").strip()

        # 3. Controllo Corrispondenza Nome RP
        nome_inserito = self.nome_cognome.value.strip()
        if nome_inserito.lower() != nome_rp_registrato.lower():
            await interaction.followup.send(
                "❌ **Nome RP Errato o non corrispondente!**\n"
                f"Il nome inserito (`{nome_inserito}`) non corrisponde a quello della tua Cittadinanza Ufficiale (`{nome_rp_registrato}`).\n"
                "Inserisci il Nome e Cognome RP esatto!",
                ephemeral=True
            )
            return

        # 4. Controllo se possiede già il conto bancario
        eco = get_user_eco(user_id_str)
        if eco.get("has_account"):
            await interaction.followup.send("❌ Possiedi già un conto corrente attivo!", ephemeral=True)
            return

        # 5. Attivazione Conto + Accredito Bonus
        eco["bank"] += 1000
        eco["has_account"] = True
        update_user_eco(user_id_str, eco)

        embed = discord.Embed(
            title="🏦 CONTO BANCARIO APERTO CON SUCCESSO! 💰",
            description=f"Congratulazioni **{nome_rp_registrato}** ({self.eta_rp.value} anni)!\n🎁 **Bonus Benvenuto:** `€ 1.000` accreditati sul tuo nuovo conto.",
            color=discord.Color.from_rgb(46, 204, 113),
            timestamp=discord.utils.utcnow()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


class VistaContoBancario(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apri Conto Bancario", style=discord.ButtonStyle.success, emoji="💳", custom_id="btn_apri_conto")
    async def btn_apri_conto(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Apriamo SUBITO la modale senza attendere controlli di rete per evitare "Unknown interaction"
        await interaction.response.send_modal(ModalApriConto())


@bot.tree.command(name="pannello-contobancario", description="Invia il nuovo pannello per l'apertura del conto bancario (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def pannello_conto_cmd(interaction: discord.Interaction):
    # Notifichiamo subito a Discord che l'operazione è in corso
    await interaction.response.defer()

    embed = discord.Embed(
        title="🏦 BANCA DI PUGLIA RP — SERVIZI FINANZIARI 🏴‍☠️",
        description=(
            "🧟‍♂️ **Benvenuto allo sportello bancario ufficiale!** 👻\n\n"
            "📋 **Requisiti per l'apertura:**\n"
            "• Possedere la **Cittadinanza Ufficiale** approvata 📜.\n"
            "• Inserire i propri dati anagrafici corretti in RP.\n\n"
            "🎁 **Vantaggi immediati:**\n"
            "Ricevi subito **€ 1.000** di bonus benvenuto sul tuo nuovo conto corrente!\n\n"
            "👇 *Clicca sul pulsante sottostante per procedere.*"
        ),
        color=discord.Color.from_rgb(230, 126, 34),
        timestamp=discord.utils.utcnow()
    )
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.set_footer(text="Puglia RP • Gestione Finanziaria Sicura 💳", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    await interaction.followup.send(embed=embed, view=VistaContoBancario())

# ==========================================
# 💸 MODULO: MULTE AVANZATE (BANCA / CONTANTI + NEGATIVO)
# ==========================================
@bot.tree.command(name="multa", description="Emetti una sanzione pecuniaria scalando i fondi da Banca o Contanti")
@app_commands.describe(
    utente="L'utente da multare", 
    importo="Importo della multa", 
    fonte="Da dove prelevare i soldi", 
    motivo="Motivazione della multa"
)
@app_commands.choices(fonte=[
    app_commands.Choice(name="🏦 Conto Bancario (Banca)", value="bank"),
    app_commands.Choice(name="💵 Portafoglio (Contanti)", value="cash")
])
async def multa_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int, fonte: app_commands.Choice[str], motivo: str):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ L'importo della multa deve essere maggiore di zero!", ephemeral=True)
        return

    user_id_str = str(utente.id)
    eco = get_user_eco(user_id_str)

    # 1. Controllo se sceglie la Banca ma non ha il conto
    if fonte.value == "bank" and not eco.get("has_account"):
        await interaction.followup.send(
            f"❌ **Impossibile emettere la multa!** {utente.mention} **non possiede un conto bancario attivo**, quindi non è possibile scalare i fondi dalla banca.",
            ephemeral=True
        )
        return

    # 2. Scaliamo i soldi (permettendo anche l'andata in negativo)
    eco[fonte.value] -= importo
    update_user_eco(user_id_str, eco)

    # 3. Invio nel canale registro multe
    canale_multe = interaction.guild.get_channel(ID_CANALE_REGISTRO_MULTE)
    if canale_multe:
        embed_log = discord.Embed(
            title="💸 NOTIFICA DI SANZIONE / MULTA — PUGLIA RP",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed_log.add_field(name="👤 Sanzionato", value=utente.mention, inline=True)
        embed_log.add_field(name="👮 Emessa da", value=interaction.user.mention, inline=True)
        embed_log.add_field(name="💰 Importo", value=f"**€ {importo:,}**", inline=True)
        embed_log.add_field(name="📍 Prelevato da", value="🏦 Conto Bancario" if fonte.value == "bank" else "💵 Portafoglio", inline=True)
        embed_log.add_field(name="📊 Saldo Residuo Utente", value=f"• Banca: `€ {eco['bank']:,}`\n• Contanti: `€ {eco['cash']:,}`", inline=False)
        embed_log.add_field(name="📋 Motivazione", value=f"```{motivo}```", inline=False)

        if utente.display_avatar:
            embed_log.set_thumbnail(url=utente.display_avatar.url)

        await canale_multe.send(embed=embed_log)

    fonte_testo = "Conto Bancario" if fonte.value == "bank" else "Portafoglio"
    await interaction.followup.send(
        f"✅ Multa di **€ {importo:,}** emessa con successo a {utente.mention} (prelevata da **{fonte_testo}**).\n"
        f"Nuovo saldo utente: 🏦 `€ {eco['bank']:,}` | 💵 `€ {eco['cash']:,}`",
        ephemeral=True
    )

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

    user_id_str = str(utente.id)
    data = load_data()

    # 1. Revoca Identificazione Staff
    if tipo.value == "staff":
        role_staff = interaction.guild.get_role(ROLE_STAFF_BASE_ID)
        if role_staff and role_staff in utente.roles:
            try:
                await utente.remove_roles(role_staff)
            except Exception as e:
                print(f"Errore rimozione ruolo staff: {e}")

        if user_id_str in data.get("users", {}):
            del data["users"][user_id_str]
            save_data(data)

        await interaction.followup.send(f"⚠️ **Identificazione Staff revocata** a {utente.mention}.", ephemeral=True)
        return

    # Helper avanzato per cercare ed eliminare il post nel Forum
    async def elimina_post_forum(parola_chiave_tipo):
        forum = interaction.guild.get_channel(ID_FORUM_DOCUMENTI)
        eliminati_count = 0
        if forum and isinstance(forum, discord.ForumChannel):
            try:
                threads = list(forum.threads)
                async for archived_thread in forum.archived_threads(limit=100):
                    threads.append(archived_thread)

                for thread in threads:
                    # Verifica che il tipo di documento sia nel titolo del post
                    if parola_chiave_tipo.lower() in thread.name.lower():
                        # Cerca il primo messaggio inviato nel thread per verificare la menzione/ID utente
                        async for msg in thread.history(limit=1, oldest_first=True):
                            # Controllo tramite menzione, ID o embed
                            trovato = False
                            if utente.mention in msg.content or str(utente.id) in msg.content:
                                trovato = True
                            elif msg.embeds:
                                embed_text = str(msg.embeds[0].to_dict())
                                if str(utente.id) in embed_text or utente.mention in embed_text:
                                    trovato = True

                            if trovato:
                                try:
                                    await thread.delete()
                                    eliminati_count += 1
                                except Exception as e:
                                    print(f"Errore eliminazione thread {thread.id}: {e}")
                                break

            except Exception as e:
                print(f"Errore scansione forum: {e}")
        return eliminati_count

    # 2. Revoca Cittadinanza
    if tipo.value == "cittadinanza":
        ruolo_cittadino = interaction.guild.get_role(ID_RUOLO_CITTADINO)
        if ruolo_cittadino and ruolo_cittadino in utente.roles:
            try:
                await utente.remove_roles(ruolo_cittadino)
            except Exception as e:
                print(f"Errore rimozione ruolo cittadino: {e}")

        if "cittadinanze" in data and user_id_str in data["cittadinanze"]:
            del data["cittadinanze"][user_id_str]
        if "rp_names" in data and user_id_str in data["rp_names"]:
            del data["rp_names"][user_id_str]
        save_data(data)

        num_eliminati = await elimina_post_forum("Cittadinanza")
        msg_post = f" 🗑️ **Post Cittadinanza eliminato dal Forum!**" if num_eliminati > 0 else " ⚠️ *(Nessun post trovato nel Forum per la Cittadinanza)*."
        await interaction.followup.send(f"🚫 **Cittadinanza revocata** a {utente.mention}.{msg_post}", ephemeral=True)
        return

    # 3. Revoca Patenti
    if tipo.value.startswith("patente_"):
        lettera = tipo.value.split("_")[1].upper()
        ruolo_id = RUOLI_PATENTI.get(lettera)
        if ruolo_id:
            ruolo_patente = interaction.guild.get_role(ruolo_id)
            if ruolo_patente and ruolo_patente in utente.roles:
                try:
                    await utente.remove_roles(ruolo_patente)
                except Exception as e:
                    print(f"Errore revoca patente: {e}")

        num_eliminati = await elimina_post_forum(f"Patente {lettera}")
        msg_post = f" 🗑️ **Post Patente {lettera} eliminato dal Forum!**" if num_eliminati > 0 else f" ⚠️ *(Nessun post trovato per Patente {lettera})*."
        await interaction.followup.send(f"🚫 **Patente {lettera} revocata** a {utente.mention}.{msg_post}", ephemeral=True)
        return

    # 4. Revoca Porto d'Armi
    if tipo.value == "armi":
        ruolo_armi = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)
        if ruolo_armi and ruolo_armi in utente.roles:
            try:
                await utente.remove_roles(ruolo_armi)
            except Exception as e:
                print(f"Errore revoca porto d'armi: {e}")

        num_eliminati = await elimina_post_forum("Porto d'Armi")
        msg_post = f" 🗑️ **Post Porto d'Armi eliminato dal Forum!**" if num_eliminati > 0 else " ⚠️ *(Nessun post trovato per Porto d'Armi)*."
        await interaction.followup.send(f"🚫 **Porto d'Armi revocato** a {utente.mention}.{msg_post}", ephemeral=True)
        return

    # 3. Revoca Patenti o Porto d'Armi
    ruolo_da_rimuovere = None
    if tipo.value.startswith("patente_"):
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
# ⭐ MODULO: RECENSIONI STAFF (HALLOWEEN/AUTUMN EDITION)
# ==========================================
@bot.tree.command(name="recensisci-staff", description="Invia una recensione per un membro dello Staff di Puglia RP")
@app_commands.describe(staffer="Menziona lo staffer da recensire", valutazione="Valutazione da 1 a 10 stelle", motivo="Motivazione della recensione")
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
    # 1. Verifico che il comando sia eseguito nel canale dedicato
    if interaction.channel.id != ID_CANALE_COMANDO_RECENSIONI:
        await interaction.response.send_message(
            f"❌ **Canale Errato!** Puoi inviare recensioni solo nel canale <#{ID_CANALE_COMANDO_RECENSIONI}>.", 
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    forum_channel = interaction.guild.get_channel(ID_CANALE_LOG_RECENSIONI)

    if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
        await interaction.followup.send("❌ **Errore:** Canale Forum delle recensioni non trovato!", ephemeral=True)
        return

    # 2. Generazione grafica delle stelle
    stelle_grafiche = "⭐" * valutazione.value

    # 3. Creazione Embed Elegante
    embed = discord.Embed(
        title="🌟 NUOVA RECENSIONE STAFF — PUGLIA RP 🌟",
        color=discord.Color.from_rgb(230, 126, 34),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="👮 Staffer Valutato", value=staffer.mention, inline=True)
    embed.add_field(name="👤 Recensione da", value=interaction.user.mention, inline=True)
    embed.add_field(name="⭐ Valutazione", value=f"**{valutazione.value} / 10**\n{stelle_grafiche}", inline=False)
    embed.add_field(name="💬 Motivazione", value=f"```\n{motivo}\n```", inline=False)

    if staffer.display_avatar:
        embed.set_thumbnail(url=staffer.display_avatar.url)
    
    # Inserimento Immagine Grafica Ufficiale
    if LINK_IMMAGINE_RECENSIONE:
        embed.set_image(url=LINK_IMMAGINE_RECENSIONE)

    embed.set_footer(text="Puglia RP • Sistema Recensioni Ufficiale", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    # 4. Creazione Thread nel Forum
    titolo_post = f"⭐ [{valutazione.value}/10] Recensione - {staffer.display_name}"
    
    try:
        await forum_channel.create_thread(name=titolo_post, embed=embed)
        await interaction.followup.send(f"✅ **Recensione pubblicata con successo per {staffer.mention}!**", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Errore durante la pubblicazione nel forum: `{e}`", ephemeral=True)

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
# 📌 SETUP EMBED INFORMATIVO RECENSIONI STAFF
# ==========================================
@bot.tree.command(name="setup-recensioni", description="Invia l'embed informativo nel canale recensioni (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_recensioni_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    canale_recensioni = interaction.guild.get_channel(1563156712679145502)
    if not canale_recensioni:
        await interaction.followup.send("❌ **Errore:** Canale `1563156712679145502` non trovato!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🌟 PUGLIA RP — RECENSIONI STAFF 🍂🎃",
        description=(
            "✨ **Vuoi valutare l'operato del nostro Staff?**\n"
            "La tua opinione è fondamentale per aiutarci a migliorare la qualità del Roleplay e premiare i membri dello Staff più attivi e disponibili! 🛡️⚡\n\n"
            "─────────────────────────────\n\n"
            "📝 **COME INVIARE UNA RECENSIONE:**\n\n"
            "Usa il comando ufficiale `/recensisci-staff` e completa tutti i campi richiesti:\n\n"
            "🔹 **`staffer:`** `@Membro_Staff` *(Menziona lo staffer che vuoi valutare)*\n"
            "🔹 **`valutazione:`** `1 - 10 Stelle` *(Seleziona il voto da 1 a 10)*\n"
            "🔹 **`motivo:`** `Scrivi qui il tuo messaggio` *(Spiega in dettaglio l'esperienza)*\n\n"
            "─────────────────────────────\n\n"
            "📌 **Esempio Pratico:**\n"
            "```text\n"
            "/recensisci-staff staffer: @MarioRossi valutazione: 10 / 10 motivo: Ottimo supporto durante il ticket, veloce e super gentile!\n"
            "```\n"
            "⚠️ *Tutte le recensioni valide verranno pubblicate automaticamente nell'Anagrafe/Forum delle Recensioni! Non usare il comando per scherzi o troll.* 🚫"
        ),
        color=discord.Color.from_rgb(230, 126, 34),  # Arancione Halloween/Autunno
        timestamp=discord.utils.utcnow()
    )

    # Impostazione Grafica Ufficiale Puglia RP
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    # Immagine Banner Ufficiale Puglia RP Recensione Staff
    embed.set_image(url="https://media.discordapp.net/attachments/1561284670883242086/1563156338580652072/1792755906447.jpg")
    embed.set_footer(text="Puglia RP • Valuta il nostro Staff 👑", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    await canale_recensioni.send(embed=embed)
    await interaction.followup.send(f"✅ **Embed informativo inviato con successo in** <#1563156712679145502>!", ephemeral=True)

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
