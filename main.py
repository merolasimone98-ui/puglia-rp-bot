import discord
from discord import app_commands
from discord.ext import commands
import datetime

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot Online 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
                
# ⚙️ CONFIGURAZIONE CANALI
ID_CANALE_ACCETTAZIONE_STAFF = 1562891209675116544  # #accettazione-cittadinanza-staff
ID_FORUM_DOCUMENTI = 1562891782415450183            # #documenti-cittadinanza (Forum)





# ⚙️ CONFIGURAZIONE CANALI
ID_CANALE_ACCETTAZIONE_STAFF = 1562891209675116544  # #accettazione-cittadinanza-staff
ID_FORUM_DOCUMENTI = 1562891782415450183            # #documenti-cittadinanza (Forum)
LINK_IMMAGINE_RECENSIONE = "https://media.discordapp.net/attachments/1561284670883242086/1563156338580652072/1792755906447.jpg?ex=6adc9a49&is=6adb48c9&hm=889b0be762da4780fd7225ff6632c4ae457b26a5d1b1f6bfdadb3c413816c642&=&format=webp"
ID_CANALE_COMANDO_RECENSIONI = 1563193613452841061
ID_CANALE_LOG_RECENSIONI = 1563194331320557768
# ⚙️ CONFIGURAZIONE CANALI MULTE E ARRESTI
ID_CANALE_REGISTRO_ARRESTI = 1524685772995690607
ID_CANALE_REGISTRO_MULTE = 1563215066411696299
ID_CANALE_CONTO_BANCARIO = 1563216017851949227





# ⚙️ CONFIGURAZIONE RUOLI
ID_RUOLO_CITTADINO = 1562894350135066674
ID_RUOLO_PORTO_DARMI = 1562894902428442695

RUOLI_PATENTI = {
    'A': 1562894624597479555,
    'B': 1562894703081431090,
    'C': 1562894760878800897,
    'D': 1562894822983860364
}

# 🧠 MEMORIA NOMI RP APPROVATI: {user_id: "Nome Cognome RP"}
nomi_rp_registrati = {}

# ⏱️ MEMORIA COOLDOWN RIFIUTI: {(user_id, tipo_doc): datetime_prossima_richiesta}
cooldowns_rifiuti = {}

