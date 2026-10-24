import os
import json
import asyncio
import datetime
from flask import Flask
from threading import Thread

import discord
from discord import app_commands
from discord.ext import commands, tasks

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
ID_RUOLO_FDO = 1563276863462178956
ID_RUOLO_STAFF = 1562507751975035065

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
ID_FORUM_STAFF_IDENTIFICATI = 1563176554786463894
ID_CANALE_LOG_DOCUMENTI = 1562891209675116544 
ID_FORUM_STAFF_IDENTIFICATI = 1563176554786463894

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
# 🛠️ GESTIONE SERVIZIO E LEADERBOARD STAFF
# ==========================================

# Struttura temporanea in memoria per il tempo attivo
# staff_turni = { user_id: { "inizio": datetime, "pausa_inizio": datetime, "stato": "attivo"/"in_pausa" } }
staff_turni = {}


class VistaServizioStaff(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Apri Servizio", style=discord.ButtonStyle.success, custom_id="btn_apri_servizio")
    async def apri_servizio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        data = load_data()

        # 1. Controllo Obbligatorio Identificazione Staff
        staff_data = data.get("staff_identificati", {})
        if user_id_str not in staff_data:
            await interaction.followup.send(
                "❌ **Non sei identificato come Staff!** Devi prima completare l'identificazione tramite `/identificami` prima di poter andare in servizio.",
                ephemeral=True
            )
            return

        if user_id_str in staff_turni:
            await interaction.followup.send("⚠️ Sei già in servizio!", ephemeral=True)
            return

        # Avvio del turno
        ora_attuale = datetime.now(timezone.utc)
        staff_turni[user_id_str] = {
            "inizio": ora_attuale,
            "pausa_totale_secondi": 0,
            "pausa_inizio": None,
            "stato": "attivo"
        }

        # Log nel canale Log Staff
        canale_log = interaction.guild.get_channel(ID_CANALE_LOG_STAFF)
        if canale_log:
            embed_log = discord.Embed(
                title="🟢 ENTRATA IN SERVIZIO STAFF",
                description=f"👮 **Staffer:** {interaction.user.mention}\n🆔 **Roblox Username:** `{staff_data[user_id_str]['roblox_user']}`\n⏰ **Ora Inizio:** <t:{int(ora_attuale.timestamp())}:T>",
                color=discord.Color.green(),
                timestamp=ora_attuale
            )
            roblox_id = staff_data[user_id_str].get("roblox_id")
            if roblox_id:
                embed_log.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={roblox_id}&width=420&height=420&format=png")
            await canale_log.send(embed=embed_log)

        await interaction.followup.send("✅ **Sei entrato in servizio con successo!** Buona guardia.", ephemeral=True)


    @discord.ui.button(label="⏸️ Metti in Pausa", style=discord.ButtonStyle.secondary, custom_id="btn_pausa_servizio")
    async def pausa_servizio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)

        if user_id_str not in staff_turni:
            await interaction.followup.send("❌ Non sei attualmente in servizio!", ephemeral=True)
            return

        turno = staff_turni[user_id_str]
        ora_attuale = datetime.now(timezone.utc)

        if turno["stato"] == "attivo":
            turno["stato"] = "in_pausa"
            turno["pausa_inizio"] = ora_attuale
            msg = "⏸️ **Servizio messo in pausa.**"
        else:
            # Ripresa dalla pausa
            durata_pausa = (ora_attuale - turno["pausa_inizio"]).total_seconds()
            turno["pausa_totale_secondi"] += durata_pausa
            turno["stato"] = "attivo"
            turno["pausa_inizio"] = None
            msg = "▶️ **Servizio ripreso dalla pausa!**"

        # Log in canale Log Staff
        canale_log = interaction.guild.get_channel(ID_CANALE_LOG_STAFF)
        if canale_log:
            embed_log = discord.Embed(
                title="⏸️ CAMBIO STATO SERVIZIO STAFF",
                description=f"👮 **Staffer:** {interaction.user.mention}\n📌 **Stato:** `{turno['stato'].upper()}`\n⏰ **Ora:** <t:{int(ora_attuale.timestamp())}:T>",
                color=discord.Color.gold(),
                timestamp=ora_attuale
            )
            await canale_log.send(embed=embed_log)

        await interaction.followup.send(msg, ephemeral=True)


    @discord.ui.button(label="🔴 Chiudi Servizio", style=discord.ButtonStyle.danger, custom_id="btn_chiudi_servizio")
    async def chiudi_servizio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)

        if user_id_str not in staff_turni:
            await interaction.followup.send("❌ Non sei in servizio!", ephemeral=True)
            return

        turno = staff_turni.pop(user_id_str)
        ora_attuale = datetime.now(timezone.utc)

        # Se era in pausa al momento della chiusura, calcoliamo la pausa finale
        if turno["stato"] == "in_pausa" and turno["pausa_inizio"]:
            turno["pausa_totale_secondi"] += (ora_attuale - turno["pausa_inizio"]).total_seconds()

        tempo_totale_secondi = (ora_attuale - turno["inizio"]).total_seconds()
        tempo_effettivo_secondi = max(0, tempo_totale_secondi - turno["pausa_totale_secondi"])
        minuti_fatti = int(tempo_effettivo_secondi // 60)

        # Salvataggio dati e aggiornamento ore
        data = load_data()
        leaderboard = data.get("leaderboard_staff", {})
        leaderboard[user_id_str] = leaderboard.get(user_id_str, 0) + minuti_fatti
        data["leaderboard_staff"] = leaderboard
        save_data(data)

        # Log Chiusura
        canale_log = interaction.guild.get_channel(ID_CANALE_LOG_STAFF)
        if canale_log:
            ore = minuti_fatti // 60
            minuti = minuti_fatti % 60
            embed_log = discord.Embed(
                title="🔴 USCITA DAL SERVIZIO STAFF",
                description=(
                    f"👮 **Staffer:** {interaction.user.mention}\n"
                    f"⏱️ **Tempo Effettivo:** `{ore}h {minuti}m` ({minuti_fatti} min)\n"
                    f"⏰ **Ora Chiusura:** <t:{int(ora_attuale.timestamp())}:T>"
                ),
                color=discord.Color.red(),
                timestamp=ora_attuale
            )
            await canale_log.send(embed=embed_log)

        await aggiorna_leaderboard_embed(interaction.guild)
        await interaction.followup.send(f"✅ **Servizio concluso.** Hai registrato `{minuti_fatti}` minuti di servizio!", ephemeral=True)


# ==========================================
# 📊 AGGIORNAMENTO LEADERBOARD AUTOMATICA
# ==========================================
async def aggiorna_leaderboard_embed(guild: discord.Guild):
    canale = guild.get_channel(ID_CANALE_LEADERBOARD)
    if not canale:
        return

    data = load_data()
    leaderboard = data.get("leaderboard_staff", {})

    # Ordina per minuti di servizio decrescenti
    classifica_ordinata = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 CLASSIFICA SETTIMANALE ORE STAFF — PUGLIA RP 🎃",
        description="I minuti di servizio si aggiornano automaticamente alla chiusura di ogni turno.\n*Si resetta ogni Lunedì a 00:00.*\n\n",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc)
    )

    if not classifica_ordinata:
        embed.description += "*Nessun dato di servizio registrato per questa settimana.*"
    else:
        testo = ""
        medaglie = ["🥇", "🥈", "🥉"]
        for idx, (u_id, minuti) in enumerate(classifica_ordinata[:10], start=1):
            icona = medaglie[idx-1] if idx <= 3 else f"`#{idx}`"
            ore = minuti // 60
            m_res = minuti % 60
            testo += f"{icona} <@{u_id}> — **{ore}h {m_res}m** (`{minuti}` min)\n"
        embed.add_field(name="📋 Top Staffer della Settimana", value=testo, inline=False)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="Puglia RP • Reset automatico il Lunedì a mezzanotte")

    # Cerca un messaggio esistente del bot per modificarlo, altrimenti lo invia
    async for msg in canale.history(limit=10):
        if msg.author == guild.me and msg.embeds and "CLASSIFICA SETTIMANALE" in msg.embeds[0].title:
            await msg.edit(embed=embed)
            return

    await canale.send(embed=embed)


