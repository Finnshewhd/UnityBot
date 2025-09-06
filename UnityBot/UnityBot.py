import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from discord import app_commands
import json

# ================== LOAD CONFIG ==================
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config["token"]
GUILD_ID = config["guild_id"]
SUPPORT_ROLE_ID = config["support_role_id"]
LOG_CHANNEL_ID = config["log_channel_id"]
TICKET_CATEGORY_ID = config["ticket_category_id"]
TICKET_PRIVATE_ROLE_IDS = config["ticket_private_role_ids"]
TICKET_PANEL_CHANNEL_ID = config["ticket_panel_channel_id"]
VOICE_CHANNEL_ID = config["voice_channel_id"]                
VOICE_NOTIFY_CHANNEL_ID = config["voice_notify_channel_id"]
VOICE_NOTIFY_ROLE_ID = config["voice_notify_role_id"]
APPLICATION_CHANNEL_ID = config.get("application_category_id")  

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)  # change the prefix to whatever you want

# ---------------------------------------------------
# Helper: Log-Embed
# ---------------------------------------------------
async def send_log(guild: discord.Guild, embed: discord.Embed):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(embed=embed) # type: ignore

# ================== TICKET-SYSTEM ==================
class TicketModal(Modal, title="🎫 Create Ticket"):
    roblox_name = TextInput(label="Your name", placeholder="Please Give Us Ur Name", required=True)
    reason = TextInput(label="Reason for the Ticket", placeholder="Tell us your Reason", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        assert guild is not None

        category = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),  # type: ignore
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for role_id in TICKET_PRIVATE_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,  # type: ignore
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 New Ticket",
            description=f"**Name:** {self.roblox_name}\n**Reason:** {self.reason}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Created by {interaction.user}")
        await ticket_channel.send(embed=embed)

        await interaction.response.send_message(f"✅ your ticket got created: {ticket_channel.mention}", ephemeral=True)

        # Logging
        log = discord.Embed(
            title="📋 Ticket Created",
            description=f"{interaction.user.mention} created a new ticket.",
            color=discord.Color.orange()
        )
        log.add_field(name="Name", value=str(self.roblox_name), inline=False)
        log.add_field(name="Reason", value=str(self.reason), inline=False)
        await send_log(guild, log)

# ================== Application-SYSTEM ==================
class ApplicationModal(Modal, title="📋Team-Application"):
    char_name = TextInput(label="Discord-Name", placeholder="Max#1234", required=True, max_length=64)
    age = TextInput(label="Age", placeholder="17", required=True, max_length=4)
    experience = TextInput(label="experience", style=discord.TextStyle.paragraph, placeholder="(:", required=True, max_length=600)
    motivation = TextInput(label="Motivation", style=discord.TextStyle.paragraph, placeholder="why do you wanna join team?", required=True, max_length=600)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        assert guild is not None

        target_channel = guild.get_channel(APPLICATION_CHANNEL_ID) if APPLICATION_CHANNEL_ID else None

        embed = discord.Embed(
            title="📋 New Team-Application",
            color=discord.Color.blurple()
        )
        embed.add_field(name="👤 User", value=interaction.user.mention, inline=True)
        embed.add_field(name="🪪 Name", value=str(self.char_name), inline=True)
        embed.add_field(name="🔞 Age", value=str(self.age), inline=True)
        embed.add_field(name="🧰 experience", value=str(self.experience), inline=False)
        embed.add_field(name="🔥 Motivation", value=str(self.motivation), inline=False)
        embed.set_footer(text=f"User-ID: {interaction.user.id}")

        if target_channel and isinstance(target_channel, discord.TextChannel):
            await target_channel.send(embed=embed)
            await interaction.response.send_message("✅ your Application got send.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ The channel for Applications is not set, please contact a admin.", ephemeral=True)

        # Log
        log = discord.Embed(
            title="🗂️ application created",
            description=f"{interaction.user.mention} created a team-appication.",
            color=discord.Color.orange()
        )
        await send_log(guild, log)