def controlla_cooldown_rifiuto(user_id, tipo_doc):
    chiave = (user_id, tipo_doc)
    if chiave in cooldowns_rifiuti:
        tempo_sblocco = cooldowns_rifiuti[chiave]
        ora_attuale = datetime.datetime.now()
        if ora_attuale < tempo_sblocco:
            minuti_rimanenti = int((tempo_sblocco - ora_attuale).total_seconds() // 60) + 1
            return False, minuti_rimanenti
        else:
            del cooldowns_rifiuti[chiave]
    return True, 0


# ==========================================
# 1️⃣ CITTADINANZA
# ==========================================
class ModalCittadinanza(discord.ui.Modal, title="🦇 Registratione Cittadinanza - Puglia RP"):
    nome_rp = discord.ui.TextInput(label="Nome e Cognome RP", placeholder="Es. Mario Rossi", min_length=3, required=True)
    eta_rp = discord.ui.TextInput(label="Data di Nascita / Età RP", placeholder="Es. 15/05/1998", min_length=2, required=True)
    roblox_user = discord.ui.TextInput(label="Username Roblox", placeholder="Es. MarioRoblox123", min_length=3, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        ruolo_cittadino = interaction.guild.get_role(ID_RUOLO_CITTADINO)
        if ruolo_cittadino and ruolo_cittadino in interaction.user.roles:
            await interaction.response.send_message(
                "❌ **NON PUOI RICHIEDERLO!** Sei già in possesso della Cittadinanza!",
                ephemeral=True
            )
            return

        ok_cooldown, minuti_attesa = controlla_cooldown_rifiuto(interaction.user.id, "Cittadinanza")
        if not ok_cooldown:
            await interaction.response.send_message(
                f"⏱️ **RICHIESTA RIFIUTATA DI RECENTE!**\nDevi attendere ancora **{minuti_attesa} minuti** prima di poter richiedere nuovamente la Cittadinanza.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "✅ La tua richiesta di cittadinanza è stata inviata allo staff! Attendi l'approvazione.", 
            ephemeral=True
        )

        canale_staff = interaction.guild.get_channel(ID_CANALE_ACCETTAZIONE_STAFF) or interaction.channel

        embed = discord.Embed(
            title="📥 NUOVA RICHIESTA CITTADINANZA",
            color=discord.Color.orange()
        )
        embed.add_field(name="Utente Discord", value=interaction.user.mention, inline=False)
        embed.add_field(name="Nome RP", value=self.nome_rp.value, inline=True)
        embed.add_field(name="Età RP", value=self.eta_rp.value, inline=True)
        embed.add_field(name="Roblox User", value=self.roblox_user.value, inline=False)

        await canale_staff.send(
            embed=embed, 
            view=ViewGestioneCittadinanza(interaction.user, self.nome_rp.value, self.eta_rp.value, self.roblox_user.value)
        )


# ==========================================
# ⚙️ GESTIONE CITTADINANZA STAFF
# ==========================================
class ViewGestioneCittadinanza(discord.ui.View):
    def __init__(self, utente, nome_rp, eta_rp, roblox_user):
        super().__init__(timeout=None)
        self.utente = utente
        self.nome_rp = nome_rp
        self.eta_rp = eta_rp
        self.roblox_user = roblox_user

    @discord.ui.button(label="Accetta ✅", style=discord.ButtonStyle.success)
    async def accetta(self, interaction: discord.Interaction, button: discord.ui.Button):
        nomi_rp_registrati[self.utente.id] = self.nome_rp

        try:
            await self.utente.edit(nick=self.nome_rp)
        except Exception:
            pass

        ruolo_cittadino = interaction.guild.get_role(ID_RUOLO_CITTADINO)
        if ruolo_cittadino:
            try:
                await self.utente.add_roles(ruolo_cittadino)
            except Exception:
                pass

        forum_channel = interaction.guild.get_channel(ID_FORUM_DOCUMENTI)
        if forum_channel and isinstance(forum_channel, discord.ForumChannel):
            # Assegnazione emoji dinamica corretta
            if "Patente A" in self.tipo_documento:
                prefisso = "🏍️"
            elif "Patente B" in self.tipo_documento:
                prefisso = "🚗"
            elif "Patente C" in self.tipo_documento:
                prefisso = "🚚"
            elif "Patente D" in self.tipo_documento:
                prefisso = "🚌"
            else:
                prefisso = "🔫"

            embed_doc = discord.Embed(
                title=f"📋 REGISTRAZIONE {self.tipo_documento.upper()}",
                description=f"Documento rilasciato con successo a {self.utente.mention}.",
                color=discord.Color.green() if "Patente" in self.tipo_documento else discord.Color.red()
            )
            embed_doc.add_field(name="Titolare RP", value=self.nome_rp_inserito, inline=False)
            
            for chiave, valore in self.dettagli.items():
                embed_doc.add_field(name=chiave, value=valore, inline=True)
                
            embed_doc.set_footer(text=f"Approvato da: {interaction.user.display_name}")

            await forum_channel.create_thread(
                name=f"{prefisso} {self.tipo_documento} - {self.nome_rp_inserito}",
                embed=embed_doc
            )

        # Disabilita i bottoni ed edita il messaggio dell'embed nello staff
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # Risposta PRIVATA/EFFIMERA solo allo staffer che ha cliccato
        await interaction.response.send_message(
            f"✅ **Cittadinanza approvata per {self.utente.mention}!** Ruolo assegnato e post pubblicato nel forum.", 
            ephemeral=True
        )

        try:
            await self.utente.send(f"🎉 La tua richiesta di cittadinanza per **Puglia RP** è stata **ACCETTATA**! Ti è stato assegnato il ruolo di Cittadino.")
        except Exception:
            pass
        self.stop()

    @discord.ui.button(label="Rifiuta ❌", style=discord.ButtonStyle.danger)
    async def rifiuta(self, interaction: discord.Interaction, button: discord.ui.Button):
        cooldowns_rifiuti[(self.utente.id, "Cittadinanza")] = datetime.datetime.now() + datetime.timedelta(minutes=10)

        # Disabilita i bottoni ed edita il messaggio
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # Risposta PRIVATA/EFFIMERA solo allo staffer
        await interaction.response.send_message(
            f"❌ **Cittadinanza rifiutata per {self.utente.mention}.** Potrà riprovare tra 5 minuti.", 
            ephemeral=True
        )

        try:
            await self.utente.send(f"❌ La tua richiesta di cittadinanza per **Puglia RP** è stata **RIFIUTATA**. Potrai riprovare tra **5 minuti**.")
        except Exception:
            pass
        self.stop()

# ==========================================
# ⚙️ GESTIONE GENERICA STAFF (PATENTI E ARMI)
# ==========================================
class ViewGestioneGenerica(discord.ui.View):
    def __init__(self, utente, nome_rp_inserito, tipo_documento, id_ruolo=None, dettagli=None):
        super().__init__(timeout=None)
        self.utente = utente
        self.nome_rp_inserito = nome_rp_inserito
        self.tipo_documento = tipo_documento
        self.id_ruolo = id_ruolo
        self.dettagli = dettagli or {}

    @discord.ui.button(label="Approva ✅", style=discord.ButtonStyle.success)
    async def accetta(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.id_ruolo:
            ruolo = interaction.guild.get_role(self.id_ruolo)
            if ruolo:
                try:
                    await self.utente.add_roles(ruolo)
                except Exception:
                    pass

        forum_channel = interaction.guild.get_channel(ID_FORUM_DOCUMENTI)
        if forum_channel and isinstance(forum_channel, discord.ForumChannel):
            embed_doc = discord.Embed(
                title=f"📋 REGISTRAZIONE {self.tipo_documento.upper()}",
                description=f"Documento rilasciato con successo a {self.utente.mention}.",
                color=discord.Color.green() if "Patente" in self.tipo_documento else discord.Color.red()
            )
            embed_doc.add_field(name="Titolare RP", value=self.nome_rp_inserito, inline=False)
            
            for chiave, valore in self.dettagli.items():
                embed_doc.add_field(name=chiave, value=valore, inline=True)
                
            embed_doc.set_footer(text=f"Approvato da: {interaction.user.display_name}")

            prefisso = "🚗" if "Patente" in self.tipo_documento else "🔫"
            await forum_channel.create_thread(
                name=f"{prefisso} {self.tipo_documento} - {self.nome_rp_inserito}",
                embed=embed_doc
            )

        # Disabilita i bottoni ed edita il messaggio dell'embed
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # Risposta PRIVATA/EFFIMERA allo staffer
        await interaction.response.send_message(
            f"✅ **{self.tipo_documento} approvata per {self.utente.mention}!** Ruolo assegnato e post pubblicato nel forum.", 
            ephemeral=True
        )

        try:
            await self.utente.send(f"🎉 La tua richiesta per **{self.tipo_documento}** su **Puglia RP** è stata **APPROVATA**!")
        except Exception:
            pass
        self.stop()

    @discord.ui.button(label="Rifiuta ❌", style=discord.ButtonStyle.danger)
    async def rifiuta(self, interaction: discord.Interaction, button: discord.ui.Button):
        cooldowns_rifiuti[(self.utente.id, self.tipo_documento)] = datetime.datetime.now() + datetime.timedelta(minutes=10)

        # Disabilita i bottoni ed edita il messaggio
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # Risposta PRIVATA/EFFIMERA allo staffer
        await interaction.response.send_message(
            f"❌ **{self.tipo_documento} rifiutata per {self.utente.mention}.** Potrà riprovare tra 10 minuti.", 
            ephemeral=True
        )

        try:
            await self.utente.send(f"❌ La tua richiesta per **{self.tipo_documento}** su **Puglia RP** è stata **RIFIUTATA**. Potrai riprovare tra **10 minuti**.")
        except Exception:
            pass
        self.stop()        


# ==========================================
# 2️⃣ PATENTI (SOLO A, B, C, D)
# ==========================================
class ModalPatente(discord.ui.Modal, title="🚗 Richiesta Patente - Puglia RP"):
    nome_rp = discord.ui.TextInput(
        label="Nome e Cognome RP", 
        placeholder="Es. Mario Rossi", 
        min_length=3, 
        required=True
    )
    tipo_patente = discord.ui.TextInput(
        label="Tipo di Patente (Solo A, B, C, D)", 
        placeholder="Scrivi solo una lettera tra: A, B, C, D", 
        min_length=1,
        max_length=1,
        required=True
    )
    modello_veicolo = discord.ui.TextInput(
        label="Modello del Veicolo", 
        placeholder="Es. Wolfsburg Marin", 
        min_length=2,
        required=True
    )
    targa_veicolo = discord.ui.TextInput(
        label="Targa Veicolo", 
        placeholder="Es. AB/CD/10", 
        min_length=4,
        max_length=12,
        required=True
    )
    note_extra = discord.ui.TextInput(
        label="Note aggiuntive / Motivazione", 
        placeholder="Es. Uso personale per lavoro", 
        style=discord.TextStyle.paragraph,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        nome_rp_inserito = self.nome_rp.value.strip()
        nome_rp_ufficiale = nomi_rp_registrati.get(interaction.user.id) or interaction.user.nick or interaction.user.display_name

        if nomi_rp_registrati.get(interaction.user.id) and nome_rp_inserito != nome_rp_ufficiale:
            await interaction.response.send_message(
                f"❌ **NOME RP NON CORRISPONDENTE!**\n"
                f"Il nome inserito (`{nome_rp_inserito}`) **NON è identico** al tuo Nome RP approvato con la Cittadinanza (`{nome_rp_ufficiale}`).\n"
                f"Devi scriverlo **esattamente uguale** rispettando maiuscole, minuscole e spazi!",
                ephemeral=True
            )
            return

        patente_inserita = self.tipo_patente.value.strip().upper()

        if patente_inserita not in RUOLI_PATENTI:
            await interaction.response.send_message(
                "❌ **LETTERA NON VALIDA!**\nPuoi richiedere soltanto le patenti ufficiali: **A, B, C** oppure **D**.\nControlla e riprova inserendo solo una di queste lettere!",
                ephemeral=True
            )
            return

        id_ruolo_patente = RUOLI_PATENTI.get(patente_inserita)
        ruolo_patente = interaction.guild.get_role(id_ruolo_patente)

        if ruolo_patente and ruolo_patente in interaction.user.roles:
            await interaction.response.send_message(
                f"❌ **NON PUOI RICHIEDERLA!** Sei già in possesso della **Patente {patente_inserita}**!",
                ephemeral=True
            )
            return

        ok_cooldown, minuti_attesa = controlla_cooldown_rifiuto(interaction.user.id, f"Patente {patente_inserita}")
        if not ok_cooldown:
            await interaction.response.send_message(
                f"⏱️ **RICHIESTA RIFIUTATA DI RECENTE!**\nDevi attendere ancora **{minuti_attesa} minuti** prima di poter richiedere nuovamente la **Patente {patente_inserita}**.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "✅ La tua richiesta per la patente è stata inviata alla Motorizzazione!", 
            ephemeral=True
        )

        canale_staff = interaction.guild.get_channel(ID_CANALE_ACCETTAZIONE_STAFF) or interaction.channel

        embed = discord.Embed(
            title="🚗 NUOVA RICHIESTA PATENTE",
            color=discord.Color.green()
        )
        embed.add_field(name="Utente Discord", value=interaction.user.mention, inline=False)
        embed.add_field(name="Nome RP", value=nome_rp_inserito, inline=True)
        embed.add_field(name="Tipo Patente", value=f"Patente {patente_inserita}", inline=True)
        embed.add_field(name="Targa", value=self.targa_veicolo.value.upper(), inline=True)
        embed.add_field(name="Modello Veicolo", value=self.modello_veicolo.value, inline=False)
        if self.note_extra.value:
            embed.add_field(name="Note", value=self.note_extra.value, inline=False)

        await canale_staff.send(
            embed=embed, 
            view=ViewGestioneGenerica(
                utente=interaction.user, 
                nome_rp_inserito=nome_rp_inserito,
                tipo_documento=f"Patente {patente_inserita}", 
                id_ruolo=id_ruolo_patente,
                dettagli={
                    "Tipo Patente": f"Patente {patente_inserita}",
                    "Modello Veicolo": self.modello_veicolo.value,
                    "Targa": self.targa_veicolo.value.upper(),
                    "Note": self.note_extra.value or "Nessuna"
                }
            )
        )


# ==========================================
# 3️⃣ PORTO D'ARMI
# ==========================================
class ModalPortoDArmi(discord.ui.Modal, title="🔫 Richiesta Porto d'Armi - Questura"):
    nome_rp = discord.ui.TextInput(
        label="Nome e Cognome RP", 
        placeholder="Es. Mario Rossi", 
        min_length=3, 
        required=True
    )
    motivo_richiesta = discord.ui.TextInput(
        label="Perché richiedi il Porto d'Armi?", 
        placeholder="Scrivi almeno 10 caratteri con una motivazione valida RP...", 
        style=discord.TextStyle.paragraph,
        min_length=10,
        required=True
    )
    tipo_arma = discord.ui.TextInput(
        label="Tipologia di Arma prevista", 
        placeholder="Es. Glock-17, MP5, G36", 
        min_length=3,
        required=True
    )
    sanzioni_precedenti = discord.ui.TextInput(
        label="Sanzioni o Precedenti RP", 
        placeholder="Es. Nessuna sanzione / Nessun precedente", 
        min_length=2,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        nome_rp_inserito = self.nome_rp.value.strip()
        nome_rp_ufficiale = nomi_rp_registrati.get(interaction.user.id) or interaction.user.nick or interaction.user.display_name

        if nomi_rp_registrati.get(interaction.user.id) and nome_rp_inserito != nome_rp_ufficiale:
            await interaction.response.send_message(
                f"❌ **NOME RP NON CORRISPONDENTE!**\n"
                f"Il nome inserito (`{nome_rp_inserito}`) **NON è identico** al tuo Nome RP approvato con la Cittadinanza (`{nome_rp_ufficiale}`).\n"
                f"Devi scriverlo **esattamente uguale** rispettando maiuscole, minuscole e spazi!",
                ephemeral=True
            )
            return

        ruolo_armi = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)

        if ruolo_armi and ruolo_armi in interaction.user.roles:
            await interaction.response.send_message(
                "❌ **NON PUOI RICHIEDERLO!** Sei già in possesso della licenza di Porto d'Armi!",
                ephemeral=True
            )
            return

        ok_cooldown, minuti_attesa = controlla_cooldown_rifiuto(interaction.user.id, "Porto d'Armi")
        if not ok_cooldown:
            await interaction.response.send_message(
                f"⏱️ **RICHIESTA RIFIUTATA DI RECENTE!**\nDevi attendere ancora **{minuti_attesa} minuti** prima di poter richiedere nuovamente il **Porto d'Armi**.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "✅ La tua richiesta per il Porto d'Armi è stata inoltrata alla Polizia di Stato!", 
            ephemeral=True
        )

        canale_staff = interaction.guild.get_channel(ID_CANALE_ACCETTAZIONE_STAFF) or interaction.channel

        embed = discord.Embed(
            title="🔫 NUOVA RICHIESTA PORTO D'ARMI",
            color=discord.Color.red()
        )
        embed.add_field(name="Utente Discord", value=interaction.user.mention, inline=False)
        embed.add_field(name="Nome RP", value=nome_rp_inserito, inline=True)
        embed.add_field(name="Tipo Arma", value=self.tipo_arma.value, inline=True)
        embed.add_field(name="Sanzioni / Precedenti", value=self.sanzioni_precedenti.value, inline=True)
        embed.add_field(name="Motivazione", value=self.motivo_richiesta.value, inline=False)

        await canale_staff.send(
            embed=embed, 
            view=ViewGestioneGenerica(
                utente=interaction.user, 
                nome_rp_inserito=nome_rp_inserito,
                tipo_documento="Porto d'Armi", 
                id_ruolo=ID_RUOLO_PORTO_DARMI,
                dettagli={
                    "Tipo Arma": self.tipo_arma.value,
                    "Sanzioni / Precedenti": self.sanzioni_precedenti.value,
                    "Motivazione": self.motivo_richiesta.value
                }
            )
        )


# ==========================================
# ⚙️ BOTTONI DI APPROVAZIONE STAFF
# ==========================================
class ViewGestioneGenerica(discord.ui.View):
    def __init__(self, utente, nome_rp_inserito, tipo_documento, id_ruolo=None, dettagli=None):
        super().__init__(timeout=None)
        self.utente = utente
        self.nome_rp_inserito = nome_rp_inserito
        self.tipo_documento = tipo_documento
        self.id_ruolo = id_ruolo
        self.dettagli = dettagli or {}

    @discord.ui.button(label="Approva ✅", style=discord.ButtonStyle.success)
    async def accetta(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.id_ruolo:
            ruolo = interaction.guild.get_role(self.id_ruolo)
            if ruolo:
                try:
                    await self.utente.add_roles(ruolo)
                except Exception:
                    pass

        forum_channel = interaction.guild.get_channel(ID_FORUM_DOCUMENTI)
        if forum_channel and isinstance(forum_channel, discord.ForumChannel):
            embed_doc = discord.Embed(
                title=f"📋 REGISTRAZIONE {self.tipo_documento.upper()}",
                description=f"Documento rilasciato con successo a {self.utente.mention}.",
                color=discord.Color.green() if "Patente" in self.tipo_documento else discord.Color.red()
            )
            embed_doc.add_field(name="Titolare RP", value=self.nome_rp_inserito, inline=False)
            
            for chiave, valore in self.dettagli.items():
                embed_doc.add_field(name=chiave, value=valore, inline=True)
                
            embed_doc.set_footer(text=f"Approvato da: {interaction.user.display_name}")

            prefisso = "🚗" if "Patente" in self.tipo_documento else "🔫"
            await forum_channel.create_thread(
                name=f"{prefisso} {self.tipo_documento} - {self.nome_rp_inserito}",
                embed=embed_doc
            )

        await interaction.response.send_message(f"✅ {self.tipo_documento} approvata per {self.utente.mention}! Ruolo assegnato e post pubblicato nel forum.", ephemeral=False)
        try:
            await self.utente.send(f"🎉 La tua richiesta per **{self.tipo_documento}** su **Puglia RP** è stata **APPROVATA**!")
        except Exception:
            pass
        self.stop()

    @discord.ui.button(label="Rifiuta ❌", style=discord.ButtonStyle.danger)
    async def rifiuta(self, interaction: discord.Interaction, button: discord.ui.Button):
        cooldowns_rifiuti[(self.utente.id, self.tipo_documento)] = datetime.datetime.now() + datetime.timedelta(minutes=10)

        await interaction.response.send_message(f"❌ {self.tipo_documento} rifiutata per {self.utente.mention}. Potrà riprovare tra 10 minuti.", ephemeral=False)
        try:
            await self.utente.send(f"❌ La tua richiesta per **{self.tipo_documento}** su **Puglia RP** è stata **RIFIUTATA**. Potrai riprovare tra **10 minuti**.")
        except Exception:
            pass
        self.stop()

# ==========================================
# 🚨 SISTEMA ARRESTI E MULTE (STAFF / FORZE DELL'ORDINE)
# ==========================================

# --- COMANDO /arresta ---
@bot.tree.command(name="arresta", description="Emetti un mandato di arresto per un utente")
@app_commands.describe(
    utente="L'utente da arrestare",
    durata="Durata della pena (es. 1 giorno, 3 giorni, 12 ore)",
    motivo="Motivazione dettagliata dell'arresto"
)
async def arresta_cmd(interaction: discord.Interaction, utente: discord.Member, durata: str, motivo: str):
    await interaction.response.defer(ephemeral=True)

    canale_arresti = interaction.guild.get_channel(ID_CANALE_REGISTRO_ARRESTI)
    if not canale_arresti:
        await interaction.followup.send("❌ Canale registro arresti non trovato!", ephemeral=True)
        return

    # Creazione Embed Arresto
    embed = discord.Embed(
        title="🚨 REGISTRO ARRESTI — PUGLIA RP",
        color=discord.Color.dark_red(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="👤 Utente Arrestato", value=utente.mention, inline=True)
    embed.add_field(name="👮 Agente / Staff", value=interaction.user.mention, inline=True)
    embed.add_field(name="⏱️ Durata Pena", value=f"`{durata}`", inline=False)
    embed.add_field(name="📋 Motivazione", value=f"```{motivo}```", inline=False)

    if utente.display_avatar:
        embed.set_thumbnail(url=utente.display_avatar.url)

    embed.set_footer(
        text="Puglia RP • Sistema Giudiziario",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    # Invio nel canale registro
    await canale_arresti.send(embed=embed)

    await interaction.followup.send(
        f"✅ Arresto registrato con successo per {utente.mention} nel canale dedicato.",
        ephemeral=True
    )


# --- COMANDO /multa ---
@bot.tree.command(name="multa", description="Emetti una sanzione pecuniaria (multa) a un utente")
@app_commands.describe(
    utente="L'utente a cui infliggere la multa",
    importo="Importo in denaro (es. 500, 1500...)",
    motivo="Motivazione della sanzione (es. Guida pericolosa)"
)
async def multa_cmd(interaction: discord.Interaction, utente: discord.Member, importo: int, motivo: str):
    await interaction.response.defer(ephemeral=True)

    canale_multe = interaction.guild.get_channel(ID_CANALE_REGISTRO_MULTE)
    if not canale_multe:
        await interaction.followup.send("❌ Canale registro multe non trovato!", ephemeral=True)
        return

    # Creazione Embed Multa
    embed = discord.Embed(
        title="💸 NOTIFICA DI SANZIONE / MULTA — PUGLIA RP",
        color=discord.Color.from_rgb(230, 126, 34),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="👤 Sanzionato", value=utente.mention, inline=True)
    embed.add_field(name="👮 Emessa da", value=interaction.user.mention, inline=True)
    embed.add_field(name="💰 Importo", value=f"**€ {importo:,}**", inline=False)
    embed.add_field(name="📋 Motivazione", value=f"```{motivo}```", inline=False)

    if utente.display_avatar:
        embed.set_thumbnail(url=utente.display_avatar.url)

    embed.set_footer(
        text="Puglia RP • Motorizzazione & Forze dell'Ordine",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    # Invio nel canale registro
    await canale_multe.send(embed=embed)

    await interaction.followup.send(
        f"✅ Multa di **€ {importo}** emessa con successo a {utente.mention}.",
        ephemeral=True
    )


# ==========================================
# 🚨 SISTEMA REVOCA DOCUMENTI / STAFF (ADMIN ONLY)
# ==========================================
@bot.tree.command(name="revoca-documento", description="Revoca un documento o l'identificazione Staff a un utente")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    utente="L'utente a cui revocare il documento/identificazione",
    tipo="Cosa desideri revocare"
)
@app_commands.choices(tipo=[
    app_commands.Choice(name="🆔 Identificazione Staff", value="staff"),
    app_commands.Choice(name="🇮🇹 Cittadinanza", value="cittadinanza"),
    app_commands.Choice(name="🚗 Patente A", value="patente_a"),
    app_commands.Choice(name="🚗 Patente B", value="patente_b"),
    app_commands.Choice(name="🚗 Patente C", value="patente_c"),
    app_commands.Choice(name="🚗 Patente D", value="patente_d"),
    app_commands.Choice(name="🔫 Porto d'Armi", value="armi")
])
async def revoca_slash(interaction: discord.Interaction, utente: discord.Member, tipo: app_commands.Choice[str]):
    try:
        await interaction.response.defer(ephemeral=True)

        STAFF_ROLE_ID = 1562507751975035065

        # --- 1. REVOCA IDENTIFICAZIONE STAFF ---
        if tipo.value == "staff":
            role_staff = interaction.guild.get_role(STAFF_ROLE_ID)
            if role_staff and role_staff in utente.roles:
                try:
                    await utente.remove_roles(role_staff)
                except Exception as e:
                    print(f"Errore rimozione ruolo: {e}")

            data = load_data()
            user_id_str = str(utente.id)
            if user_id_str in data.get("users", {}):
                del data["users"][user_id_str]
                save_data(data)

            embed = discord.Embed(
                title="⚠️ IDENTIFICAZIONE STAFF REVOCATA",
                description=f"L'identificazione Staff di {utente.mention} è stata revocata con successo.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # --- 2. REVOCA CITTADINANZA, PATENTI O PORTO D'ARMI ---
        ruolo_da_rimuovere = None
        nome_doc = tipo.name

        if tipo.value == "cittadinanza":
            ruolo_da_rimuovere = interaction.guild.get_role(ID_RUOLO_CITTADINO)
            if utente.id in nomi_rp_registrati:
                del nomi_rp_registrati[utente.id]

        elif tipo.value.startswith("patente_"):
            lettera = tipo.value.split("_")[1].upper()
            ruolo_da_rimuovere = interaction.guild.get_role(RUOLI_PATENTI.get(lettera))

        elif tipo.value == "armi":
            ruolo_da_rimuovere = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)

        if ruolo_da_rimuovere and ruolo_da_rimuovere in utente.roles:
            try:
                await utente.remove_roles(ruolo_da_rimuovere)
            except Exception as e:
                print(f"Errore rimozione ruolo documento: {e}")

        embed = discord.Embed(
            title="🚫 REVOCA DOCUMENTO",
            description=f"È stata revocata la voce: **{nome_doc}** a {utente.mention}.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as err:
        print(f"Errore durante l'esecuzione di /revoca: {err}")
        try:
            await interaction.followup.send(f"❌ **Si è verificato un errore:** `{err}`", ephemeral=True)
        except Exception:
            pass


# ==========================================
# 🎛️ PANNELLO PRINCIPALE UTENTI (HALLOWEEN EDITION)
# ==========================================
class PannelloPugliaRP(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📜 Richiedi Cittadinanza", style=discord.ButtonStyle.primary, custom_id="btn_cittadinanza")
    async def btn_cittadinanza(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalCittadinanza())

    @discord.ui.button(label="🚗 Richiedi Patente (A/B/C/D)", style=discord.ButtonStyle.secondary, custom_id="btn_patente")
    async def btn_patente(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalPatente())

    @discord.ui.button(label="🔫 Porto d'Armi", style=discord.ButtonStyle.danger, custom_id="btn_armi")
    async def btn_armi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalPortoDArmi())


def crea_embed_halloween(bot_user):
    embed = discord.Embed(
        title="🎃 CENTRO SERVIZI PUGLIA RP - HALLOWEEN EDITION 👻",
        description=(
            "🕸️ **Benvenuto nella Motorizzazione & Anagrafe Ufficiale!**\n"
            "Clicca sui pulsanti in basso per inviare le tue richieste ufficiali."
        ),
        color=discord.Color.from_rgb(230, 126, 34)  # Arancione Halloween
    )
    
    if bot_user and bot_user.display_avatar:
        embed.set_thumbnail(url=bot_user.display_avatar.url)

    embed.add_field(
        name="📜 1. Cittadinanza Ufficiale",
        value=(
            "• **Descrizione:** Registrazione all'Anagrafe del server.\n"
            "• **Requisiti:** Inserisci Nome e Cognome RP realistici."
        ),
        inline=False
    )

    embed.add_field(
        name="🚗 2. Licenza di Guida / Patenti (A, B, C, D)",
        value=(
            "• **Descrizione:** Registrazione veicolo e licenza di guida.\n"
            "• **Categorie:** 🛵 **A** (Moto) | 🚗 **B** (Auto) | 🚚 **C** (Camion) | 🚌 **D** (Bus)\n"
            "• **Nota:** Il Nome RP deve essere **identico** alla Cittadinanza!"
        ),
        inline=False
    )

    embed.add_field(
        name="🔫 3. Licenza Porto d'Armi",
        value=(
            "• **Descrizione:** Licenza per detenzione e uso armi legale.\n"
            "• **Requisiti:** Visita psicofisica idonea e motivazione RP."
        ),
        inline=False
    )

    embed.add_field(
        name="⚠️ Regolamento e Note Importanti",
        value=(
            "1️⃣ Assicurati di non possedere già il documento.\n"
            "2️⃣ In caso di **rifiuto**, attendere **10 minuti di cooldown**.\n"
            "3️⃣ Compila i moduli con serietà: no troll o nomi irrealistici."
        ),
        inline=False
    )

    embed.set_footer(
        text="🦇 Puglia RP - Sistema Automazione Documenti • Dolcetto o Scherzetto? 🎃",
        icon_url=bot_user.display_avatar.url if bot_user and bot_user.display_avatar else None
    )
    return embed


@bot.tree.command(name="pannello", description="Manda il pannello principale per i documenti (Halloween Edition)")
@app_commands.checks.has_permissions(administrator=True)
async def pannello_slash(interaction: discord.Interaction):
    embed = crea_embed_halloween(bot.user)
    await interaction.response.send_message(embed=embed, view=PannelloPugliaRP())


@bot.command(name="pannello")
@commands.has_permissions(administrator=True)
async def pannello_prefisso(ctx):
    embed = crea_embed_halloween(bot.user)
    await ctx.send(embed=embed, view=PannelloPugliaRP())


# ==========================================
# 🚀 AVVIO E SINCRONIZZAZIONE COMANDI SLASH
# ==========================================
@bot.event
async def on_ready():
    print(f'🤖 Bot connesso come {bot.user}')

    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"⚡ Sincronizzati istantaneamente {len(synced)} comandi slash nel server: {guild.name}")
        except Exception as e:
            print(f"❌ Errore sincronizzazione su {guild.name}: {e}")

    print('✅ Il bot di Puglia RP è ONLINE e pronto!')

    # Avvio sicuro del task per il reset del lunedì
    if not monday_reset_task.is_running():
        monday_reset_task.start()

TOKEN = "MTU2MjU3Mjg4MjQxNDkyNzg3Mw.GEEuWu.NaQWmZYnB3UVMzHY-f5aSGYsy4hlRHD8JxJTZk"

@bot.tree.command(name="sessione", description="Annuncia l'apertura della sessione di Puglia RP con grafica avanzata")
@app_commands.describe(codice="Il codice di accesso della sessione", banner="Link opzionale di un'immagine o banner da mettere in grande")
async def sessione(interaction: discord.Interaction, codice: str, banner: str = None):
    
    class VistaSessionePuglia(discord.ui.View):
        def __init__(self, cod: str):
            super().__init__(timeout=None)
            self.cod = cod

        @discord.ui.button(label="Copia Codice", style=discord.ButtonStyle.success, emoji="📋")
        async def fa_copia_codice(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(
                f"Ecco il codice pronto da copiare: `{self.cod}`", 
                ephemeral=True
            )

    embed = discord.Embed(
        title="🌾 𝐏𝐔𝐆𝐋𝐈𝐀 𝐑𝐎𝐋𝐄𝐏𝐋𝐀𝐘 — 𝐒𝐄𝐒𝐒𝐈𝐎𝐍𝐄 𝐀𝐏𝐄𝐑𝐓𝐀 🌾",
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 **IL SERVER È UFFICIALMENTE ONLINE!** 🔥\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚗 *Accendi i motori, raduna la tua crew e vivi la tua storia nel cuore della Puglia.* \n\n"
            f"🔑 **Codice di Accesso Rapido:** \n```ini\n[ {codice} ]\n```\n"
            "⚠️ *Ricorda di rispettare sempre il regolamento RP.*"
        ),
        color=discord.Color.from_rgb(255, 140, 0)
    )

    embed.add_field(name="👑 Host / Attivato da", value=f"{interaction.user.mention}", inline=True)
    embed.add_field(name="⏰ Orario di Apertura", value=f"<t:{int(discord.utils.utcnow().timestamp())}:f>", inline=True)
    
    if banner:
        embed.set_image(url=banner)

    embed.set_footer(
        text="PUGLIA RP • Sistema di Gestione Ufficiale", 
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    await interaction.response.send_message(
        content="@here 🚨 **ATTENZIONE! LA SESSIONE DI PUGLIA RP È APPENA PARTITA!** 🚨", 
        embed=embed, 
        view=VistaSessionePuglia(codice)
    )
    
# --- COMANDO /sessione ---
# --- COMANDO /sessione-offline ---
@bot.tree.command(name="sessione-offline", description="Manda direttamente l'annuncio di sessione offline")
async def sessione_offline(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚪ SESSIONE ROLEPLAY OFFLINE",
        description="La sessione di Roleplay su **Puglia RP** è attualmente **OFFLINE**.\n\nTutte le azioni RP fuori sessione sono sospese.",
        color=discord.Color.dark_gray()
    )
    embed.add_field(name="📢 Stato", value="OFFLINE", inline=True)
    embed.set_footer(text="Puglia RP • Restate sintonizzati per la prossima apertura!")

    await interaction.response.send_message(embed=embed)

import json
import asyncio
import urllib.request
import urllib.parse
from datetime import datetime, time, timezone, timedelta
import discord
from discord import app_commands, ui
from discord.ext import tasks

# ==========================================
# CONFIGURAZIONE ID PUGLIA RP
# ==========================================
ROLE_STAFF_BASE_ID = 1524685130399219842
ROLE_STAFF_IDENTIFICATO_ID = 1562507751975035065

LOG_CHANNEL_ID = 1563153373619027989
LEADERBOARD_CHANNEL_ID = 1563153429512065115
ALLOWED_SERVIZIO_CHANNEL_ID = 1563153684542656613

DATA_FILE = "staff_data.json"

# ==========================================
# GESTIONE DATABASE E API ROBLOX
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "active_sessions": {}, "weekly_minutes": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "users" not in data: data["users"] = {}
            if "active_sessions" not in data: data["active_sessions"] = {}
            if "weekly_minutes" not in data: data["weekly_minutes"] = {}
            return data
    except Exception:
        return {"users": {}, "active_sessions": {}, "weekly_minutes": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_roblox_avatar(roblox_username):
    try:
        req_user_data = json.dumps({"usernames": [roblox_username], "excludeBannedUsers": False}).encode("utf-8")
        req_user = urllib.request.Request(
            "https://users.roblox.com/v1/usernames/users",
            data=req_user_data,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req_user, timeout=5) as response:
            res_user = json.loads(response.read().decode("utf-8"))
            if not res_user.get("data") or len(res_user["data"]) == 0:
                return None
            user_id = res_user["data"][0]["id"]

        thumb_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false"
        req_thumb = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_thumb, timeout=5) as response:
            res_thumb = json.loads(response.read().decode("utf-8"))
            if res_thumb.get("data") and len(res_thumb["data"]) > 0:
                return res_thumb["data"][0]["imageUrl"]
    except Exception as e:
        print(f"[Roblox API] Errore nel recupero avatar per {roblox_username}: {e}")
    return None

def format_minutes(total_minutes):
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

# ==========================================
# MODALE E BOTTONI PER IDENTIFICAZIONE
# ==========================================
class IdentificationModal(discord.ui.Modal, title="Identificazione Staff Puglia RP"):
    roblox_name = discord.ui.TextInput(
        label="Nome Utente Roblox",
        placeholder="Inserisci il tuo nome utente esatto di Roblox",
        required=True
    )
    rp_name = discord.ui.TextInput(
        label="Nome e Cognome RP",
        placeholder="Es: Mario Rossi",
        required=True
    )
    rank = discord.ui.TextInput(
        label="Grado Staff",
        placeholder="Es: Helper, Moderatore, Admin...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id_str = str(interaction.user.id)
        data = load_data()

        # Salvataggio dati
        data["users"][user_id_str] = {
            "discord_name": interaction.user.name,
            "roblox_name": self.roblox_name.value,
            "rp_name": self.rp_name.value,
            "rank": self.rank.value,
            "total_seconds": 0
        }
        save_data(data)

        # Assegnazione Ruolo "Staff Identificato"
        ROLE_STAFF_IDENTIFICATO_ID = 1562507751975035065
        role = interaction.guild.get_role(ROLE_STAFF_IDENTIFICATO_ID)
        if role:
            try:
                await interaction.user.add_roles(role)
            except Exception as e:
                print(f"Errore nell'assegnare il ruolo: {e}")

        # Creazione Embed per il Post del Forum
        embed = discord.Embed(
            title="🆔 NUOVA IDENTIFICAZIONE STAFF",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 Utente", value=interaction.user.mention, inline=True)
        embed.add_field(name="🎮 Roblox", value=f"`{self.roblox_name.value}`", inline=True)
        embed.add_field(name="🎭 Nome RP", value=self.rp_name.value, inline=True)
        embed.add_field(name="⭐ Grado", value=self.rank.value, inline=False)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Puglia RP • Sistema Identificazione Staff")

        # Invio nel Canale Forum
        FORUM_LOG_STAFF_ID = 1563176554786463894
        forum_channel = interaction.guild.get_channel(FORUM_LOG_STAFF_ID)

        if forum_channel and isinstance(forum_channel, discord.ForumChannel):
            # Crea un nuovo post nel forum
            thread_title = f"🆔 Identificazione - {self.rp_name.value} ({interaction.user.name})"
            await forum_channel.create_thread(
                name=thread_title,
                embed=embed
            )

        # Risposta privata all'utente
        await interaction.followup.send(
            "✅ **Identificazione completata con successo!** Dati salvati e post creato nei Log Staff.",
            ephemeral=True
        )

# ==========================================
# EVENTO ASSEGNAZIONE RUOLO STAFF BASE
# ==========================================
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    had_role = any(r.id == ROLE_STAFF_BASE_ID for r in before.roles)
    has_role = any(r.id == ROLE_STAFF_BASE_ID for r in after.roles)

    if not had_role and has_role:
        try:
            embed_welcome = discord.Embed(
                title="🌟 BENVENUTO NEL TEAM STAFF DI PUGLIA RP!",
                description=(
                    f"Ciao **{after.display_name}**, benvenuto nello Staff di **Puglia RP**!\n\n"
                    "⚠️ **ATTENZIONE:** Per poter iniziare a svolgere il servizio Staff è **obbligatorio** effettuare l'identificazione.\n"
                    "Clicca sul pulsante qui sotto per inserire i tuoi dati."
                ),
                color=discord.Color.gold()
            )
            embed_welcome.set_footer(text="Puglia RP • Servizio Gestione Staff")
            await after.send(embed=embed_welcome, view=DMIdentificationView())
        except discord.Forbidden:
            print(f"Impossibile inviare DM a {after.display_name}: DM chiusi.")

# ==========================================
# PANNELLO SERVIZIO STAFF & BOTTONI
# ==========================================
class ServiceControlView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

    async def check_user(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Questo pannello di servizio appartiene a un altro staffer!", ephemeral=True)
            return False
        return True

    @ui.button(label="Apri Servizio", style=discord.ButtonStyle.success, emoji="🟢", custom_id="btn_apri_servizio")
    async def apri_servizio(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_user(interaction): return
        data = load_data()
        user_str = self.user_id

        if user_str in data["active_sessions"] and data["active_sessions"][user_str]["status"] == "active":
            await interaction.response.send_message("⚠️ Il tuo servizio staff è già **ATTIVO**!", ephemeral=True)
            return

        now_iso = datetime.utcnow().isoformat()
        if user_str in data["active_sessions"] and data["active_sessions"][user_str]["status"] == "paused":
            data["active_sessions"][user_str]["status"] = "active"
            data["active_sessions"][user_str]["last_start"] = now_iso
            msg_action = "▶️ Servizio Staff **RIPRESO** con successo!"
            log_title = "▶️ SERVIZIO STAFF RIPRESO"
            log_color = discord.Color.green()
        else:
            data["active_sessions"][user_str] = {
                "status": "active",
                "start_time": now_iso,
                "last_start": now_iso,
                "accumulated_seconds": 0
            }
            msg_action = "🟢 Servizio Staff **APERTO** con successo!"
            log_title = "🟢 SERVIZIO STAFF APERTO"
            log_color = discord.Color.green()

        save_data(data)
        await interaction.response.send_message(msg_action, ephemeral=True)

        log_chan = interaction.guild.get_channel(LOG_CHANNEL_ID) if interaction.guild else None
        if log_chan:
            user_info = data["users"].get(user_str, {})
            embed_log = discord.Embed(title=log_title, color=log_color, timestamp=datetime.now(timezone.utc))
            embed_log.add_field(name="👤 Staffer", value=interaction.user.mention, inline=True)
            embed_log.add_field(name="🎮 Roblox", value=user_info.get("roblox_name", "N/D"), inline=True)
            embed_log.add_field(name="⭐ Grado", value=user_info.get("grado", "N/D"), inline=True)
            embed_log.set_footer(text="Puglia RP • Log Servizio Staff")
            await log_chan.send(embed=embed_log)

    @ui.button(label="Metti in Pausa", style=discord.ButtonStyle.secondary, emoji="⏸️", custom_id="btn_pausa_servizio")
    async def pausa_servizio(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_user(interaction): return
        data = load_data()
        user_str = self.user_id

        if user_str not in data["active_sessions"] or data["active_sessions"][user_str]["status"] == "offline":
            await interaction.response.send_message("❌ Non hai un servizio attivo da mettere in pausa!", ephemeral=True)
            return

        if data["active_sessions"][user_str]["status"] == "paused":
            await interaction.response.send_message("⚠️ Il tuo servizio è già in pausa!", ephemeral=True)
            return

        session = data["active_sessions"][user_str]
        last_start = datetime.fromisoformat(session["last_start"])
        elapsed = (datetime.utcnow() - last_start).total_seconds()
        session["accumulated_seconds"] += elapsed
        session["status"] = "paused"
        save_data(data)

        await interaction.response.send_message("⏸️ Servizio Staff **MESSO IN PAUSA**.", ephemeral=True)

        log_chan = interaction.guild.get_channel(LOG_CHANNEL_ID) if interaction.guild else None
        if log_chan:
            user_info = data["users"].get(user_str, {})
            embed_log = discord.Embed(title="⏸️ SERVIZIO STAFF IN PAUSA", color=discord.Color.gold(), timestamp=datetime.now(timezone.utc))
            embed_log.add_field(name="👤 Staffer", value=interaction.user.mention, inline=True)
            embed_log.add_field(name="⏱️ Tempo Parziale", value=format_minutes(session["accumulated_seconds"] / 60), inline=True)
            embed_log.set_footer(text="Puglia RP • Log Servizio Staff")
            await log_chan.send(embed=embed_log)

    @ui.button(label="Chiudi Servizio", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="btn_chiudi_servizio")
    async def chiudi_servizio(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_user(interaction): return
        data = load_data()
        user_str = self.user_id

        if user_str not in data["active_sessions"] or data["active_sessions"][user_str]["status"] == "offline":
            await interaction.response.send_message("❌ Non hai un servizio attivo da chiudere!", ephemeral=True)
            return

        session = data["active_sessions"][user_str]
        total_seconds = session.get("accumulated_seconds", 0)

        if session["status"] == "active":
            last_start = datetime.fromisoformat(session["last_start"])
            total_seconds += (datetime.utcnow() - last_start).total_seconds()

        session_minutes = total_seconds / 60.0
        data["weekly_minutes"][user_str] = data["weekly_minutes"].get(user_str, 0) + session_minutes
        del data["active_sessions"][user_str]
        save_data(data)

        formatted_time = format_minutes(session_minutes)
        formatted_total = format_minutes(data["weekly_minutes"][user_str])

        await interaction.response.send_message(
            f"🔴 Servizio Staff **CHIUSO**.\n"
            f"⏱️ Tempo sessione: **{formatted_time}**\n"
            f"📊 Totale settimana: **{formatted_total}**",
            ephemeral=True
        )

        log_chan = interaction.guild.get_channel(LOG_CHANNEL_ID) if interaction.guild else None
        if log_chan:
            user_info = data["users"].get(user_str, {})
            embed_log = discord.Embed(title="🔴 SERVIZIO STAFF CHIUSO", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
            embed_log.add_field(name="👤 Staffer", value=interaction.user.mention, inline=True)
            embed_log.add_field(name="🎮 Roblox", value=user_info.get("roblox_name", "N/D"), inline=True)
            embed_log.add_field(name="⏱️ Sessione", value=formatted_time, inline=True)
            embed_log.add_field(name="📊 Totale Settimanale", value=formatted_total, inline=True)
            embed_log.set_footer(text="Puglia RP • Log Servizio Staff")
            await log_chan.send(embed=embed_log)

# ==========================================
# 💰 FUNZIONI HELPER ECONOMIA
# ==========================================
def get_user_eco(user_id_str):
    data = load_data()
    if "economy" not in data:
        data["economy"] = {}
    if user_id_str not in data["economy"]:
        data["economy"][user_id_str] = {
            "bank": 0,
            "cash": 0,
            "has_account": False
        }
        save_data(data)
    return data["economy"][user_id_str]

def update_user_eco(user_id_str, eco_data):
    data = load_data()
    if "economy" not in data:
        data["economy"] = {}
    data["economy"][user_id_str] = eco_data
    save_data(data)

# ==========================================
# 💳 PANNELLO & VISTA CONTO BANCARIO
# ==========================================
class ModalApriConto(discord.ui.Modal, title="🏦 Apertura Conto Corrente - Puglia RP"):
    nome_cognome = discord.ui.TextInput(
        label="Nome e Cognome RP",
        placeholder="Es. Mario Rossi",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        eco = get_user_eco(user_id_str)

        if eco.get("has_account"):
            await interaction.followup.send("❌ **Possiedi già un conto corrente attivo!**", ephemeral=True)
            return

        # Bonus iniziale di 1000 in banca
        eco["bank"] += 1000
        eco["has_account"] = True
        update_user_eco(user_id_str, eco)

        embed = discord.Embed(
            title="🏦 CONTO BANCARIO APERTO CON SUCCESSO!",
            description=(
                f"Congratulazioni **{self.nome_cognome.value}**! Il tuo conto corrente presso la Banca di Puglia RP è stato attivato.\n\n"
                f"🎁 **Bonus di benvenuto:** `€ 1.000` accreditati sul tuo conto!"
            ),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Banca di Puglia RP • Gestione Finanziaria")
        await interaction.followup.send(embed=embed, ephemeral=True)


class VistaContoBancario(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💳 Apri Conto Bancario", style=discord.ButtonStyle.success, custom_id="btn_apri_conto")
    async def btn_apri_conto(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id_str = str(interaction.user.id)
        eco = get_user_eco(user_id_str)

        if eco.get("has_account"):
            await interaction.response.send_message("❌ **Hai già aperto un conto corrente bancario!**", ephemeral=True)
            return

        await interaction.response.send_modal(ModalApriConto())

# ==========================================
# 💰 COMANDI SLASH ECONOMIA & BANCA
# ==========================================

# --- COMANDO /pannello-contobancario (ADMIN ONLY) ---
@bot.tree.command(name="pannello-contobancario", description="Invia il pannello per l'apertura del conto bancario")
@app_commands.checks.has_permissions(administrator=True)
async def pannello_conto_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏦 BANCA DI PUGLIA RP — APERTURA CONTO",
        description=(
            "Benvenuto nel servizio bancario ufficiale di **Puglia RP**!\n\n"
            "• **Apertura Conto:** Clicca sul pulsante sottostante per registrare il tuo conto corrente.\n"
            "• **Bonus Benvenuto:** Riceverai subito **€ 1.000** di credito sul tuo saldo bancario.\n"
            "• **Servizi:** Potrai depositare, prelevare contanti e trasferire denaro agli altri cittadini."
        ),
        color=discord.Color.gold()
    )
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.set_footer(text="Puglia RP • Servizi Finanziari Ufficiali")

    await interaction.response.send_message(embed=embed, view=VistaContoBancario())


# --- COMANDO /saldo ---
@bot.tree.command(name="saldo", description="Visualizza il tuo saldo bancario e i contanti in tuo possesso")
async def saldo_cmd(interaction: discord.Interaction, utente: discord.Member = None):
    target = utente or interaction.user
    eco = get_user_eco(str(target.id))

    embed = discord.Embed(
        title=f"💰 PORTAFOGLIO & CONTO — {target.display_name}",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="💵 Contanti", value=f"`€ {eco['cash']:,}`", inline=True)
    embed.add_field(name="🏦 Saldo Bancario", value=f"`€ {eco['bank']:,}`", inline=True)
    embed.add_field(name="💳 Stato Conto", value="✅ Attivo" if eco["has_account"] else "❌ Non Attivo", inline=False)

    if target.display_avatar:
        embed.set_thumbnail(url=target.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- COMANDO /preleva ---
@bot.tree.command(name="preleva", description="Preleva denaro dal tuo conto bancario per metterlo in contanti")
@app_commands.describe(importo="Quantità di denaro da prelevare dal conto")
async def preleva_cmd(interaction: discord.Interaction, importo: int):
    if importo <= 0:
        await interaction.response.send_message("❌ Inserisci un importo valido positivo!", ephemeral=True)
        return

    user_id_str = str(interaction.user.id)
    eco = get_user_eco(user_id_str)

    if not eco.get("has_account"):
        await interaction.response.send_message("❌ Non possiedi un conto bancario attivo! Apri prima un conto.", ephemeral=True)
        return

    if eco["bank"] < importo:
        await interaction.response.send_message(f"❌ Saldo insufficiente! Sul conto hai solo **€ {eco['bank']:,}**.", ephemeral=True)
        return

    eco["bank"] -= importo
    eco["cash"] += importo
    update_user_eco(user_id_str, eco)

    await interaction.response.send_message(
        f"🏧 **PRELIEVO EFFETTUATO!**\nHai prelevato **€ {importo:,}** dal conto bancario.\n"
        f"• Saldo Banco Rimasto: `€ {eco['bank']:,}`\n• Contanti attuali: `€ {eco['cash']:,}`",
        ephemeral=True
    )


# --- COMANDO /deposita ---
@bot.tree.command(name="deposita", description="Deposita contanti sul tuo conto corrente bancario")
@app_commands.describe(importo="Quantità di denaro da versare in banca")
async def deposita_cmd(interaction: discord.Interaction, importo: int):
    if importo <= 0:
        await interaction.response.send_message("❌ Inserisci un importo valido positivo!", ephemeral=True)
        return

    user_id_str = str(interaction.user.id)
    eco = get_user_eco(user_id_str)

    if not eco.get("has_account"):
        await interaction.response.send_message("❌ Non possiedi un conto bancario attivo!", ephemeral=True)
        return

    if eco["cash"] < importo:
        await interaction.response.send_message(f"❌ Non hai abbastanza contanti! In tasca hai solo **€ {eco['cash']:,}**.", ephemeral=True)
        return

    eco["cash"] -= importo
    eco["bank"] += importo
    update_user_eco(user_id_str, eco)

    await interaction.response.send_message(
        f"🏦 **DEPOSITO EFFETTUATO!**\nHai versato **€ {importo:,}** sul conto corrente.\n"
        f"• Saldo Banco Attuale: `€ {eco['bank']:,}`\n• Contanti rimasti: `€ {eco['cash']:,}`",
        ephemeral=True
    )


# --- COMANDO /paga (PRIVATO / EFFIMERO) ---
@bot.tree.command(name="paga", description="Paga o dai contanti ad un altro cittadino in RP")
@app_commands.describe(
    destinatario="Cittadino a cui dare i contanti",
    importo="Quantità di denaro da consegnare"
)
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
        await interaction.response.send_message(f"❌ Non hai abbastanza contanti in tasca! Disponibili: **€ {eco_mittente['cash']:,}**.", ephemeral=True)
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
    
    # Invia il messaggio impostando ephemeral=True così lo vede solo chi usa il comando
    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- COMANDO /aggiungi-soldi (ADMIN ONLY) ---
@bot.tree.command(name="aggiungi-soldi", description="Aggiungi denaro a un utente (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    utente="L'utente a cui aggiungere denaro",
    importo="Somma da aggiungere",
    dove="Dove aggiungere i soldi ('bank' o 'cash')"
)
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
    await interaction.response.send_message(
        f"✅ Aggiunti **€ {importo:,}** in **{luogo}** per {utente.mention}.",
        ephemeral=True
    )



# ==========================================
# COMANDO /servizio
# ==========================================
@bot.tree.command(name="servizio", description="Apri il tuo pannello personale di gestione Servizio Staff")
async def servizio_cmd(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_SERVIZIO_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ Questo comando può essere eseguito solo nel canale dedicato: <#{ALLOWED_SERVIZIO_CHANNEL_ID}>!",
            ephemeral=True
        )
        return

    has_identificativo = any(r.id == ROLE_STAFF_IDENTIFICATO_ID for r in interaction.user.roles)
    if not has_identificativo:
        await interaction.response.send_message(
            "❌ Non hai il ruolo **Staff Identificato**! Controlla i tuoi DM per completare l'identificazione.",
            ephemeral=True
        )
        return

    data = load_data()
    user_str = str(interaction.user.id)
    user_info = data["users"].get(user_str, {})

    roblox_name = user_info.get("roblox_name", "Non Registrato")
    rp_name = user_info.get("rp_name", "Non Registrato")
    grado = user_info.get("grado", "Staff")

    current_status = "⚪ Offline"
    if user_str in data["active_sessions"]:
        st = data["active_sessions"][user_str]["status"]
        if st == "active": current_status = "🟢 In Servizio"
        elif st == "paused": current_status = "⏸️ In Pausa"

    total_min = data["weekly_minutes"].get(user_str, 0)
    formatted_total = format_minutes(total_min)

    embed = discord.Embed(
        title="🛡️ PANNELLO SERVIZIO STAFF",
        description=f"Benvenuto nel tuo pannello personale, **{interaction.user.mention}**.\nUsa i pulsanti sottostanti per gestire il tuo turno.",
        color=discord.Color.blue()
    )
    embed.add_field(name="🪪 Nome RP", value=rp_name, inline=True)
    embed.add_field(name="🎮 Roblox", value=roblox_name, inline=True)
    embed.add_field(name="⭐ Grado", value=grado, inline=True)
    embed.add_field(name="📢 Stato Attuale", value=f"**{current_status}**", inline=True)
    embed.add_field(name="⏱️ Ore Settimanali", value=f"**{formatted_total}**", inline=True)

    avatar_url = get_roblox_avatar(roblox_name) if roblox_name != "Non Registrato" else None
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    else:
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

    embed.set_footer(text="Puglia RP • Gestione Servizio Staff")
    await interaction.response.send_message(embed=embed, view=ServiceControlView(interaction.user.id), ephemeral=True)

# ==========================================
# COMANDO /identificami (SOLO PER STAFF BASE)
# ==========================================
@bot.tree.command(name="identificami", description="Apri il modulo di identificazione Staff di Puglia RP")
async def identificami_cmd(interaction: discord.Interaction):
    # Verifica se l'utente possiede il ruolo Staff Base
    has_staff_base = any(r.id == 1562507751975035065 for r in interaction.user.roles)
    
    if not has_staff_base:
        await interaction.response.send_message(
            "❌ **Accesso Negato:** Questo comando è riservato ai membri del team **Staff Base**!",
            ephemeral=True
        )
        return

    # Controlla se l'utente è già stato identificato
    data = load_data()
    user_id_str = str(interaction.user.id)
    
    if user_id_str in data["users"]:
        await interaction.response.send_message(
            "⚠️ Risulti già **identificato** nel sistema di Puglia RP!",
            ephemeral=True
        )
        return

    # Apre direttamente il modulo (Modal) per l'identificazione
    await interaction.response.send_modal(IdentificationModal())
    

# ==========================================
# COMANDO /leaderboard-staff
# ==========================================
@bot.tree.command(name="leaderboard-staff", description="Visualizza la classifica settimanale delle ore Staff")
async def leaderboard_cmd(interaction: discord.Interaction):
    data = load_data()
    weekly = data.get("weekly_minutes", {})

    if not weekly:
        await interaction.response.send_message("📊 Nessun dato di servizio accumulato per questa settimana.", ephemeral=True)
        return

    sorted_staff = sorted(weekly.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 LEADERBOARD SETTIMANALE STAFF",
        description="Ecco la classifica delle ore di servizio accumulate dal team staff questa settimana:",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc)
    )

    medals = ["🥇", "🥈", "🥉"]
    for idx, (u_id, minutes) in enumerate(sorted_staff[:10], start=1):
        badge = medals[idx-1] if idx <= 3 else f"**#{idx}**"
        user_info = data["users"].get(u_id, {})
        r_name = user_info.get("roblox_name", "Utente")
        rp_name = user_info.get("rp_name", "")
        grado = user_info.get("grado", "Staff")

        display_text = f"<@{u_id}> ({r_name})" if r_name != "Utente" else f"<@{u_id}>"
        embed.add_field(
            name=f"{badge} {display_text}",
            value=f"⏱️ Tempo: **{format_minutes(minutes)}** | ⭐ Grado: `{grado}`",
            inline=False
        )

    embed.set_footer(text="Puglia RP • Reset automatico ogni Lunedì a mezzanotte")
    await interaction.response.send_message(embed=embed)

# ==========================================
# COMANDO /lista-staff (VISIBILE SOLO A CHI LO ESEGUI)
# ==========================================
@bot.tree.command(name="lista-staff", description="Mostra la lista di tutti i membri dello Staff identificati")
async def lista_staff_cmd(interaction: discord.Interaction):
    data = load_data()
    users_data = data.get("users", {})

    # Controlla se ci sono utenti registrati
    if not users_data:
        await interaction.response.send_message(
            "ℹ️ **Nessun membro dello staff è attualmente identificato nel sistema.**",
            ephemeral=True
        )
        return

    # Creazione dell'Embed per la lista
    embed = discord.Embed(
        title="📋 Lista Staff Identificati - Puglia RP",
        description=f"Totale membri identificati: **{len(users_data)}**",
        color=discord.Color.blue()
    )

    # Scorre tutti gli utenti salvati e li aggiunge all'embed
    for user_id, info in users_data.items():
        discord_name = info.get("discord_name", f"<@{user_id}>")
        roblox_name = info.get("roblox_name", "N/D")
        rp_name = info.get("rp_name", "N/D")
        rank = info.get("rank", "N/D")

        field_value = (
            f"👤 **Discord:** {discord_name}\n"
            f"🎮 **Roblox:** `{roblox_name}`\n"
            f"🎭 **Nome RP:** {rp_name}\n"
            f"🎖️ **Grado:** {rank}"
        )
        
        embed.add_field(
            name=f"• Staff ID: {user_id}",
            value=field_value,
            inline=False
        )

    embed.set_footer(text="Puglia RP • Sistema Gestione Staff")
    
    # invia il messaggio in modalità ephemeral (privato solo per l'utente)
    await interaction.response.send_message(embed=embed, ephemeral=True)

    embed.set_footer(text="Puglia RP • Sistema Gestione Staff")
    
    # Invia la lista visibile a chi esegue il comando
    await interaction.response.send_message(embed=embed)

# ==========================================
# ⭐ COMANDO /recensisci-staff (VERSIONE FORUM)
# ==========================================
@bot.tree.command(name="recensisci-staff", description="Invia una recensione per un membro dello Staff di Puglia RP")
@app_commands.describe(
    staffer="Il membro dello staff da recensire",
    valutazione="Valutazione da 1 a 10 stelle",
    motivo="Motivazione o commento sulla recensione"
)
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
async def recensisci_staff_cmd(
    interaction: discord.Interaction, 
    staffer: discord.Member, 
    valutazione: app_commands.Choice[int], 
    motivo: str
):
    # Controllo canale di esecuzione
    if interaction.channel.id != ID_CANALE_COMANDO_RECENSIONI:
        await interaction.response.send_message(
            f"❌ **NON PUOI USARE QUESTO COMANDO QUI!** Puoi rilasciare recensioni solo nel canale dedicato: <#{ID_CANALE_COMANDO_RECENSIONI}>.",
            ephemeral=True
        )
        return

    # Previene il timeout di 3 secondi
    await interaction.response.defer(ephemeral=True)

    # Recupera il canale Forum
    forum_channel = interaction.guild.get_channel(ID_CANALE_LOG_RECENSIONI)
    
    # Verifica che il canale esista e che sia effettivamente un Forum
    if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
        await interaction.followup.send(
            "❌ **Errore:** Canale Forum per le recensioni non trovato o non configurato correttamente.",
            ephemeral=True
        )
        return

    stelle_grafiche = "⭐" * valutazione.value

    # Creazione dell'Embed per la Recensione
    embed = discord.Embed(
        title="🌟 NUOVA RECENSIONE STAFF — PUGLIA RP 🌟",
        color=discord.Color.from_rgb(230, 126, 34),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(name="👮 Staffer Recensito", value=staffer.mention, inline=True)
    embed.add_field(name="👤 Recensito da", value=interaction.user.mention, inline=True)
    embed.add_field(name="⭐ Valutazione", value=f"**{valutazione.value}/10**\n{stelle_grafiche}", inline=False)
    embed.add_field(name="💬 Motivazione", value=f"```{motivo}```", inline=False)

    if staffer.display_avatar:
        embed.set_thumbnail(url=staffer.display_avatar.url)

    if LINK_IMMAGINE_RECENSIONE:
        embed.set_image(url=LINK_IMMAGINE_RECENSIONE)

    embed.set_footer(
        text="Puglia RP Autumn • Sistema Recensioni Ufficiale",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    # 📌 CREAZIONE DEL POST NEL FORUM
    titolo_post = f"⭐ [{valutazione.value}/10] Recensione Staff - {staffer.display_name}"
    
    try:
        await forum_channel.create_thread(
            name=titolo_post,
            embed=embed
        )
        await interaction.followup.send(
            f"✅ **Recensione inviata con successo!** È stato creato un nuovo post nel Forum per {staffer.mention}.",
            ephemeral=True
        )
    except Exception as e:
        print(f"Errore creazione post forum: {e}")
        await interaction.followup.send(
            f"❌ Si è verificato un errore durante la pubblicazione nel forum: `{e}`",
            ephemeral=True
        )

# ==========================================
# TASK AUTOMATICO: RESET & LEADERBOARD LUNEDÌ
# ==========================================
@tasks.loop(time=time(0, 0, tzinfo=timezone.utc))
async def monday_reset_task():
    # Verifica che sia Lunedì (weekday 0)
    if datetime.now(timezone.utc).weekday() == 0:
        print("[RESET SETTIMANALE] Avvio reset ore staff del Lunedì...")
        data = load_data()
        weekly = data.get("weekly_minutes", {})

        guild = None
        for g in bot.guilds:
            lb_chan = g.get_channel(LEADERBOARD_CHANNEL_ID)
            if lb_chan:
                guild = g
                break

        if guild:
            lb_chan = guild.get_channel(LEADERBOARD_CHANNEL_ID)
            if lb_chan and weekly:
                sorted_staff = sorted(weekly.items(), key=lambda x: x[1], reverse=True)

                embed = discord.Embed(
                    title="📊 CLASSIFICA FINALE SETTIMANALE STAFF",
                    description="La settimana è giunta al termine! Ecco i risultati e il totale delle ore svolte dal team:",
                    color=discord.Color.purple(),
                    timestamp=datetime.now(timezone.utc)
                )

                medals = ["🥇", "🥈", "🥉"]
                for idx, (u_id, minutes) in enumerate(sorted_staff, start=1):
                    badge = medals[idx-1] if idx <= 3 else f"#{idx}"
                    user_info = data["users"].get(u_id, {})
                    r_name = user_info.get("roblox_name", "N/D")
                    grado = user_info.get("grado", "Staff")
                    embed.add_field(
                        name=f"{badge} <@{u_id}> - Roblox: {r_name}",
                        value=f"⏱️ **{format_minutes(minutes)}** | ⭐ `{grado}`",
                        inline=False
                    )

                embed.set_footer(text="Puglia RP • Le ore sono state azzerate per la nuova settimana!")
                await lb_chan.send(content="🔔 **RESET SETTIMANALE EFFETTUATO!** Ecco la classifica finale:", embed=embed)

        # Azzera la leaderboard settimanale
        data["weekly_minutes"] = {}
        save_data(data)
        print("[RESET SETTIMANALE] Ore staff azzerate con successo!")

@monday_reset_task.before_loop
async def before_monday_reset():
    await bot.wait_until_ready()

# Avvia il loop del reset settimanale

    
import os

keep_alive() # <-- Aggiungi questa riga per la 24/7 di Flask

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERRORE: DISCORD_TOKEN non trovato!")
