import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import json, os, asyncio
from datetime import timedelta

TOKEN = os.environ.get("TOKEN", "")
GUILD_ID = 1496970391200207049
BAD_WORDS = ["fuck","shit","bitch","ass","damn","idiot","stupid"]
XP_FILE = "xp.json"
WARN_FILE = "warns.json"
LEVEL_ROLES = {5:"🔰 Recruit",10:"🗡️ TNC Member",20:"🛡️ UKA Member",30:"⚔️ KRD Member",50:"👑 Supreme Commander"}
STAFF_ROLES = ["👑 Supreme Commander","⚔️ KRD Commander","🛡️ UKA Commander","🗡️ TNC Commander","⚔️ KRD Officer","🛡️ UKA Officer","🗡️ TNC Officer"]
ALLIANCE_ROLES = {"KRD":"⚔️ KRD Member","UKA":"🛡️ UKA Member","TNC":"🗡️ TNC Member"}

def load(f): return json.load(open(f)) if os.path.exists(f) else {}
def save(f,d): json.dump(d,open(f,"w"))
def lvl(xp): return int((xp/100)**0.5)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

class VerifyActionView(View):
    def __init__(self, member, verify_ch, alliance):
        super().__init__(timeout=None)
        self.member = member
        self.verify_ch = verify_ch
        self.alliance = alliance

    @discord.ui.button(label="✅ Verify", style=discord.ButtonStyle.green, custom_id="verify_accept")
    async def accept(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ No permission!", ephemeral=True)
            return
        guild = interaction.guild
        verified_role = discord.utils.get(guild.roles, name="✅ Verified")
        if not verified_role:
            verified_role = await guild.create_role(name="✅ Verified", color=discord.Color.green())
        await self.member.add_roles(verified_role)
        if self.alliance and self.alliance in ALLIANCE_ROLES:
            alliance_role = discord.utils.get(guild.roles, name=ALLIANCE_ROLES[self.alliance])
            if alliance_role:
                await self.member.add_roles(alliance_role)
        welcome_ch = discord.utils.get(guild.text_channels, name="welcome")
        if welcome_ch:
            embed = discord.Embed(title="⚔️ New Verified Member!", description=f"Welcome {self.member.mention} to A3O8E5!\nAlliance: **{self.alliance}**\nGlory to the Alliance! 🏰", color=0xFFD700)
            embed.set_thumbnail(url=self.member.display_avatar.url)
            await welcome_ch.send(embed=embed)
        try:
            await self.member.send(f"✅ You have been verified! Welcome to A3O8E5! You joined **{self.alliance}**! ⚔️")
        except:
            pass
        await interaction.response.send_message(f"✅ {self.member.mention} verified as **{self.alliance}** member!", ephemeral=True)
        await asyncio.sleep(3)
        await self.verify_ch.delete()

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red, custom_id="verify_reject")
    async def reject(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ No permission!", ephemeral=True)
            return
        try:
            await self.member.send("❌ Your verification was rejected. You have been removed from A3O8E5.")
        except:
            pass
        await interaction.response.send_message(f"❌ {self.member.mention} rejected.", ephemeral=True)
        await asyncio.sleep(3)
        await self.verify_ch.delete()
        await self.member.kick(reason="Verification rejected")

class AgeSelect(Select):
    def __init__(self, member_data):
        self.member_data = member_data
        options = [
            discord.SelectOption(label="🌑 Dark Age (Under 18)", value="Dark Age"),
            discord.SelectOption(label="⚔️ Feudal Age (18-25)", value="Feudal Age"),
            discord.SelectOption(label="🏰 Castle Age (25-35)", value="Castle Age"),
            discord.SelectOption(label="👑 Imperial Age (35+)", value="Imperial Age"),
        ]
        super().__init__(placeholder="Select your Era (Age)...", options=options, custom_id="OB:AGE")

    async def callback(self, interaction: discord.Interaction):
        self.member_data["age"] = self.values[0]
        await interaction.response.defer()

class ContinentSelect(Select):
    def __init__(self, member_data):
        self.member_data = member_data
        options = [
            discord.SelectOption(label="🌏 Asia", value="Asia"),
            discord.SelectOption(label="🌍 Africa", value="Africa"),
            discord.SelectOption(label="🌎 Americas", value="Americas"),
            discord.SelectOption(label="🌐 Europe", value="Europe"),
        ]
        super().__init__(placeholder="Where are you from?", options=options, custom_id="OB:CONTINENT")

    async def callback(self, interaction: discord.Interaction):
        self.member_data["continent"] = self.values[0]
        await interaction.response.defer()

class SpendingSelect(Select):
    def __init__(self, member_data):
        self.member_data = member_data
        options = [
            discord.SelectOption(label="🐋 Whale", value="Whale", description="Heavy Spender"),
            discord.SelectOption(label="🐬 Dolphin", value="Dolphin", description="Mid Spender"),
            discord.SelectOption(label="🆓 F2P", value="F2P", description="Free to Play"),
        ]
        super().__init__(placeholder="What is your spending level?", options=options, custom_id="OB:SPENDING")

    async def callback(self, interaction: discord.Interaction):
        self.member_data["spending"] = self.values[0]
        await interaction.response.defer()

class AllianceSelect(Select):
    def __init__(self, member_data):
        self.member_data = member_data
        options = [
            discord.SelectOption(label="⚔️ KRD — KnightsRenegade", value="KRD"),
            discord.SelectOption(label="🛡️ UKA — Unified Kingdom", value="UKA"),
            discord.SelectOption(label="🗡️ TNC — Tenacity", value="TNC"),
        ]
        super().__init__(placeholder="Select your Alliance...", options=options, custom_id="OB:ALLIANCE")

    async def callback(self, interaction: discord.Interaction):
        self.member_data["alliance"] = self.values[0]
        await interaction.response.defer()

class OnboardingView(View):
    def __init__(self, member, guild, verify_ch):
        super().__init__(timeout=300)
        self.member_data = {}
        self.member = member
        self.guild = guild
        self.verify_ch = verify_ch
        self.add_item(AgeSelect(self.member_data))
        self.add_item(ContinentSelect(self.member_data))
        self.add_item(SpendingSelect(self.member_data))
        self.add_item(AllianceSelect(self.member_data))

    @discord.ui.button(label="👨 Male", style=discord.ButtonStyle.primary, custom_id="OB:MALE")
    async def male(self, interaction: discord.Interaction, button: Button):
        self.member_data["gender"] = "Male"
        await self.submit(interaction)

    @discord.ui.button(label="👩 Female", style=discord.ButtonStyle.danger, custom_id="OB:FEMALE")
    async def female(self, interaction: discord.Interaction, button: Button):
        self.member_data["gender"] = "Female"
        await self.submit(interaction)

    async def submit(self, interaction: discord.Interaction):
        missing = [k for k in ["age","continent","spending","alliance"] if k not in self.member_data]
        if missing:
            await interaction.response.send_message(f"⚠️ Please complete all selections first!", ephemeral=True)
            return
        data = self.member_data
        embed = discord.Embed(title="📋 Profile Submitted!", description="Now send your **verification video** showing:\n\n1️⃣ Your **in-game name**\n2️⃣ Your **alliance name** (KRD / UKA / TNC)\n\n⏰ You have **24 hours** to submit.", color=0xFFD700)
        embed.add_field(name="⚔️ Era", value=data.get("age","?"))
        embed.add_field(name="🌍 Continent", value=data.get("continent","?"))
        embed.add_field(name="💰 Spending", value=data.get("spending","?"))
        embed.add_field(name="👤 Gender", value=data.get("gender","?"))
        embed.add_field(name="🏰 Alliance", value=data.get("alliance","?"))
        await interaction.response.send_message(embed=embed)
        staff_mentions = " ".join([r.mention for r in self.guild.roles if r.name in STAFF_ROLES])
        embed2 = discord.Embed(title="🎥 Verification Request", description=f"**Member:** {self.member.mention}\n**Era:** {data.get('age','?')}\n**Continent:** {data.get('continent','?')}\n**Spending:** {data.get('spending','?')}\n**Gender:** {data.get('gender','?')}\n**Alliance:** {data.get('alliance','?')}\n\nWaiting for verification video... 🎥", color=0xFF8C00)
        embed2.set_thumbnail(url=self.member.display_avatar.url)
        await self.verify_ch.send(content=staff_mentions, embed=embed2, view=VerifyActionView(self.member, self.verify_ch, data.get("alliance")))

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Open Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = interaction.user
        cat = discord.utils.get(guild.categories, name="🎫 Tickets")
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing:
            await interaction.response.send_message(f"❌ Already have ticket: {existing.mention}", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        for r in guild.roles:
            if any(s in r.name for s in ["Commander","Officer"]):
                overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        ch = await guild.create_text_channel(f"ticket-{member.name.lower()}", category=cat, overwrites=overwrites)
        staff_mentions = " ".join([r.mention for r in guild.roles if r.name in STAFF_ROLES])
        embed = discord.Embed(title="🎫 New Ticket", description=f"**User:** {member.mention}\n\nDescribe your issue.", color=0xFFD700)
        await ch.send(content=f"{member.mention} {staff_mentions}", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket: {ch.mention}", ephemeral=True)

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔒 Closing in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

@bot.event
async def on_ready():
    print(f"✅ A3O8E5 BOT Online! — {bot.guilds[0].name}")
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())

@bot.event
async def on_member_join(member):
    guild = member.guild
    verify_cat = discord.utils.get(guild.categories, name="🔐 Verification")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }
    for r in guild.roles:
        if any(s in r.name for s in ["Commander","Officer"]):
            overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
    verify_ch = await guild.create_text_channel(f"verify-{member.name.lower()}", category=verify_cat, overwrites=overwrites)
    embed = discord.Embed(
        title=f"⚔️ Welcome to A3O8E5, {member.display_name}!",
        description="**Complete your profile below, then send a verification video showing:**\n\n1️⃣ Your **in-game name**\n2️⃣ Your **alliance name** (KRD / UKA / TNC)\n\n⏰ You have **24 hours** to verify or you will be kicked! 🚫",
        color=0xFFD700
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await verify_ch.send(content=member.mention, embed=embed, view=OnboardingView(member, guild, verify_ch))
    await asyncio.sleep(86400)
    verified_role = discord.utils.get(guild.roles, name="✅ Verified")
    if verified_role not in member.roles:
        try:
            await member.send("⏰ Verification time expired. You have been kicked from A3O8E5.")
        except:
            pass
        try:
            await verify_ch.delete()
        except:
            pass
        await member.kick(reason="Verification timeout")

@bot.event
async def on_message(message):
    if message.author.bot: 
        return

    import re  # ← أضف هذا السطر

    for word in BAD_WORDS:
        if re.search(rf"\b{word}\b", message.content.lower()):
            await message.delete()
            warns = load(WARN_FILE)
            uid = str(message.author.id)
            warns[uid] = warns.get(uid,0)+1
            save(WARN_FILE,warns)
            w = warns[uid]
            await message.channel.send(f"⚠️ {message.author.mention} Warning! ({w}/3)", delete_after=5)
            if w>=3:
                await message.author.timeout(timedelta(minutes=30))
                await message.channel.send(f"🔇 {message.author.mention} muted 30 min!", delete_after=10)
                warns[uid]=0
                save(WARN_FILE,warns)
            return

    xp = load(XP_FILE)
    uid = str(message.author.id)
    xp[uid] = xp.get(uid,0)+10
    old = lvl(xp[uid]-10)
    new = lvl(xp[uid])
    save(XP_FILE,xp)
    if new > old:
        await message.channel.send(f"🎉 {message.author.mention} reached **Level {new}**!", delete_after=10)
        if new in LEVEL_ROLES:
            role = discord.utils.get(message.guild.roles, name=LEVEL_ROLES[new])
            if not role: role = await message.guild.create_role(name=LEVEL_ROLES[new])
            await message.author.add_roles(role)
    await bot.process_commands(message)

@bot.command()
async def rank(ctx):
    xp = load(XP_FILE)
    uid = str(ctx.author.id)
    x = xp.get(uid,0)
    embed = discord.Embed(title=f"⚔️ {ctx.author.display_name}", color=0xFFD700)
    embed.add_field(name="Level", value=f"**{lvl(x)}**")
    embed.add_field(name="XP", value=f"**{x}**")
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def top(ctx):
    xp = load(XP_FILE)
    top10 = sorted(xp.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="🏆 A3O8E5 Leaderboard", color=0xFFD700)
    for i,(uid,x) in enumerate(top10,1):
        try:
            u = await bot.fetch_user(int(uid))
            embed.add_field(name=f"{i}. {u.display_name}", value=f"Lv {lvl(x)} | {x} XP", inline=False)
        except: pass
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def verify(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="✅ Verified")
    if not role: role = await ctx.guild.create_role(name="✅ Verified", color=discord.Color.green())
    await member.add_roles(role)
    verify_ch = discord.utils.get(ctx.guild.text_channels, name=f"verify-{member.name.lower()}")
    if verify_ch: await verify_ch.delete()
    welcome_ch = discord.utils.get(ctx.guild.text_channels, name="welcome")
    if welcome_ch:
        embed = discord.Embed(title="⚔️ New Verified Member!", description=f"Welcome {member.mention} to A3O8E5! Glory to the Alliance! 🏰", color=0xFFD700)
        embed.set_thumbnail(url=member.display_avatar.url)
        await welcome_ch.send(embed=embed)
    await ctx.send(f"✅ {member.mention} verified!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    embed = discord.Embed(title="🎫 Support Tickets", description="Need help? Click below!\n\n📋 A staff member will assist you shortly.", color=0xFFD700)
    await ctx.send(embed=embed, view=TicketView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason"):
    await member.ban(reason=reason)
    await ctx.send(f"🚫 {member} banned!")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member} kicked!")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int=10):
    await member.timeout(timedelta(minutes=minutes))
    await ctx.send(f"🔇 {member.mention} muted {minutes} min!")

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="No reason"):
    warns = load(WARN_FILE)
    uid = str(member.id)
    warns[uid] = warns.get(uid,0)+1
    save(WARN_FILE,warns)
    await ctx.send(f"⚠️ {member.mention} warned! ({warns[uid]}/3)")

@bot.command()
async def stats(ctx):
    g = ctx.guild
    embed = discord.Embed(title=f"📊 {g.name}", color=0xFFD700)
    embed.add_field(name="👥 Members", value=g.member_count)
    embed.add_field(name="💬 Channels", value=len(g.channels))
    embed.add_field(name="🎭 Roles", value=len(g.roles))
    await ctx.send(embed=embed)

bot.run(TOKEN)