# ==========================================
# ⏰ TASK AUTOMATICO: RESET LUNEDÌ MEZZANOTTE
# ==========================================
@tasks.loop(minutes=1)
async def task_reset_settimanale():
    ora_ora = datetime.now(timezone.utc)
    # Lunedì = 0, Ora = 00:00
    if ora_ora.weekday() == 0 and ora_ora.hour == 0 and ora_ora.minute == 0:
        data = load_data()
        data["leaderboard_staff"] = {}
        save_data(data)

        for guild in bot.guilds:
            canale = guild.get_channel(ID_CANALE_LEADERBOARD)
            if canale:
                await canale.send("🔄 **RESET SETTIMANALE ESEGUITO!** La classifica ore staff è stata resettata per la nuova settimana.")
                await aggiorna_leaderboard_embed(guild)

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
# ❌ COMANDO /REVOCA (RIFATTO E COMPLETO)
# ==========================================
@bot.tree.command(name="revoca", description="Revoca licenze, patenti, cittadinanza o status ad un utente")
@app_commands.describe(utente="L'utente a cui revocare il documento/licenza", tipo="Cosa vuoi revocare?")
@app_commands.choices(tipo=[
    app_commands.Choice(name="🚗 Patente A (Moto)", value="patente_a"),
    app_commands.Choice(name="🚙 Patente B (Auto)", value="patente_b"),
    app_commands.Choice(name="🚛 Patente C (Camion)", value="patente_c"),
    app_commands.Choice(name="🚌 Patente D (Autobus)", value="patente_d"),
    app_commands.Choice(name="🔫 Porto d'Armi", value="porto_darmi"),
    app_commands.Choice(name="🇮🇹 Cittadinanza", value="cittadinanza"),
    app_commands.Choice(name="🏦 Conto Bancario / Documenti", value="documenti"),
    app_commands.Choice(name="🛡️ Identificazione Staff", value="staff")
])
async def revoca_cmd(interaction: discord.Interaction, utente: discord.Member, tipo: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)

    try:
        # 1. Controllo Permessi (Staff vs FDO)
        is_staff = any(role.id == ID_RUOLO_STAFF for role in interaction.user.roles) or interaction.user.guild_permissions.administrator
        is_fdo = any(role.id == ID_RUOLO_FDO for role in interaction.user.roles)
        
        licenze_fdo = ["patente_a", "patente_b", "patente_c", "patente_d", "porto_darmi"]

        if not is_staff and not is_fdo:
            await interaction.followup.send("❌ Non hai i permessi necessari per utilizzare questo comando!", ephemeral=True)
            return

        if is_fdo and not is_staff and tipo.value not in licenze_fdo:
            await interaction.followup.send("⚠️ Come membro delle **FDO** puoi revocare solamente le **Patenti** e il **Porto d'Armi**!", ephemeral=True)
            return

        user_id_str = str(utente.id)
        data = load_data()
        
        licenze_data = data.setdefault("licenze_cittadini", {})
        user_licenze = licenze_data.setdefault(user_id_str, {
            "patente_a": False, "patente_b": False, "patente_c": False, "patente_d": False,
            "porto_darmi": False, "cittadinanza": True
        })

        messaggio = ""
        modificato = False

        # --- REVOCA PATENTI (A, B, C, D) ---
        if tipo.value in RUOLI_PATENTI:
            role_id = RUOLI_PATENTI[tipo.value]
            user_licenze[tipo.value] = False
            modificato = True
            messaggio = f"✅ **{tipo.name}** revocata con successo a {utente.mention}!"

            # Rimuove il ruolo Discord della patente se presente
            ruolo = interaction.guild.get_role(role_id)
            if ruolo and ruolo in utente.roles:
                try:
                    await utente.remove_roles(ruolo, reason="Patente revocata")
                except Exception:
                    pass

        # --- REVOCA PORTO D'ARMI ---
        elif tipo.value == "porto_darmi":
            user_licenze["porto_darmi"] = False
            modificato = True
            messaggio = f"✅ **Porto d'Armi** revocato con successo a {utente.mention}!"
            
            ruolo = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)
            if ruolo and ruolo in utente.roles:
                try:
                    await utente.remove_roles(ruolo, reason="Porto d'armi revocato")
                except Exception:
                    pass

        # --- REVOCA CITTADINANZA ---
        elif tipo.value == "cittadinanza":
            user_licenze["cittadinanza"] = False
            modificato = True
            messaggio = f"✅ **Cittadinanza** revocata con successo a {utente.mention}!"

            ruolo = interaction.guild.get_role(ID_RUOLO_CITTADINO)
            if ruolo and ruolo in utente.roles:
                try:
                    await utente.remove_roles(ruolo, reason="Cittadinanza revocata")
                except Exception:
                    pass

        # --- REVOCA CONTO BANCARIO / DOCUMENTI ---
        elif tipo.value == "documenti":
            eco_data = data.setdefault("economia", {}).setdefault(user_id_str, {})
            eco_data["has_account"] = False
            eco_data["bank"] = 0
            modificato = True
            messaggio = f"✅ Conto bancario e documenti revocati a {utente.mention}!"

        # --- REVOCA IDENTIFICAZIONE STAFF & FORUM ---
        elif tipo.value == "staff":
            staff_data = data.get("identificazioni_staff", {})
            info_staff = staff_data.pop(user_id_str, None)
            data["identificazioni_staff"] = staff_data
            modificato = True
            messaggio = f"✅ L'identificazione Staff di {utente.mention} è stata revocata con successo!"

            # Rimuove ruolo Staff
            ruolo = interaction.guild.get_role(ID_RUOLO_STAFF)
            if ruolo and ruolo in utente.roles:
                try:
                    await utente.remove_roles(ruolo, reason="Identificazione Staff revocata")
                except Exception:
                    pass

            # Cancella il post dal Forum Staff
            if info_staff:
                try:
                    forum_channel = interaction.guild.get_channel(ID_FORUM_STAFF_IDENTIFICATI)
                    if forum_channel and isinstance(forum_channel, discord.ForumChannel):
                        roblox_user = info_staff.get("roblox_user", "")
                        for thread in forum_channel.threads:
                            if roblox_user and roblox_user.lower() in thread.name.lower():
                                await thread.delete()
                                messaggio += "\n🗑️ *Post nel forum Staff eliminato automaticamente.*"
                                break
                except Exception:
                    pass

        if modificato:
            save_data(data)

        await interaction.followup.send(messaggio, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Si è verificato un errore: `{e}`", ephemeral=True)

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
# 📝 MODALE IDENTIFICAZIONE STAFF (Senza ID Numerico)
# ==========================================
class ModalIdentificami(discord.ui.Modal, title="🆔 Identificazione Staff Puglia RP"):
    roblox_user = discord.ui.TextInput(label="🎮 Username Roblox", placeholder="Es. Player123", required=True, max_length=40)
    nome_rp = discord.ui.TextInput(label="👤 Nome e Cognome RP", placeholder="Es. Mario Rossi", required=True, max_length=50)
    ruolo_staff = discord.ui.TextInput(label="🛡️ Ruolo / Grado Staff", placeholder="Es. Trial / Helper / Admin", required=True, max_length=30)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        canale_log = interaction.guild.get_channel(ID_CANALE_LOG_DOCUMENTI)
        if not canale_log:
            await interaction.followup.send("❌ Canale log documenti non trovato!", ephemeral=True)
            return

        username_clean = self.roblox_user.value.strip()

        # Recupero automatico dell'ID Roblox tramite API
        roblox_id = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://users.roblox.com/v1/usernames/users",
                    json={"usernames": [username_clean], "excludeBannedUsers": False}
                ) as resp:
                    if resp.status == 200:
                        res_data = await resp.json()
                        if res_data.get("data"):
                            roblox_id = str(res_data["data"][0]["id"])
        except Exception:
            roblox_id = None

        embed_richiesta = discord.Embed(
            title="📥 NUOVA RICHIESTA IDENTIFICAZIONE STAFF",
            description=(
                f"👤 **Utente Discord:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"🎮 **Username Roblox:** `{username_clean}`\n"
                f"👤 **Nome RP:** `{self.nome_rp.value.strip()}`\n"
                f"🛡️ **Ruolo Dichiarato:** `{self.ruolo_staff.value.strip()}`"
            ),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )

        if roblox_id:
            embed_richiesta.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={roblox_id}&width=420&height=420&format=png")

        embed_richiesta.set_footer(text="Richiesta in attesa di approvazione Staff/Admin")

        vista = VistaApprovazioneIdentificazione(
            user_id=str(interaction.user.id),
            roblox_user=username_clean,
            roblox_id=roblox_id or "",
            nome_rp=self.nome_rp.value.strip(),
            ruolo_staff=self.ruolo_staff.value.strip()
        )
        await canale_log.send(embed=embed_richiesta, view=vista)

        await interaction.followup.send("✅ **Modulo inviato con successo!** La tua identificazione è in attesa di verifica dallo Staff.", ephemeral=True)


