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

# ==========================================
# 📌 CONFIGURAZIONE ID RUOLI E CANALI
# ==========================================
ID_RUOLO_CITTADINO = 1562894350135066674
ID_RUOLO_PORTO_DARMI = 1562894902428442695
ID_RUOLO_FDO = 1563276863462178956
ID_RUOLO_STAFF = 1562507751975035065
ID_RUOLO_ASSICURATO = 1563488413875834890

ID_RUOLO_PATENTI = {
    'patente_a': 1562894624597479555,
    'patente_b': 1562894703081431090,
    'patente_c': 1562894760878800897,
    'patente_d': 1562894822983860364
}

ID_FORUM_DOCUMENTI = 1562891782415450183

ID_CANALE_COMANDO_RECENSIONI = 1563156712679145502  # Sostituisci con l'ID del canale recensioni
ID_CANALE_LOG_RECENSIONI = 1563194331320557768     # Canale Forum Recensioni
LINK_IMMAGINE_RECENSIONE = "https://media.discordapp.net/attachments/1561284670883242086/1563156338580652072/1792755906447.jpg?ex=6adc9a49&is=6adb48c9&hm=889b0be762da4780fd7225ff6632c4ae457b26a5d1b1f6bfdadb3c413816c642&=&format=webp"

ID_CANALE_REGISTRO_ARRESTI = 1524685772995690607
ID_CANALE_REGISTRO_MULTE = 1563215066411696299
ID_CANALE_CONTO_BANCARIO = 1563216017851949227
ID_FORUM_STAFF_IDENTIFICATI = 1563176554786463894
ID_FORUM_STAFF_IDENTIFICATI = 1563176554786463894
ID_CANALE_LOG_DOCUMENTI = 1562891209675116544  # Canale Accettazione / Log Documenti
ID_FORUM_DOCUMENTI = 1562891782415450183       # Forum Schede Documenti

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

