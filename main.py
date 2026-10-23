# ==========================================
# RICHIESTA DOCUMENTO
# ==========================================

ID_CANALE_LOG_RICHIESTA_DOCUMENTO = 1563240758390030517
ID_RUOLO_APPROVA_DOCUMENTO = 1562507751975035065
TITOLO_RICHIESTA_DOCUMENTO_IN_ATTESA = "📄 Nuova richiesta documento"

_lock_richieste_documento = {}


async def cerca_avatar_roblox(nome_utente):
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
            risultati = (await response.json()).get("data", [])

        if not risultati:
            return None

        return risultati[0].get("imageUrl")


class ViewApprovazioneRichiestaDocumento(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        membro = interaction.user

        if not isinstance(membro, discord.Member):
            await interaction.response.send_message(
                "Questi pulsanti funzionano solo nel server.",
                ephemeral=True,
            )
            return False

        if not any(
            ruolo.id == ID_RUOLO_APPROVA_DOCUMENTO
            for ruolo in membro.roles
        ):
            await interaction.response.send_message(
                "Non hai il ruolo necessario per gestire le richieste.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Accetta",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="richiesta_documento:accetta",
    )
    async def accetta(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.gestisci_richiesta(interaction, accettata=True)

    @discord.ui.button(
        label="Rifiuta",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="richiesta_documento:rifiuta",
    )
    async def rifiuta(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.gestisci_richiesta(interaction, accettata=False)

    async def gestisci_richiesta(
        self,
        interaction: discord.Interaction,
        *,
        accettata: bool,
    ):
        messaggio = interaction.message

        if messaggio is None or messaggio.channel is None:
            await interaction.response.send_message(
                "Non riesco a trovare il messaggio della richiesta.",
                ephemeral=True,
            )
            return

        lock = _lock_richieste_documento.setdefault(
            messaggio.id,
            asyncio.Lock(),
        )

        async with lock:
            try:
                messaggio = await messaggio.channel.fetch_message(messaggio.id)
            except discord.HTTPException:
                await interaction.response.send_message(
                    "Non riesco a leggere il messaggio della richiesta.",
                    ephemeral=True,
                )
                return

            if not messaggio.embeds:
                await interaction.response.send_message(
                    "Il messaggio non contiene una richiesta valida.",
                    ephemeral=True,
                )
                return

            embed = discord.Embed.from_dict(messaggio.embeds[0].to_dict())

            if embed.title != TITOLO_RICHIESTA_DOCUMENTO_IN_ATTESA:
                await interaction.response.send_message(
                    "Questa richiesta è già stata gestita.",
                    ephemeral=True,
                )
                return

            footer = embed.footer.text or ""
            corrispondenza = re.search(r"discord_id=(\d+)", footer)

            if not corrispondenza:
                await interaction.response.send_message(
                    "Non riesco a individuare chi ha inviato la richiesta.",
                    ephemeral=True,
                )
                return

            richiedente_id = int(corrispondenza.group(1))

            if accettata:
                esito = "accettata"
                messaggio_dm = (
                    "✅ La tua richiesta documento è stata accettata "
                    "con successo."
                )
                embed.title = "✅ Richiesta documento accettata"
                embed.color = discord.Color.green()
            else:
                esito = "rifiutata"
                messaggio_dm = "❌ La tua richiesta documento è stata rifiutata."
                embed.title = "❌ Richiesta documento rifiutata"
                embed.color = discord.Color.red()

            embed.add_field(
                name="Esito",
                value=f"Richiesta {esito} da {interaction.user.mention}.",
                inline=False,
            )
            embed.set_footer(
                text=f"Richiesta gestita • discord_id={richiedente_id}"
            )

            vista_disabilitata = ViewApprovazioneRichiestaDocumento()
            for elemento in vista_disabilitata.children:
                elemento.disabled = True

            await interaction.response.edit_message(
                embed=embed,
                view=vista_disabilitata,
            )

        dm_inviato = False

        try:
            utente = bot.get_user(richiedente_id)
            if utente is None:
                utente = await bot.fetch_user(richiedente_id)

            await utente.send(messaggio_dm)
            dm_inviato = True
        except discord.HTTPException:
            pass

        if dm_inviato:
            await interaction.followup.send(
                f"Richiesta {esito}; ho inviato un DM al richiedente.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f"Richiesta {esito}, ma non sono riuscito a inviare il DM. "
                "Il richiedente potrebbe avere i messaggi privati disattivati.",
                ephemeral=True,
            )


@bot.tree.command(
    name="richiesta-documento",
    description="Invia una richiesta di documento allo staff.",
)
@app_commands.guild_only()
@app_commands.describe(
    nome="Nome: almeno 4 caratteri",
    cognome="Cognome: almeno 4 caratteri",
    data_di_nascita="Data nel formato GG/MM/AAAA",
    sesso="Sesso: almeno 4 caratteri",
    cittadinanza="Cittadinanza: almeno 4 caratteri",
    nome_roblox="Nome Roblox: almeno 4 caratteri",
)
@app_commands.rename(data_di_nascita="data-di-nascita")
async def richiesta_documento(
    interaction: discord.Interaction,
    nome: str,
    cognome: str,
    data_di_nascita: str,
    sesso: str,
    cittadinanza: str,
    nome_roblox: str,
):
    campi = {
        "Nome": nome.strip(),
        "Cognome": cognome.strip(),
        "Data di nascita": data_di_nascita.strip(),
        "Sesso": sesso.strip(),
        "Cittadinanza": cittadinanza.strip(),
        "Nome Roblox": nome_roblox.strip(),
    }

    for etichetta, valore in campi.items():
        if len(valore) < 4:
            await interaction.response.send_message(
                f"Il campo **{etichetta}** deve contenere più di 3 caratteri.",
                ephemeral=True,
            )
            return

        if len(valore) > 100:
            await interaction.response.send_message(
                f"Il campo **{etichetta}** non può superare 100 caratteri.",
                ephemeral=True,
            )
            return

    try:
        datetime.datetime.strptime(
            campi["Data di nascita"],
            "%d/%m/%Y",
        )
    except ValueError:
        await interaction.response.send_message(
            "Inserisci la data nel formato **GG/MM/AAAA**.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    try:
        avatar_url = await cerca_avatar_roblox(campi["Nome Roblox"])
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, KeyError):
        await interaction.followup.send(
            "Il servizio Roblox non è disponibile. Riprova più tardi.",
            ephemeral=True,
        )
        return

    if not avatar_url:
        await interaction.followup.send(
            "Non ho trovato quel nome utente Roblox. Controlla che sia corretto.",
            ephemeral=True,
        )
        return

    canale = interaction.guild.get_channel(
        ID_CANALE_LOG_RICHIESTA_DOCUMENTO
    )

    if canale is None:
        try:
            canale = await bot.fetch_channel(
                ID_CANALE_LOG_RICHIESTA_DOCUMENTO
            )
        except discord.HTTPException:
            canale = None

    if not isinstance(canale, discord.TextChannel):
        await interaction.followup.send(
            "Il canale di log non è disponibile o non è testuale.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title=TITOLO_RICHIESTA_DOCUMENTO_IN_ATTESA,
        description="Una nuova richiesta è in attesa di revisione.",
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name="Richiesta documento")
    embed.set_thumbnail(url=avatar_url)

    for etichetta, valore in campi.items():
        embed.add_field(name=etichetta, value=valore, inline=True)

    embed.set_footer(
        text=f"Richiedente • discord_id={interaction.user.id}"
    )

    try:
        await canale.send(
            embed=embed,
            view=ViewApprovazioneRichiestaDocumento(),
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except (discord.Forbidden, discord.HTTPException):
        await interaction.followup.send(
            "Non sono riuscito a pubblicare la richiesta nel canale di log.",
            ephemeral=True,
        )
        return

    await interaction.followup.send(
        "✅ Richiesta inviata con successo. Riceverai un DM dopo la revisione.",
        ephemeral=True,
    )