# ==========================================
# 🔘 VISTA APPROVAZIONE IDENTIFICAZIONE
# ==========================================
class VistaApprovazioneIdentificazione(discord.ui.View):
    def __init__(self, user_id: str, roblox_user: str, roblox_id: str, nome_rp: str, ruolo_staff: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.roblox_user = roblox_user
        self.roblox_id = roblox_id
        self.nome_rp = nome_rp
        self.ruolo_staff = ruolo_staff

    @discord.ui.button(label="✅ Accetta", style=discord.ButtonStyle.success, custom_id="btn_accetta_identificazione")
    async def accetta(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        data = load_data()
        if "identificazioni_staff" not in data:
            data["identificazioni_staff"] = {}

        data["identificazioni_staff"][self.user_id] = {
            "roblox_user": self.roblox_user,
            "roblox_id": self.roblox_id,
            "nome_rp": self.nome_rp,
            "ruolo": self.ruolo_staff,
            "approvato_da": str(interaction.user.id)
        }
        save_data(data)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ IDENTIFICAZIONE STAFF APPROVATA"
        embed.set_footer(text=f"Approvato da {interaction.user.display_name}")

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)

        # 📌 POST AUTOMATICO NEL FORUM STAFF
        forum_channel = interaction.guild.get_channel(ID_FORUM_STAFF_IDENTIFICATI)
        if forum_channel and isinstance(forum_channel, discord.ForumChannel):
            embed_forum = discord.Embed(
                title=f"🛡️ STAFF IDENTIFICATO — {self.roblox_user}",
                description=(
                    f"👤 **Membro Staff:** <@{self.user_id}>\n"
                    f"🎮 **Username Roblox:** `{self.roblox_user}`\n"
                    f"👤 **Nome RP:** `{self.nome_rp}`\n"
                    f"🎖️ **Grado Staff:** `{self.ruolo_staff}`\n\n"
                    "✅ *Identificazione ufficiale registrata nel database di Puglia RP.*"
                ),
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            if self.roblox_id:
                embed_forum.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={self.roblox_id}&width=420&height=420&format=png")

            await forum_channel.create_thread(
                name=f"🛡️丨{self.roblox_user} ({self.ruolo_staff})",
                embed=embed_forum
            )

        try:
            target_member = interaction.guild.get_member(int(self.user_id))
            if target_member:
                await target_member.send(f"🎉 **Complimenti!** La tua identificazione Staff come **{self.roblox_user}** è stata approvata!")
        except Exception:
            pass

    @discord.ui.button(label="❌ Rifiuta", style=discord.ButtonStyle.danger, custom_id="btn_rifiuta_identificazione")
    async def rifiuta(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ IDENTIFICAZIONE STAFF RIFIUTATA"
        embed.set_footer(text=f"Rifiutato da {interaction.user.display_name}")

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)


# ==========================================
# 📌 COMANDO /IDENTIFICAMI
# ==========================================
@bot.tree.command(name="identificami", description="Apri il modulo di identificazione Staff di Puglia RP")
async def identificami_cmd(interaction: discord.Interaction):
    await interaction.response.send_modal(ModalIdentificami())
    

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
