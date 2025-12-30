import discord
from discord import app_commands
from discord.ext import commands
from openai import OpenAI
import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    port = int(os.environ.get("PORT", 10000))  # Renderが自動割り当て
    app.run(host='0.0.0.0', port=port)

Thread(target=run).start()

# ===== 環境変数 =====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ===== OpenAI =====
client_ai = OpenAI(api_key=OPENAI_API_KEY)

# ===== Discord =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# サーバーごとに「ONのチャンネル」を管理
koizumi_channels = {}  # { guild_id: set(channel_id) }

# ===== 小泉AI（高速版）=====
def koizumi_reply(text: str) -> str:
    res = client_ai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたは小泉進次郎風に話します。"
                    "抽象的で同義反復を多用し、"
                    "『ということは、〜ということです』を必ず使ってください。"
                )
            },
            {"role": "user", "content": text}
        ],
        max_tokens=120,
        temperature=0.7
    )
    return res.choices[0].message.content

# ===== 起動 =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

# ===== /koizumi =====
@bot.tree.command(name="koizumi", description="このチャンネルで小泉モードをON/OFFします")
async def koizumi(interaction: discord.Interaction):
    gid = interaction.guild_id
    cid = interaction.channel_id

    if gid not in koizumi_channels:
        koizumi_channels[gid] = set()

    if cid in koizumi_channels[gid]:
        koizumi_channels[gid].remove(cid)
        status = "OFF"
    else:
        koizumi_channels[gid].add(cid)
        status = "ON"

    await interaction.response.send_message(
        f"🌀 このチャンネルの小泉モードを **{status}** にしました",
        ephemeral=True
    )

# ===== /koizumikobun =====
@bot.tree.command(name="koizumikobun", description="小泉構文を表示します")
async def koizumikobun(interaction: discord.Interaction):
    text = koizumi_reply("今の日本について一言")
    await interaction.response.send_message(text)

# ===== メッセージ監視 =====
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    gid = message.guild.id
    cid = message.channel.id

    if gid in koizumi_channels and cid in koizumi_channels[gid]:
        try:
            reply = koizumi_reply(message.content)
            await message.channel.send(reply)
        except:
            await message.channel.send("それは、エラーということです。")

    await bot.process_commands(message)

# ===== 実行 =====
bot.run(DISCORD_TOKEN)