# ==========================================
# 🔘 VISTA APPROVAZIONE DOCUMENTI (PERSISTENTE)
# ==========================================
# ==========================================
# 🔘 VISTA APPROVAZIONE DOCUMENTI (DINAMICA & CORRETTA)
# ==========================================
class Documenti(discord.ui.View):
    def __init__(self, user_id: int, nome_rp: str, roblox_user: str, tipo_doc: str = "Cittadinanza"):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nome_rp = nome_rp
        self.roblox_user = roblox_user  # Usato come Modello + Targa se tipo_doc == "Assicurazione"
        self.tipo_doc = tipo_doc

    @discord.ui.button(label="Accetta Documento", style=discord.ButtonStyle.success, custom_id="btn_accetta_documento")
    async def accetta(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        try:
            data = load_data()
            user_id_str = str(self.user_id)
            licenze_data = data.setdefault("licenze_cittadini", {})
            user_lic = licenze_data.setdefault(user_id_str, {
                "patente_a": False, "patente_b": False, "patente_c": False, "patente_d": False,
                "porto_darmi": False, "cittadinanza": True, "assicurazione": False
            })

            tipo_upper = self.tipo_doc.upper()
            emoji_doc = "📄"
            ruolo_da_assegnare = None

            # --- GESTIONE DEI VARI TIPI DI DOCUMENTI ---
            if "CITTADINANZA" in tipo_upper:
                user_lic["cittadinanza"] = True
                emoji_doc = "🇮🇹"
                if ID_RUOLO_CITTADINO != 0:
                    ruolo_da_assegnare = interaction.guild.get_role(ID_RUOLO_CITTADINO)

            elif "PORTO" in tipo_upper or "ARMI" in tipo_upper:
                user_lic["porto_darmi"] = True
                emoji_doc = "🔫"
                if ID_RUOLO_PORTO_DARMI != 0:
                    ruolo_da_assegnare = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)

            elif "ASSICURAZIONE" in tipo_upper:
                # 1. Controlla e scala i € 500
                eco = get_user_eco(user_id_str)
                cash = eco.get("cash", 0)
                bank = eco.get("bank", 0)

                if cash >= 500:
                    eco["cash"] -= 500
                elif bank >= 500:
                    eco["bank"] -= 500
                else:
                    await interaction.followup.send(
                        f"❌ **Impossibile approvare:** L'utente non ha € 500. Possiede € {cash:,} in contanti e € {bank:,} in banca.",
                        ephemeral=True
                    )
                    return

                update_user_eco(user_id_str, eco)

                # 2. Salva lo stato nei dati locali
                user_lic["assicurazione"] = True
                emoji_doc = "🛡️"
                if ID_RUOLO_ASSICURATO != 0:
                    ruolo_da_assegnare = interaction.guild.get_role(ID_RUOLO_ASSICURATO)

            elif "PATENTE" in tipo_upper:
                if "PATENTE B" in tipo_upper:
                    user_lic["patente_b"] = True
                    role_id = ID_RUOLO_PATENTI.get("patente_b")
                elif "PATENTE C" in tipo_upper:
                    user_lic["patente_c"] = True
                    role_id = ID_RUOLO_PATENTI.get("patente_c")
                elif "PATENTE D" in tipo_upper:
                    user_lic["patente_d"] = True
                    role_id = ID_RUOLO_PATENTI.get("patente_d")
                elif "PATENTE A" in tipo_upper:
                    user_lic["patente_a"] = True
                    role_id = ID_RUOLO_PATENTI.get("patente_a")
                else:
                    role_id = None

                if role_id:
                    ruolo_da_assegnare = interaction.guild.get_role(role_id)

            save_data(data)

            # Recuperiamo l'utente dal server
            member = interaction.guild.get_member(self.user_id)
            if not member:
                try:
                    member = await interaction.guild.fetch_member(self.user_id)
                except Exception:
                    member = None

            # 1. Assegna il ruolo Discord all'utente
            ruolo_assegnato = False
            if member and ruolo_da_assegnare:
                try:
                    await member.add_roles(ruolo_da_assegnare, reason=f"Documento approvato: {self.tipo_doc}")
                    ruolo_assegnato = True
                except Exception:
                    pass

            # 2. Invia il messaggio in DM all'utente
            dm_inviato = False
            if member:
                if "ASSICURAZIONE" in tipo_upper:
                    embed_dm = discord.Embed(
                        title="🛡️ ASSICURAZIONE APPROVATA",
                        description=(
                            f"Ciao {member.mention}, la tua richiesta di assicurazione per il veicolo "
                            f"**{self.roblox_user}** è stata **APPROVATA** dallo Staff!\n\n"
                            f"💸 **Costo addebitato:** `€ 500`\n"
                            f"🎗️ Ti è stato assegnato il ruolo di assicurato."
                        ),
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                else:
                    embed_dm = discord.Embed(
                        title=f"✅ {emoji_doc} DOCUMENTO APPROVATO",
                        description=(
                            f"Ciao {member.mention}, la tua richiesta per **{self.tipo_doc}** è stata **APPROVATA**!\n\n"
                            f"🎗️ Ti è stato assegnato il rispettivo ruolo nel server."
                        ),
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )

                try:
                    await member.send(embed=embed_dm)
                    dm_inviato = True
                except Exception:
                    dm_inviato = False

            # 3. Aggiorna l'embed nel canale Accettazione Documenti
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.title = f"✅ RICHIESTA APPROVATA: {self.tipo_doc.upper()}"
            embed.set_footer(text=f"Approvato da {interaction.user.display_name}")

            # Disabilita i pulsanti
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(embed=embed, view=self)

            # Conferma visibile allo staff
            await interaction.followup.send(
                f"✅ **Documento approvato con successo!**\n"
                f"🎗️ Ruolo assegnato: `{'SÌ ✅' if ruolo_assegnato else 'NO ❌ (Controlla gerarchia ruoli)'}`\n"
                f"📩 DM inviato: `{'SÌ ✅' if dm_inviato else 'NO ❌ (L’utente ha i DM chiusi)'}`",
                ephemeral=True
            )

            # 📥 CREA IL POST AUTOMATICO NEL FORUM DOCUMENTI CITTADINI
            forum_channel = interaction.guild.get_channel(ID_FORUM_DOCUMENTI)
            if forum_channel and isinstance(forum_channel, discord.ForumChannel):
                if "ASSICURAZIONE" in tipo_upper:
                    embed_forum = discord.Embed(
                        title=f"🛡️ ASSICURAZIONE VEICOLO — {self.nome_rp}",
                        description=(
                            f"👤 **Intestatario:** {member.mention if member else 'Utente'}\n"
                            f"📜 **Nome RP:** `{self.nome_rp}`\n"
                            f"🚗 **Veicolo & Targa:** `{self.roblox_user}`\n"
                            f"💳 **Stato Polizza:** `ATTIVA ✅`\n"
                            f"💰 **Importo Saldato:** `€ 500`"
                        ),
                        color=discord.Color.blue(),
                        timestamp=discord.utils.utcnow()
                    )
                    nome_thread = f"🛡️ ASSICURAZIONE | {self.nome_rp} ({self.roblox_user})"
                else:
                    embed_forum = discord.Embed(
                        title=f"📄 {emoji_doc} DOCUMENTO ({self.tipo_doc}) — {self.nome_rp}",
                        description=(
                            f"👤 **Cittadino:** {member.mention if member else 'Utente'}\n"
                            f"📜 **Nome RP:** `{self.nome_rp}`\n"
                            f"🎮 **Account Roblox:** `{self.roblox_user}`\n"
                            f"📌 **Tipo Documento:** `{self.tipo_doc}`\n\n"
                            f"📌 *Documento ufficiale registrato nel sistema di Puglia RP.*"
                        ),
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                    nome_thread = f"{emoji_doc} {self.tipo_doc.upper()} | {self.nome_rp} ({self.roblox_user})"

                try:
                    await forum_channel.create_thread(
                        name=nome_thread,
                        embed=embed_forum
                    )
                except Exception:
                    pass

        except Exception as e:
            await interaction.followup.send(f"❌ Errore durante l'approvazione: `{e}`", ephemeral=True)

    @discord.ui.button(label="Rifiuta Documento", style=discord.ButtonStyle.danger, custom_id="btn_rifiuta_documento")
    async def rifiuta(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        try:
            member = interaction.guild.get_member(self.user_id)
            if not member:
                try:
                    member = await interaction.guild.fetch_member(self.user_id)
                except Exception:
                    member = None

            # Invia il DM di rifiuto all'utente
            dm_inviato = False
            if member:
                tipo_upper = self.tipo_doc.upper()
                if "ASSICURAZIONE" in tipo_upper:
                    embed_dm = discord.Embed(
                        title="❌ ASSICURAZIONE RIFIUTATA",
                        description=(
                            f"Ciao {member.mention}, la tua richiesta di assicurazione per **{self.roblox_user}** è stata **RIFIUTATA** dallo Staff.\n\n"
                            f"⏳ Nessun importo è stato scalato. Puoi correggere i dati e inviare una nuova richiesta."
                        ),
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )
                else:
                    embed_dm = discord.Embed(
                        title="❌ DOCUMENTO RIFIUTATO",
                        description=f"Ciao {member.mention}, la tua richiesta per **{self.tipo_doc}** è stata **RIFIUTATA** dallo Staff.",
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )

                try:
                    await member.send(embed=embed_dm)
                    dm_inviato = True
                except Exception:
                    dm_inviato = False

            # Aggiorna il messaggio nel canale log dello staff
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()
            embed.title = f"❌ RICHIESTA RIFIUTATA: {self.tipo_doc.upper()}"
            embed.set_footer(text=f"Rifiutato da {interaction.user.display_name}")

            for child in self.children:
                child.disabled = True
            await interaction.message.edit(embed=embed, view=self)

            await interaction.followup.send(
                f"❌ **Richiesta rifiutata con successo!**\n"
                f"📩 DM inviato all'utente: `{'SÌ ✅' if dm_inviato else 'NO ❌ (ha i DM chiusi)'}`",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(f"❌ Errore durante il rifiuto: `{e}`", ephemeral=True)
            
# ==========================================
# 📝 MODALE RICHIESTA CITTADINANZA
# ==========================================
# ==========================================
# 🇮🇹 MODALE RICHIESTA CITTADINANZA
# ==========================================
class ModalCittadinanza(discord.ui.Modal, title="🇮🇹 Richiesta Cittadinanza Puglia RP"):
    nome_rp = discord.ui.TextInput(
        label="👤 Nome e Cognome RP",
        placeholder="Es. Mario Rossi",
        required=True,
        max_length=50
    )
    roblox_user = discord.ui.TextInput(
        label="🎮 Nome Utente Roblox",
        placeholder="Es. MarioRossi_123",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # 1. Recupera il canale dei log/accettazione
        canale_log = interaction.guild.get_channel(ID_CANALE_LOG_DOCUMENTI)
        if not canale_log:
            await interaction.followup.send(
                "❌ **Errore:** Il canale di approvazione documenti non è configurato correttamente! Avvisa un Amministratore.", 
                ephemeral=True
            )
            return

        # 2. Embed inviato allo Staff nel canale di accettazione
        embed_richiesta = discord.Embed(
            title="🇮🇹 RICHIESTA DOCUMENTO: CITTADINANZA",
            description=(
                f"👤 **Cittadino:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"📜 **Nome RP:** `{self.nome_rp.value.strip()}`\n"
                f"🎮 **Account Roblox:** `{self.roblox_user.value.strip()}`\n\n"
                f"⏳ *In attesa di approvazione o rifiuto da parte dello Staff.*"
            ),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed_richiesta.set_footer(text="Puglia RP • In attesa di valutazione")

        # 3. Collega i pulsanti della vista Documenti
        view = Documenti(
            user_id=interaction.user.id,
            nome_rp=self.nome_rp.value.strip(),
            roblox_user=self.roblox_user.value.strip(),
            tipo_doc="Cittadinanza"
        )

        try:
            # 4. Invio nel canale staff
            await canale_log.send(embed=embed_richiesta, view=view)
            await interaction.followup.send(
                "✅ **Richiesta inviata con successo!** È stata inoltrata allo Staff per la valutazione.", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Impossibile inviare la richiesta nel canale staff. Errore permessi: `{e}`", 
                ephemeral=True
            )


# --- Modale Patente (Ordinata e Senza Roblox) ---
# ==========================================
# 🚗 MODALE RICHIESTA PATENTI (A, B, C, D)
# ==========================================
# ==========================================
# 🚗 MODALE RICHIESTA PATENTE
# ==========================================
class ModalPatente(discord.ui.Modal, title="🚗 Richiesta Patente Puglia RP"):
    nome_rp = discord.ui.TextInput(
        label="👤 Nome e Cognome RP",
        placeholder="Es. Mario Rossi",
        required=True,
        max_length=50
    )
    tipo_patente = discord.ui.TextInput(
        label="🪪 Tipo di Patente (A, B, C, D)",
        placeholder="Es. Patente B",
        required=True,
        max_length=20
    )
    roblox_user = discord.ui.TextInput(
        label="🎮 Nome Utente Roblox",
        placeholder="Es. MarioRossi_123",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # 1. Recupera il canale dei log/accettazione dello staff
        canale_log = interaction.guild.get_channel(ID_CANALE_LOG_DOCUMENTI)
        if not canale_log:
            await interaction.followup.send(
                "❌ **Errore:** Il canale di approvazione documenti non è configurato correttamente! Avvisa un Amministratore.", 
                ephemeral=True
            )
            return

        # 2. Crea l'embed da mandare allo Staff nel canale di accettazione
        embed_richiesta = discord.Embed(
            title=f"🚗 RICHIESTA DOCUMENTO: {self.tipo_patente.value.strip().upper()}",
            description=(
                f"👤 **Cittadino:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"📜 **Nome RP:** `{self.nome_rp.value.strip()}`\n"
                f"🪪 **Tipo Richiesto:** `{self.tipo_patente.value.strip()}`\n"
                f"🎮 **Account Roblox:** `{self.roblox_user.value.strip()}`\n\n"
                f"⏳ *In attesa di approvazione o rifiuto da parte dello Staff.*"
            ),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed_richiesta.set_footer(text="Puglia RP • In attesa di valutazione")

        # 3. Collega i pulsanti della vista Documenti passando il tipo esatto (es. "Patente B")
        view = Documenti(
            user_id=interaction.user.id,
            nome_rp=self.nome_rp.value.strip(),
            roblox_user=self.roblox_user.value.strip(),
            tipo_doc=self.tipo_patente.value.strip()  # Importante per far riconoscere se è A, B, C o D
        )

        try:
            # 4. Invia nel canale staff con i bottoni Accetta/Rifiuta
            await canale_log.send(embed=embed_richiesta, view=view)
            await interaction.followup.send(
                "✅ **Richiesta di patente inviata con successo!** È stata inoltrata allo Staff per la valutazione.", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Impossibile inviare la richiesta nel canale staff. Errore: `{e}`", 
                ephemeral=True
            )
            await interaction.followup.send(f"❌ Errore nell'invio della richiesta nel canale: `{e}`", ephemeral=True)


# ==========================================
# 🔫 MODALE PORTO D'ARMI (CON MODELLO ARMA)
# ==========================================
class ModalPortoDArmi(discord.ui.Modal, title="🔫 Richiesta Porto d'Armi Puglia RP"):
    nome_rp = discord.ui.TextInput(
        label="👤 Nome e Cognome RP",
        placeholder="Es. Mario Rossi",
        required=True,
        max_length=50
    )
    roblox_user = discord.ui.TextInput(
        label="🎮 Account Roblox",
        placeholder="Es. Player123",
        required=True,
        max_length=50
    )
    modello_arma = discord.ui.TextInput(
        label="🔫 Modello Arma Richiesta",
        placeholder="Es. Glock-17, Beretta 92FS...",
        required=True,
        max_length=50
    )
    motivazione = discord.ui.TextInput(
        label="📝 Motivazione Richiesta",
        style=discord.TextStyle.paragraph,
        placeholder="",
        required=True,
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)

        # 1. Salva nei dati locali
        data = load_data()
        licenze_data = data.setdefault("licenze_cittadini", {})
        user_lic = licenze_data.setdefault(user_id_str, {})
        user_lic["porto_darmi"] = True
        save_data(data)

        # 2. Assegna il Ruolo Discord Porto d'Armi
        if ID_RUOLO_PORTO_DARMI != 0:
            ruolo = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)
            if ruolo:
                try:
                    await interaction.user.add_roles(ruolo, reason="Porto d'armi approvato")
                except Exception:
                    pass

        # 3. Invia Log nel canale Log Documenti
        canale_log = interaction.guild.get_channel(ID_CANALE_LOG_DOCUMENTI)
        if canale_log:
            embed_log = discord.Embed(
                title="🔫 NUOVO PORTO D'ARMI REGISTRATO",
                description=(
                    f"👤 **Cittadino:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"📜 **Nome RP:** `{self.nome_rp.value.strip()}`\n"
                    f"🎮 **Roblox:** `{self.roblox_user.value.strip()}`\n"
                    f"🔫 **Modello Arma:** `{self.modello_arma.value.strip()}`\n"
                    f"📝 **Motivazione:** `{self.motivazione.value.strip()}`"
                ),
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed_log.set_footer(text="Puglia RP • Licenza Armi Attiva")
            await canale_log.send(embed=embed_log)

        # 4. Crea la Scheda Ufficiale nel Forum Documenti
        forum_channel = interaction.guild.get_channel(ID_FORUM_DOCUMENTI)
        if forum_channel and isinstance(forum_channel, discord.ForumChannel):
            embed_forum = discord.Embed(
                title=f"🔫 PORTO D'ARMI — {self.nome_rp.value.strip()}",
                description=(
                    f"👤 **Intestatario:** {interaction.user.mention}\n"
                    f"📜 **Nome RP:** `{self.nome_rp.value.strip()}`\n"
                    f"🎮 **Account Roblox:** `{self.roblox_user.value.strip()}`\n"
                    f"🔫 **Modello Arma Registrata:** `{self.modello_arma.value.strip()}`\n"
                    f"📝 **Motivazione:** `{self.motivazione.value.strip()}`\n"
                    f"💳 **Stato Licenza:** `VALIDA ✅`"
                ),
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            try:
                await forum_channel.create_thread(
                    name=f"🔫 PORTO D'ARMI | {self.nome_rp.value.strip()} ({self.modello_arma.value.strip()})",
                    embed=embed_forum
                )
            except Exception:
                pass

        # 5. Messaggio di conferma all'utente
        embed_conferma = discord.Embed(
            title="🔫 PORTO D'ARMI RILASCIATO CON SUCCESSO!",
            description=(
                f"Il tuo Porto d'Armi per **{self.modello_arma.value.strip()}** è stato approvato e registrato.\n\n"
                f"🎗️ Ti è stato assegnato il ruolo ufficiale e la scheda è stata salvata nel **Forum Documenti**."
            ),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.followup.send(embed=embed_conferma, ephemeral=True)

# ==========================================
# 🛡️ MODALE RICHIESTA ASSICURAZIONE (COMPLETO)
# ==========================================
class ModalAssicurazione(discord.ui.Modal, title="🛡️ Stipula Assicurazione Veicolo"):
    nome_rp = discord.ui.TextInput(
        label="👤 Nome e Cognome RP",
        placeholder="Es. Mario Rossi",
        required=True,
        max_length=50
    )
    modello_veicolo = discord.ui.TextInput(
        label="🚗 Modello Veicolo",
        placeholder="Es. Volksburg Marin",
        required=True,
        max_length=40
    )
    targa = discord.ui.TextInput(
        label="🔢 Targa Veicolo",
        placeholder="Es. AB/BC/10",
        required=True,
        max_length=20
    )
    patente = discord.ui.TextInput(
        label="🪪 Tipo di Patente",
        placeholder="Es. A, B, C, D",
        required=True,
        max_length=20

    )
    soldi = discord.ui.TextInput(
        label="💵 Hai 500 euro da spendere?",
        placeholder=" Si, No",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        canale_log = interaction.guild.get_channel(ID_CANALE_LOG_DOCUMENTI)
        if not canale_log:
            await interaction.followup.send("❌ Canale di approvazione non trovato!", ephemeral=True)
            return

        veicolo_info = f"{self.modello_veicolo.value.strip()} ({self.targa.value.strip()})"

        embed_richiesta = discord.Embed(
            title="🛡️ RICHIESTA DOCUMENTO: ASSICURAZIONE VEICOLO",
            description=(
                f"👤 **Cittadino:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"📜 **Nome RP:** `{self.nome_rp.value.strip()}`\n"
                f"🚗 **Modello Veicolo:** `{self.modello_veicolo.value.strip()}`\n"
                f"🔢 **Targa:** `{self.targa.value.strip()}`\n"
                f"🪪 **Tipo Patente:** `{self.patente.value.strip()}\n"
                f"💰 **Costo Previsto:** `€ 500`\n\n"
                f"⏳ *In attesa di approvazione o rifiuto da parte dello Staff.*"
            ),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed_richiesta.set_footer(text="Puglia RP • Valutazione Polizza")

        view = Documenti(
            user_id=interaction.user.id,
            nome_rp=self.nome_rp.value.strip(),
            roblox_user=veicolo_info, # Inviamo le info del veicolo
            tipo_doc="Assicurazione"
        )

        await canale_log.send(embed=embed_richiesta, view=view)
        await interaction.followup.send(
            f"✅ **Richiesta inviata con successo!** L'assicurazione per **{veicolo_info}** è stata inoltrata allo Staff per l'approvazione.", 
            ephemeral=True
        )



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

    @discord.ui.button(label="Stipula Assicurazione (€500)", style=discord.ButtonStyle.success, emoji="🛡️", custom_id="btn_stipula_assicurazione")
    async def req_assicurazione(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalAssicurazione())

    @discord.ui.button(label="Porto d'Armi", style=discord.ButtonStyle.danger, emoji="🔫", custom_id="btn_armi")
    async def btn_armi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalPortoDArmi())

    

#sdasdas
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
# 💰 GESTIONE ECONOMIA UNIFICATA
# ==========================================

def get_user_eco(user_id_str: str):
    data = load_data()
    eco_all = data.setdefault("economia", {})
    eco_user = eco_all.setdefault(user_id_str, {
        "cash": 0,
        "bank": 0,
        "has_account": False
    })
    
    if "cash" not in eco_user: eco_user["cash"] = 0
    if "bank" not in eco_user: eco_user["bank"] = 0
    if "has_account" not in eco_user:
        eco_user["has_account"] = True if eco_user.get("bank", 0) > 0 else False
        
    save_data(data)
    return eco_user

def update_user_eco(user_id_str: str, eco_data: dict):
    data = load_data()
    data.setdefault("economia", {})[user_id_str] = eco_data
    save_data(data)


# ------------------------------------------
# 💵 COMANDI CITTADINI
# ------------------------------------------

# 🤝 /paga (Scambio di contanti a mani)
@bot.tree.command(name="paga", description="Paga un altro cittadino in contanti (mano a mano)")
@app_commands.describe(utente="Il cittadino a cui consegnare i contanti", importo="Quantità di denaro in euro")
async def paga_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int):
    await interaction.response.defer(ephemeral=True)

    if utente.id == interaction.user.id:
        await interaction.followup.send("❌ Non puoi pagare te stesso!", ephemeral=True)
        return

    if importo <= 0:
        await interaction.followup.send("❌ Inserisci un importo valido maggiore di zero!", ephemeral=True)
        return

    sender_id = str(interaction.user.id)
    receiver_id = str(utente.id)

    sender_eco = get_user_eco(sender_id)
    receiver_eco = get_user_eco(receiver_id)

    if sender_eco.get("cash", 0) < importo:
        await interaction.followup.send(f"❌ Non hai abbastanza contanti in portafoglio! Possiedi solo **€ {sender_eco.get('cash', 0):,}**.", ephemeral=True)
        return

    sender_eco["cash"] -= importo
    receiver_eco["cash"] += importo

    update_user_eco(sender_id, sender_eco)
    update_user_eco(receiver_id, receiver_eco)

    await interaction.followup.send(f"🤝 Hai consegnato **€ {importo:,}** in contanti a {utente.mention}!", ephemeral=True)


# 🏦 /bonifico (Trasferimento da conto bancario a conto bancario)
@bot.tree.command(name="bonifico", description="Effettua un bonifico bancario ad un altro cittadino")
@app_commands.describe(utente="Il destinatario del bonifico", importo="Quantità di euro da inviare")
async def bonifico_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int):
    await interaction.response.defer(ephemeral=True)

    if utente.id == interaction.user.id:
        await interaction.followup.send("❌ Non puoi inviare un bonifico a te stesso!", ephemeral=True)
        return

    if importo <= 0:
        await interaction.followup.send("❌ Inserisci un importo valido maggiore di zero!", ephemeral=True)
        return

    sender_id = str(interaction.user.id)
    receiver_id = str(utente.id)

    sender_eco = get_user_eco(sender_id)
    receiver_eco = get_user_eco(receiver_id)

    if not sender_eco.get("has_account"):
        await interaction.followup.send("❌ Non possiedi un conto bancario attivo! Aprilo prima allo sportello bancario.", ephemeral=True)
        return

    if not receiver_eco.get("has_account"):
        await interaction.followup.send(f"❌ {utente.mention} non possiede un conto bancario attivo!", ephemeral=True)
        return

    if sender_eco.get("bank", 0) < importo:
        await interaction.followup.send(f"❌ Saldo bancario insufficiente! Sul tuo conto hai **€ {sender_eco.get('bank', 0):,}**.", ephemeral=True)
        return

    sender_eco["bank"] -= importo
    receiver_eco["bank"] += importo

    update_user_eco(sender_id, sender_eco)
    update_user_eco(receiver_id, receiver_eco)

    await interaction.followup.send(f"🏦 Bonifico di **€ {importo:,}** inviato con successo a {utente.mention}!", ephemeral=True)


# 🏦 /deposita (Mettere contanti in banca)
@bot.tree.command(name="deposita", description="Deposita contanti sul tuo conto bancario")
@app_commands.describe(importo="L'importo in euro da depositare")
async def deposita_cmd(interaction: discord.Interaction, importo: int):
    await interaction.response.defer(ephemeral=True)
    
    if importo <= 0:
        await interaction.followup.send("❌ Inserisci un importo valido!", ephemeral=True)
        return

    user_id_str = str(interaction.user.id)
    eco = get_user_eco(user_id_str)

    if not eco.get("has_account"):
        await interaction.followup.send("❌ Non possiedi un conto bancario attivo!", ephemeral=True)
        return

    if eco.get("cash", 0) < importo:
        await interaction.followup.send(f"❌ Non hai abbastanza contanti! Hai solo **€ {eco.get('cash', 0):,}**.", ephemeral=True)
        return

    eco["cash"] -= importo
    eco["bank"] += importo
    update_user_eco(user_id_str, eco)

    await interaction.followup.send(f"✅ Hai depositato **€ {importo:,}** sul tuo conto bancario!", ephemeral=True)


# 🏧 /preleva (Prelevare soldi dalla banca in contanti)
@bot.tree.command(name="preleva", description="Preleva denaro contante dal tuo conto bancario")
@app_commands.describe(importo="L'importo in euro da prelevare")
async def preleva_cmd(interaction: discord.Interaction, importo: int):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ Inserisci un importo valido!", ephemeral=True)
        return

    user_id_str = str(interaction.user.id)
    eco = get_user_eco(user_id_str)

    if not eco.get("has_account"):
        await interaction.followup.send("❌ Non possiedi un conto bancario attivo!", ephemeral=True)
        return

    if eco.get("bank", 0) < importo:
        await interaction.followup.send(f"❌ Saldo bancario insufficiente! Hai solo **€ {eco.get('bank', 0):,}** in banca.", ephemeral=True)
        return

    eco["bank"] -= importo
    eco["cash"] += importo
    update_user_eco(user_id_str, eco)

    await interaction.followup.send(f"💸 Hai prelevato **€ {importo:,}** dal tuo conto bancario!", ephemeral=True)


# ------------------------------------------
# 🛠️ COMANDI ADMIN / STAFF
# ------------------------------------------

# ➕ /aggiungi-soldi
@bot.tree.command(name="aggiungi-soldi", description="Aggiungi soldi ad un utente (Solo Admin)")
@app_commands.describe(utente="L'utente a cui aggiungere denaro", tipo="Dove aggiungere il denaro?", importo="Quantità in euro")
@app_commands.choices(tipo=[
    app_commands.Choice(name="💵 Contanti (Portafoglio)", value="cash"),
    app_commands.Choice(name="🏦 Conto Bancario", value="bank")
])
@app_commands.checks.has_permissions(administrator=True)
async def aggiungi_soldi_cmd(interaction: discord.Interaction, utente: discord.Member, tipo: app_commands.Choice[str], importo: int):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ L'importo deve essere maggiore di zero!", ephemeral=True)
        return

    user_id_str = str(utente.id)
    eco = get_user_eco(user_id_str)

    if tipo.value == "bank":
        eco["has_account"] = True  # Se gli admin aggiungono soldi in banca, attiva automaticamente il conto
        eco["bank"] += importo
        destinazione = "conto bancario"
    else:
        eco["cash"] += importo
        destinazione = "portafoglio (contanti)"

    update_user_eco(user_id_str, eco)
    await interaction.followup.send(f"✅ Aggiunti **€ {importo:,}** sul {destinazione} di {utente.mention}!", ephemeral=True)


# ➖ /rimuovi-soldi
@bot.tree.command(name="rimuovi-soldi", description="Rimuovi soldi ad un utente (Solo Admin)")
@app_commands.describe(utente="L'utente a cui togliere denaro", tipo="Da dove togliere il denaro?", importo="Quantità in euro")
@app_commands.choices(tipo=[
    app_commands.Choice(name="💵 Contanti (Portafoglio)", value="cash"),
    app_commands.Choice(name="🏦 Conto Bancario", value="bank")
])
@app_commands.checks.has_permissions(administrator=True)
async def rimuovi_soldi_cmd(interaction: discord.Interaction, utente: discord.Member, tipo: app_commands.Choice[str], importo: int):
    await interaction.response.defer(ephemeral=True)

    if importo <= 0:
        await interaction.followup.send("❌ L'importo deve essere maggiore di zero!", ephemeral=True)
        return

    user_id_str = str(utente.id)
    eco = get_user_eco(user_id_str)

    if tipo.value == "bank":
        eco["bank"] = max(0, eco.get("bank", 0) - importo)
        destinazione = "conto bancario"
    else:
        eco["cash"] = max(0, eco.get("cash", 0) - importo)
        destinazione = "portafoglio (contanti)"

    update_user_eco(user_id_str, eco)
    await interaction.followup.send(f"✅ Rimosse **€ {importo:,}** dal {destinazione} di {utente.mention}!", ephemeral=True)
        
# ==========================================
# 🏦 APERTURA CONTO BANCARIO (SCRITTURA DIRETTA)
# ==========================================
class ModalApriContoIstantaneo(discord.ui.Modal, title="🏦 Apertura Conto Corrente"):
    nome_cognome = discord.ui.TextInput(label="👤 Nome e Cognome RP", placeholder="Es. Mario Rossi", required=True, max_length=40)
    eta_rp = discord.ui.TextInput(label="🆔 Hai già la cittadinanza?", placeholder="Si, No", required=True, max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        
        # Carichiamo ed aggiorniamo direttamente l'economia
        eco = get_user_eco(user_id_str)

        if eco.get("has_account") and eco.get("bank", 0) > 0:
            await interaction.followup.send("❌ **Possiedi già un conto corrente attivo su Puglia RP!**", ephemeral=True)
            return

        # Impostiamo conto attivo + Bonus 1.000€
        eco["has_account"] = True
        eco["bank"] = eco.get("bank", 0) + 1000
        update_user_eco(user_id_str, eco)

        # Salva anche il nome RP
        data = load_data()
        data.setdefault("rp_names", {})[user_id_str] = self.nome_cognome.value.strip()
        save_data(data)

        embed = discord.Embed(
            title="🎉 CONTO BANCARIO APERTO CON SUCCESSO!",
            description=(
                f"Benvenuto nella gestione finanziaria di **Puglia RP**, **{self.nome_cognome.value.strip()}**!\n\n"
                f"💳 **Stato Conto:** `ATTIVO`\n"
                f"👤 **Intestatario RP:** `{self.nome_cognome.value.strip()}` (`{self.eta_rp.value.strip()} anni`)\n"
                f"💰 **Bonus di Benvenuto:** `€ 1.000` accreditati sul tuo conto corrente!"
            ),
            color=discord.Color.from_rgb(46, 204, 113),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Banca di Puglia RP • Servizi Finanziari Digitali")

        await interaction.followup.send(embed=embed, ephemeral=True)


# ==========================================
# 💳 COMANDO /PORTAFOGLIO
# ==========================================
@bot.tree.command(name="portafoglio", description="Mostra il tuo estratto conto bancario e i contanti")
async def portafoglio_cmd(interaction: discord.Interaction, utente: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    target = utente or interaction.user
    user_id_str = str(target.id)
    
    # Legge esattamente lo stesso dizionario
    eco = get_user_eco(user_id_str)
    
    cash = eco.get("cash", 0)
    bank = eco.get("bank", 0)
    has_account = eco.get("has_account", False)

    # Se ha soldi in banca, mostriamo lo stato attivo a prescindere
    if bank > 0:
        has_account = True

    stato_conto = f"**€ {bank:,}**" if has_account else "**Non Posseduto ❌**"

    embed = discord.Embed(
        title=f"💳 ESTRATTO CONTO — {target.display_name}",
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="💵 Portafoglio (Contanti)", value=f"**€ {cash:,}**", inline=True)
    embed.add_field(name="🏦 Conto Bancario", value=stato_conto, inline=True)
    
    if target.display_avatar:
        embed.set_thumbnail(url=target.display_avatar.url)

    await interaction.followup.send(embed=embed, ephemeral=True)

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
# 🏦 MODULO CONTO BANCARIO DIRECT (APERTURA ISTANTANEA)
# ==========================================


# 2. Vista del Pannello con il Pulsante "Apri Conto Bancario"
class VistaContoBancario(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apri Conto Bancario", style=discord.ButtonStyle.success, emoji="💳", custom_id="btn_apri_conto_bancario_direct")
    async def btn_apri_conto(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Apre subito il modale corretto all'utente
        await interaction.response.send_modal(ModalApriContoIstantaneo())


# 3. Comando Slash per spawnare il Pannello Bancario (Solo Admin)
@bot.tree.command(name="pannello-contobancario", description="Invia il pannello per l'apertura immediata del conto bancario (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def pannello_conto_cmd(interaction: discord.Interaction):
    await interaction.response.defer()

    embed = discord.Embed(
        title="🏦 ┆ BANCA DI PUGLIA RP — SPORTELLO DIGITALE",
        description=(
            "✨ **Benvenuto cittadino!** Gestisci al meglio le tue finanze all'interno della regione.\n"
            "Apri subito il tuo conto corrente personale in modo semplice, rapido e sicuro.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.from_rgb(230, 126, 34),
        timestamp=discord.utils.utcnow()
    )

    # Aggiungiamo dei campi ordinati per dare un tocco pulito e professionale
    embed.add_field(
        name="📋 ┆ Requisiti per l'Apertura",
        value="• Essere residenti registrati a **Puglia RP**\n• Utilizzare i propri dati anagrafici reali in RP",
        inline=False
    )

    embed.add_field(
        name="🎁 ┆ Vantaggi Esclusivi",
        value="• Ricevi subito un bonus di benvenuto di **€ 1.000** sul nuovo conto!\n• Accesso a bonifici, gestione contanti e prestiti regionali.",
        inline=False
    )

    embed.add_field(
        name="⚡ ┆ Come procedere",
        value="*Clicca sul pulsante sottostante per avviare la procedura guidata e registrare subito il tuo conto bancario.*",
        inline=False
    )

    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
        
    embed.set_footer(text="Puglia RP • Sistema Finanziario Integrato", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    await interaction.followup.send(embed=embed, view=VistaContoBancario())

# ==========================================
# ❌ COMANDO /REVOCA COMPLETO (INCLUSA ASSICURAZIONE)
# ==========================================
@bot.tree.command(name="revoca", description="Revoca licenze, patenti, cittadinanza o status")
@app_commands.describe(utente="L'utente a cui revocare il documento/licenza", tipo="Cosa vuoi revocare?")
@app_commands.choices(tipo=[
    app_commands.Choice(name="🚗 Patente A (Moto)", value="patente_a"),
    app_commands.Choice(name="🚙 Patente B (Auto)", value="patente_b"),
    app_commands.Choice(name="🚛 Patente C (Camion)", value="patente_c"),
    app_commands.Choice(name="🚌 Patente D (Autobus)", value="patente_d"),
    app_commands.Choice(name="🔫 Porto d'Armi", value="porto_darmi"),
    app_commands.Choice(name="🛡️ Assicurazione Veicolo", value="assicurazione"),
    app_commands.Choice(name="🇮🇹 Cittadinanza", value="cittadinanza"),
    app_commands.Choice(name="🏦 Conto Bancario / Documenti", value="documenti"),
    app_commands.Choice(name="🛡️ Identificazione Staff", value="staff")
])
async def revoca_cmd(interaction: discord.Interaction, utente: discord.Member, tipo: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)

    try:
        # 1. Permessi (Staff vs FDO)
        is_staff = any(role.id == ID_RUOLO_STAFF for role in interaction.user.roles) or interaction.user.guild_permissions.administrator
        is_fdo = any(role.id == ID_RUOLO_FDO for role in interaction.user.roles)
        
        licenze_fdo = ["patente_a", "patente_b", "patente_c", "patente_d", "porto_darmi", "assicurazione"]

        if not is_staff and not is_fdo:
            await interaction.followup.send("❌ Non hai i permessi necessari per utilizzare questo comando!", ephemeral=True)
            return

        if is_fdo and not is_staff and tipo.value not in licenze_fdo:
            await interaction.followup.send("⚠️ Come membro delle **FDO** puoi revocare solamente Patenti, Porto d'Armi e Assicurazioni!", ephemeral=True)
            return

        user_id_str = str(utente.id)
        data = load_data()
        
        licenze_data = data.setdefault("licenze_cittadini", {})
        user_licenze = licenze_data.setdefault(user_id_str, {
            "patente_a": False, "patente_b": False, "patente_c": False, "patente_d": False,
            "porto_darmi": False, "cittadinanza": True, "assicurazione": False
        })

        messaggio = ""
        modificato = False
        forum_id_da_pulire = None

        # --- REVOCA PATENTI ---
        if tipo.value in RUOLI_PATENTI:
            role_id = RUOLI_PATENTI[tipo.value]
            user_licenze[tipo.value] = False
            modificato = True
            messaggio = f"✅ **{tipo.name}** revocata con successo a {utente.mention}!"

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

        # --- REVOCA ASSICURAZIONE ---
        elif tipo.value == "assicurazione":
            user_licenze["assicurazione"] = False
            modificato = True
            messaggio = f"✅ **Assicurazione Veicolo** revocata con successo a {utente.mention}!"
            forum_id_da_pulire = ID_FORUM_DOCUMENTI

            ruolo = interaction.guild.get_role(ID_RUOLO_ASSICURATO)
            if ruolo and ruolo in utente.roles:
                try:
                    await utente.remove_roles(ruolo, reason="Assicurazione revocata")
                except Exception:
                    pass

        # --- REVOCA CITTADINANZA ---
        elif tipo.value == "cittadinanza":
            user_licenze["cittadinanza"] = False
            modificato = True
            messaggio = f"✅ **Cittadinanza** revocata con successo a {utente.mention}!"
            forum_id_da_pulire = ID_FORUM_DOCUMENTI

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
            forum_id_da_pulire = ID_FORUM_DOCUMENTI

        # --- REVOCA IDENTIFICAZIONE STAFF ---
        elif tipo.value == "staff":
            staff_data = data.get("identificazioni_staff", {})
            info_staff = staff_data.pop(user_id_str, None)
            data["identificazioni_staff"] = staff_data
            modificato = True
            messaggio = f"✅ L'identificazione Staff di {utente.mention} è stata revocata con successo!"
            forum_id_da_pulire = ID_FORUM_STAFF_IDENTIFICATI

            ruolo = interaction.guild.get_role(ID_RUOLO_STAFF)
            if ruolo and ruolo in utente.roles:
                try:
                    await utente.remove_roles(ruolo, reason="Identificazione Staff revocata")
                except Exception:
                    pass

        # 🗑️ ELIMINAZIONE AUTOMATICA POST NEL FORUM
        if forum_id_da_pulire:
            try:
                forum_channel = interaction.guild.get_channel(forum_id_da_pulire)
                if forum_channel and isinstance(forum_channel, discord.ForumChannel):
                    search_keys = [utente.name.lower(), utente.display_name.lower(), str(utente.id)]
                    
                    if tipo.value == "staff" and info_staff:
                        roblox_u = info_staff.get("roblox_user", "")
                        if roblox_u:
                            search_keys.append(roblox_u.lower())

                    post_eliminato = False
                    for thread in forum_channel.threads:
                        thread_name_lower = thread.name.lower()
                        if any(key in thread_name_lower for key in search_keys if key):
                            await thread.delete()
                            post_eliminato = True
                            messaggio += "\n🗑️ *Post nel forum eliminato automaticamente.*"
                            break

                    if not post_eliminato:
                        async for thread in forum_channel.archived_threads():
                            thread_name_lower = thread.name.lower()
                            if any(key in thread_name_lower for key in search_keys if key):
                                await thread.delete()
                                messaggio += "\n🗑️ *Post nel forum eliminato automaticamente.*"
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
# ❌ GESTIONE RIFIUTO DOCUMENTO CON DM SICURO
# ==========================================

# Esempio all'interno dell'on_submit del Modale di Rifiuto o comando di Rifiuto:
async def notifica_rifiuto(interaction: discord.Interaction, utente: discord.Member, tipo_documento: str, motivazione: str):
    dm_inviato = False

    # 1. Creiamo l'Embed per l'utente
    embed_dm = discord.Embed(
        title="❌ DOCUMENTO RIFIUTATO — PUGLIA RP",
        description=(
            f"Ciao {utente.mention}, la tua richiesta per **{tipo_documento}** è stata **RIFIUTATA**.\n\n"
            f"📝 **Motivazione:** `{motivazione}`\n\n"
            f"⏳ Potrai riprovare ad inviare la richiesta tra **10 minuti**."
        ),
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    embed_dm.set_footer(text="Puglia RP • Servizio Anagrafe e Documenti")

    # 2. Tentativo di invio in Messaggio Privato (DM)
    try:
        await utente.send(embed=embed_dm)
        dm_inviato = True
    except discord.Forbidden:
        # L'utente ha i DM chiusi o ha bloccato i bot
        dm_inviato = False
    except Exception:
        dm_inviato = False

    # 3. Risposta allo Staff/FDO che ha eseguito il rifiuto
    if dm_inviato:
        await interaction.followup.send(
            f"✅ Documento rifiutato a {utente.mention}.\n📩 **Messaggio inviato con successo nei suoi DM!**", 
            ephemeral=True
        )
    else:
        # Se i DM sono chiusi, avvisa lo staff
        await interaction.followup.send(
            f"⚠️ Documento rifiutato a {utente.mention}.\n"
            f"❌ **Impossibile inviare il DM:** L'utente ha i Messaggi Diretti disattivati nelle impostazioni di privacy di Discord!", 
            ephemeral=True
        )

    # 4. Log nel Canale dei Log Documenti
    canale_log = interaction.guild.get_channel(ID_CANALE_LOG_DOCUMENTI)
    if canale_log:
        embed_log = discord.Embed(
            title="❌ DOCUMENTO RIFIUTATO",
            description=(
                f"👤 **Utente:** {utente.mention} (`{utente.id}`)\n"
                f"📄 **Tipo Documento:** `{tipo_documento}`\n"
                f"🛡️ **Rifiutato da:** {interaction.user.mention}\n"
                f"📝 **Motivazione:** `{motivazione}`\n"
                f"📩 **Notificato in DM:** `{'SÌ ✅' if dm_inviato else 'NO ❌ (DM Chiusi)'}`"
            ),
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )
        await canale_log.send(embed=embed_log)

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
