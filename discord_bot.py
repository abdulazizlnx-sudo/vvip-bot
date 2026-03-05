import discord
from discord.ext import commands
import aiohttp
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MIDDLEWARE_URL = os.environ.get("MIDDLEWARE_URL", "http://localhost:5000")
MIDDLEWARE_SECRET = os.environ.get("SECRET_KEY", "")
CLAIM_CHANNEL_ID = int(os.environ.get("CLAIM_CHANNEL_ID", "0"))
ADMIN_ROLES = os.environ.get("ADMIN_ROLES", "Admin,Owner").split(",")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

def is_admin(member):
    return any(role.name in ADMIN_ROLES for role in member.roles)

@bot.event
async def on_ready():
    print(f"✅ Bot aktif sebagai {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id == CLAIM_CHANNEL_ID and not message.content.startswith("!"):
        username = message.content.strip()
        if username and len(username) <= 20:
            await message.add_reaction("⏳")
            await message.reply(f"📋 Claim VVIP untuk username **{username}** sudah diterima!\nMenunggu persetujuan admin...", mention_author=False)
    await bot.process_commands(message)

@bot.command(name="givevvip")
async def give_vvip(ctx, roblox_username: str):
    if not is_admin(ctx.author):
        await ctx.reply("❌ Lo tidak punya izin!")
        return
    await ctx.reply(f"⏳ Memproses VVIP untuk **{roblox_username}**...")
    async with aiohttp.ClientSession() as session:
        try:
            payload = {"username": roblox_username, "secret": MIDDLEWARE_SECRET, "given_by": str(ctx.author)}
            async with session.post(f"{MIDDLEWARE_URL}/give-vvip", json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if data.get("success"):
                    embed = discord.Embed(title="✅ VVIP Berhasil Diberikan!", color=discord.Color.gold())
                    embed.add_field(name="Username", value=roblox_username, inline=True)
                    embed.add_field(name="Roblox ID", value=str(data.get("roblox_id", "?")), inline=True)
                    embed.add_field(name="Oleh", value=str(ctx.author), inline=True)
                    await ctx.reply(embed=embed)
                else:
                    await ctx.reply(f"❌ Gagal: **{data.get('error')}**")
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

@bot.command(name="approve")
async def approve_claim(ctx):
    if not is_admin(ctx.author):
        await ctx.reply("❌ Lo tidak punya izin!")
        return

    if not ctx.message.reference:
        await ctx.reply("❌ Reply ke pesan USER (username), bukan pesan bot!")
        return

    ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    # 🔥 Jangan izinkan approve pesan bot
    if ref_msg.author.bot:
        await ctx.reply("❌ Reply langsung ke pesan USER yang berisi username!")
        return

    roblox_username = ref_msg.content.strip()

    await ctx.reply(f"⏳ Memproses VVIP untuk **{roblox_username}**...")

    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "username": roblox_username,
                "secret": MIDDLEWARE_SECRET,
                "given_by": str(ctx.author)
            }

            async with session.post(
                f"{MIDDLEWARE_URL}/give-vvip",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:

                data = await resp.json()

                if data.get("success"):
                    await ref_msg.clear_reactions()
                    await ref_msg.add_reaction("✅")

                    embed = discord.Embed(title="✅ VVIP Approved!", color=discord.Color.gold())
                    embed.add_field(name="Username", value=roblox_username, inline=True)
                    embed.add_field(name="Roblox ID", value=str(data.get("roblox_id", "?")), inline=True)
                    embed.add_field(name="Admin", value=str(ctx.author), inline=True)

                    await ctx.reply(embed=embed)
                else:
                    await ref_msg.clear_reactions()
                    await ref_msg.add_reaction("❌")
                    await ctx.reply(f"❌ Gagal: **{data.get('error')}**")

        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

@bot.command(name="checkvvip")
async def check_vvip(ctx, roblox_username: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{MIDDLEWARE_URL}/check-vvip/{roblox_username}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                status = "✅ VVIP Aktif" if data.get("is_vvip") else "❌ Bukan VVIP"
                await ctx.reply(f"**{roblox_username}**: {status}")
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

bot.run(BOT_TOKEN)
