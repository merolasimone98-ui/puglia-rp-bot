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

bot = commands.Bot(command_prefix="/", intents=intents)

# 📌 ID RUOLI E CANALI
ROLE_STAFF_BASE_ID = 1562507751975035065
ID_RUOLO_CITTADINO = 1562894350135066674
ID_RUOLO_PORTO_DARMI = 1562894902428442695

RUOLI_PATENTI = {
    'A': 1562894624597479555,
    'B': 1562894703081431090,
    'C': 1562894760878800897,
    'D': 1562894822983860364
}

# Canali per Recensioni, Registro ed Economia
ID_CANALE_COMANDO_RECENSIONI = 123456789012345678  # Sostituisci con l'ID del canale per /recensisci-staff
ID_CANALE_LOG_RECENSIONI = 1563176554786463894      # Canale Forum
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
        return {"users": {}, "economy": {}, "duty": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Errore lettura {DATA_FILE}: {e}")
        return {"users": {}, "economy": {}, "duty": {}}

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

nomi_rp_registrati = {}

# ==========================================
# 💳 INTERFACCIA CONTO BANCARIO
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

# ==========================================
# 🆔 IDENTIFICAZIONE STAFF & REVOCA
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
# ⭐ RECENSIONI STAFF
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
# 🚨 ARRESTI & MULTE
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
# 💰 ECONOMIA & BANCA
# ==========================================
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
# 🚀 EVENTO ON_READY & AVVIO BOT
# ==========================================
@bot.event
async def on_ready():
    print(f'🤖 Bot connesso come {bot.user}')
    
    bot.add_view(VistaContoBancario())

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