# ================== PANEL + Application) ==================
class PanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🎫 Create Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket"))
        self.add_item(Button(label="📋 Create Team-Application", style=discord.ButtonStyle.success, custom_id="create_application"))

@bot.tree.command(name="send_ticket", description="Sends the Ticket in the Set channel")
@app_commands.checks.has_permissions(administrator=True)
async def send_ticket(interaction: discord.Interaction):
    if interaction.channel_id != TICKET_PANEL_CHANNEL_ID:
        return await interaction.response.send_message("❌ Please Send this command in the channel you set in the config.", ephemeral=True)

    embed = discord.Embed(
        title="🎫 Ticket & 📋 Application",
        description=(
            "• **Ticket**: Klick the button Create ticket to create a ticket (:\n"
            "• **Application**: Klick the button Create Team-Application to create a Team-Application (:\n\n"
        ),
        color=discord.Color.blurple()
    )
    await interaction.channel.send(embed=embed, view=PanelView())  # type: ignore
    await interaction.response.send_message("✅ Panel send!", ephemeral=True)

# ================== INTERACTION HANDLER (Buttons) ==================
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data:  # type: ignore
        cid = interaction.data.get("custom_id")  # type: ignore
        if cid == "create_ticket":
            return await interaction.response.send_modal(TicketModal())
        if cid == "create_application":
            return await interaction.response.send_modal(ApplicationModal())

