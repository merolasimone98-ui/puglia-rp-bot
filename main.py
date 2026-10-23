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
# 🚨 SISTEMA REVOCA DOCUMENTI (ADMIN ONLY)
# ==========================================
class SelectRevocaDocumento(discord.ui.Select):
    def __init__(self, utente_target):
        self.utente_target = utente_target
        options = [
            discord.SelectOption(label="Cittadinanza", description="Revoca la cittadinanza ed elimina il Nome RP", emoji="📜"),
            discord.SelectOption(label="Patente A", description="Revoca la Patente A", emoji="🛵"),
            discord.SelectOption(label="Patente B", description="Revoca la Patente B", emoji="🚗"),
            discord.SelectOption(label="Patente C", description="Revoca la Patente C", emoji="🚚"),
            discord.SelectOption(label="Patente D", description="Revoca la Patente D", emoji="🚌"),
            discord.SelectOption(label="Porto d'Armi", description="Revoca la licenza del Porto d'Armi", emoji="🔫"),
        ]
        super().__init__(placeholder="Seleziona il documento da revocare...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        scelta = self.values[0]
        ruolo_da_rimuovere = None

        if scelta == "Cittadinanza":
            ruolo_da_rimuovere = interaction.guild.get_role(ID_RUOLO_CITTADINO)
            if self.utente_target.id in nomi_rp_registrati:
                del nomi_rp_registrati[self.utente_target.id]
        elif scelta.startswith("Patente"):
            lettera = scelta.split()[1]
            id_r = RUOLI_PATENTI.get(lettera)
            ruolo_da_rimuovere = interaction.guild.get_role(id_r)
        elif scelta == "Porto d'Armi":
            ruolo_da_rimuovere = interaction.guild.get_role(ID_RUOLO_PORTO_DARMI)

        if ruolo_da_rimuovere and ruolo_da_rimuovere in self.utente_target.roles:
            try:
                await self.utente_target.remove_roles(ruolo_da_rimuovere)
            except Exception:
                pass

        # Risposta privata per l'admin che ha eseguito la revoca
        await interaction.response.send_message(
            f"🚫 **REVOCA COMPLETATA!**\nÈ stata revocata la **{scelta}** all'utente {self.utente_target.mention}. Ora dovrà richiedere nuovamente il documento.",
            ephemeral=True
        )

        try:
            await self.utente_target.send(
                f"⚠️ **ATTENZIONE!** La tua **{scelta}** su **Puglia RP** è stata **REVOCATA** dagli Amministratori.\nDovrai compilare nuovamente il modulo per ottenerla."
            )
        except Exception:
            pass


class ViewRevocaDocumento(discord.ui.View):
    def __init__(self, utente_target):
        super().__init__(timeout=60)
        self.add_item(SelectRevocaDocumento(utente_target))


# 🛠️ COMANDO SLASH NATIVO: /revoca (Rendiamo il pannello EFFIMERO/PRIVATO)
@bot.tree.command(name="revoca", description="Revoca un documento ad un utente (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def revoca_slash(interaction: discord.Interaction, utente: discord.Member):
    embed = discord.Embed(
        title="🚨 REVOCA DOCUMENTI - PUGLIA RP",
        description=f"Seleziona dal menu sottostante quale documento vuoi revocare a {utente.mention}:",
        color=discord.Color.dark_red()
    )
    # ephemeral=True lo rende visibile SOLO a chi ha lanciato il comando
    await interaction.response.send_message(embed=embed, view=ViewRevocaDocumento(utente), ephemeral=True)


# 🛠️ COMANDO CLASSICO PREFISSO /: /revoca @utente
@bot.command(name="revoca")
@commands.has_permissions(administrator=True)
async def revoca_prefisso(ctx, utente: discord.Member = None):
    if not utente:
        await ctx.send("❌ **Uso corretto del comando:** `/revoca @Utente`", delete_after=10)
        return

    # Cancella il messaggio del comando per pulizia del canale
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        title="🚨 REVOCA DOCUMENTI - PUGLIA RP",
        description=f"Seleziona dal menu sottostante quale documento vuoi revocare a {utente.mention}:",
        color=discord.Color.dark_red()
    )
    await ctx.send(embed=embed, view=ViewRevocaDocumento(utente))


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
class IdentificationModal(ui.Modal, title="Identificazione Staff Puglia RP"):
    nome_discord = ui.TextInput(label="Nome Discord", placeholder="Es. simone_rp", required=True)
    nome_roblox = ui.TextInput(label="Nome Roblox", placeholder="Es. Player123", required=True)
    nome_rp = ui.TextInput(label="Nome e Cognome RP", placeholder="Es. Marco Rossi", required=True)
    grado_staff = ui.TextInput(label="Grado Staff", placeholder="Es. Mod / Admin / Helper", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id_str = str(interaction.user.id)
        data = load_data()

        data["users"][user_id_str] = {
            "discord_name": self.nome_discord.value,
            "roblox_name": self.nome_roblox.value,
            "rp_name": self.nome_rp.value,
            "grado": self.grado_staff.value,
            "registered_at": datetime.utcnow().isoformat()
        }
        save_data(data)

        guild = bot.get_guild(interaction.guild_id) if interaction.guild else None
        member = None
        if guild:
            member = guild.get_member(interaction.user.id)
            if member:
                role_identificato = guild.get_role(ROLE_STAFF_IDENTIFICATO_ID)
                if role_identificato:
                    try:
                        await member.add_roles(role_identificato)
                    except Exception as e:
                        print(f"Errore nell'assegnare il ruolo identificato: {e}")

        await interaction.response.send_message(
            "✅ **Identificazione completata con successo!**\n"
            "Ora possiedi il ruolo **Staff Identificato** e puoi utilizzare il comando `/servizio` nel canale dedicato.",
            ephemeral=True
        )

        if guild:
            log_channel = guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed_log = discord.Embed(
                    title="📝 NUOVA IDENTIFICAZIONE STAFF",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed_log.add_field(name="👤 Utente", value=interaction.user.mention, inline=True)
                embed_log.add_field(name="🎮 Roblox", value=self.nome_roblox.value, inline=True)
                embed_log.add_field(name="🪪 Nome RP", value=self.nome_rp.value, inline=True)
                embed_log.add_field(name="⭐ Grado", value=self.grado_staff.value, inline=True)
                embed_log.set_footer(text="Puglia RP • Sistema Identificazione")
                await log_channel.send(embed=embed_log)

class DMIdentificationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🆔 Effettua Identificazione", style=discord.ButtonStyle.primary, custom_id="btn_identifica_dm")
    async def identifica_button(self, interaction: discord.Interaction, button: ui.Button):
        data = load_data()
        user_id_str = str(interaction.user.id)
        if user_id_str in data["users"]:
            await interaction.response.send_message("❌ Risulti già identificato nel sistema di Puglia RP!", ephemeral=True)
            return
        await interaction.response.send_modal(IdentificationModal())

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