# ================== VOICE JOIN NOTIFY ==================
class MoveButtonView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member

    @discord.ui.button(label="➡️ Move in your channel", style=discord.ButtonStyle.green)
    async def move_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        supporter_channel = interaction.user.voice.channel if interaction.user.voice else None  # type: ignore
        if not supporter_channel:
            return await interaction.response.send_message(
                "❌ You Have to be in a voice Channel, To move someone!", ephemeral=True
            )

        try:
            await self.member.move_to(supporter_channel)
            await interaction.response.send_message(
                f"✅ {self.member.mention} got moved to {supporter_channel.name}", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ You dont have the rights to Move.", ephemeral=True)

@bot.event
async def on_voice_state_update(member, before, after):
    # Warteraum-Join
    if after.channel and after.channel.id == VOICE_CHANNEL_ID and (not before.channel or before.channel.id != VOICE_CHANNEL_ID):
        notify_channel = bot.get_channel(VOICE_NOTIFY_CHANNEL_ID)
        voice_role = member.guild.get_role(VOICE_NOTIFY_ROLE_ID)
        support_role = member.guild.get_role(SUPPORT_ROLE_ID)
        if notify_channel and isinstance(notify_channel, discord.TextChannel):
            await notify_channel.send(
                f"🔊 {member.mention} Is waiting in the waitingroom {voice_role.mention if voice_role else ''} {support_role.mention if support_role else ''}",
                view=MoveButtonView(member)
            )

# ================== SLASH: /announce ==================
@bot.tree.command(name="announce", description="Send a Annoucment in Embed")
@app_commands.describe(message="Massage")
@app_commands.checks.has_permissions(manage_guild=True)
async def announce(interaction: discord.Interaction, message: str):
    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Send by {interaction.user}")
    await interaction.response.send_message(embed=embed)

    # Log
    log = discord.Embed(
        title="📋 Announcement Sent",
        description=f"{interaction.user.mention} Has send an announcement.",
        color=discord.Color.orange()
    )
    log.add_field(name="Massage", value=message, inline=False)
    await send_log(interaction.guild, log)  # type: ignore

# ================== SLASH: /rules ==================
@bot.tree.command(name="rules", description="Sends the rules")
async def rules(interaction: discord.Interaction):
    rules_text = """
**Rules**
1. **Idk**: Put smth here.
2. **Idk**: Put smth here.
3. **Idk**: Put smth here.
4. **Idk**: Put smth here.
5. **Idk**: Put smth here.
6. **Idk**: Put smth here.
7. **Idk**: Put smth here.
    """
    embed = discord.Embed(
        title="📜 Rules",
        description=rules_text,
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

    log = discord.Embed(
        title="📋 Rules send",
        description=f"{interaction.user.mention} has send the rules.",
        color=discord.Color.orange()
    )
    await send_log(interaction.guild, log)  # type: ignore

# ================== /uprank ==================
@bot.tree.command(name="uprank", description="Gives a Uprank 😸")
@app_commands.describe(
    member="Who?",
    from_role="From Role",
    to_role="To Role",
    reason="Reason"
)
@app_commands.checks.has_permissions(manage_roles=True)
async def uprank(
    interaction: discord.Interaction,
    member: discord.Member,
    from_role: discord.Role | None,
    to_role: discord.Role,
    reason: str
):
    # Role Change
    try:
        if from_role and from_role in member.roles:
            await member.remove_roles(from_role, reason=f"Uprank: {reason}")
        if to_role not in member.roles:
            await member.add_roles(to_role, reason=f"Uprank: {reason}")
    except discord.Forbidden:
        return await interaction.response.send_message("❌ I Dont have the perms to do that.", ephemeral=True)

    # send embed
    embed = discord.Embed(
        title="🏅 • Uprank • 🏅",
        color=discord.Color.from_str("#f39c12")
    )
    embed.add_field(name="👤 WHO:", value=member.mention, inline=False)
    embed.add_field(name="📈 TO:", value=f"» {to_role.mention}", inline=True)
    embed.add_field(name="📉 FROM:", value=f"» {from_role.mention if from_role else '—'}", inline=True)
    embed.add_field(name="📝 REASON:", value=reason, inline=False)
    embed.set_footer(text="✨ Thank you for your work!😽")
    await interaction.response.send_message(embed=embed)

    # Log
    log = discord.Embed(
        title="🟧 Uprank",
        description=f"{interaction.user.mention} Gave {member.mention} A Uprank.",
        color=discord.Color.orange()
    )
    log.add_field(name="From", value=(from_role.mention if from_role else "—"), inline=True)
    log.add_field(name="To", value=to_role.mention, inline=True)
    log.add_field(name="Reason", value=reason, inline=False)
    await send_log(interaction.guild, log)  # type: ignore

# ================== /teamkick ==================
@bot.tree.command(name="teamkick", description="Kicks a Member")
@app_commands.describe(member="WHO", reason="REASON")
@app_commands.checks.has_permissions(kick_members=True)
async def teamkick(interaction: discord.Interaction, member: discord.Member, reason: str):
    if member == interaction.user:
        return await interaction.response.send_message("❌ Why Would you Kick yourself?.", ephemeral=True)

    try:
        await member.kick(reason=f"{interaction.user} | {reason}")
    except discord.Forbidden:
        return await interaction.response.send_message("❌ I dont have the Perms.", ephemeral=True)

    embed = discord.Embed(
        title="👢 Team-Kick",
        description=f"{member.mention} Got Kicked.",
        color=discord.Color.red()
    )
    embed.add_field(name="📝 Reason", value=reason, inline=False)
    embed.set_footer(text=f"From {interaction.user}")
    await interaction.response.send_message(embed=embed)

    # Log
    log = discord.Embed(
        title="🟥 Teamkick",
        description=f"{interaction.user.mention} Kicked {member.mention}.",
        color=discord.Color.dark_red()
    )
    log.add_field(name="Reason", value=reason, inline=False)
    await send_log(interaction.guild, log)  # type: ignore

# ================== BOT START / READY ==================
@bot.event
async def on_ready():
    print(f"✅ Bot Logged in as {bot.user}")
    
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    except Exception as e:
        print(f"Error with commands {e}")

    # Logging
    for guild in bot.guilds:
        embed = discord.Embed(
            title="✅ Bot Started",
            description=f"the bot {bot.user.mention} is online.",  # type: ignore
            color=discord.Color.green()
        )
        await send_log(guild, embed)

bot.run(TOKEN)
