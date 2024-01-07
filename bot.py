#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ipaddress, asyncio, os, discord, random, traceback, sys, mc, typing, psycopg2, re, ast, platform, aiohttp, requests, logging, base64
from discord.ext import commands, tasks
from faker import Faker
from russian_names import RussianNames
from datetime import datetime, timezone, timedelta
from mc.builtin import validators, formatters
from discord import VoiceState, app_commands, Interaction, Member, User, Guild
from discord.app_commands import AppCommandError, Transform, Transformer
from io import BytesIO
from mc.builtin.formatters import usual_syntax
from discord.app_commands import Choice
from cfg import stexts_ordinary, stexts_nsfw, bot_invite_url, owner_id, guild_id, discord_url
from discord_logging.handler import DiscordHandler

bot = commands.Bot(command_prefix=commands.when_mentioned_or('.'), case_insensitive=True, help_command=None, intents=discord.Intents.all())
bot.owner_id = owner_id
bot.cd_mapping = commands.CooldownMapping.from_cooldown(10, 10, commands.BucketType.member)
snipes = {}
esnipes = {}
keepalive_kwargs = {
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 5,
    "keepalives_count": 5,
}
con = psycopg2.connect(os.environ.get('DATABASE_URL'), **keepalive_kwargs)
cur = con.cursor()
cur.execute("SELECT * FROM markov_chain;")
generator = mc.PhraseGenerator(samples=[r[0] for r in cur.fetchall()])
time_regex = re.compile(r"([0-9]+)(секунда|секунды|секунд|сек|мин|минута|минут|минуты|час|часа|часов|дней|дня|день|нед|неделя|недели|недель|месяц|месяца|месяцев|год|года|лет|[смчднгл])")
time_dict = {"ч": 3600, "с": 1, "м": 60, "д": 86400, "секунда": 1, "секунды": 1, "секунд": 1, "сек": 1, "мин": 60, "минута": 60, "минут": 60, "минуты": 60, "час": 3600, "часа": 3600, "часов": 3600, "день": 86400, "дня": 86400, "дней": 86400, "н": 604800, "нед": 604800, "неделя": 604800, "недели": 604800, "недель": 604800, "мес": 2592000, "месяц": 2592000, "месяца": 2592000, "месяцев": 2592000, "г": 31104000, "год": 31104000, "года": 31104000, "лет": 31104000, "л": 31104000}

def serverss():
  cif = str(len(bot.guilds))
  if cif[len(cif)-1] == '1' and cif[len(cif) - 2] + cif[len(cif) - 1] != '11':
     return f"{cif} сервер"
  elif cif[len(cif)-1] in ['2', '3', '4'] and cif[len(cif) - 2] + cif[len(cif) - 1] not in ['12', '13', '14']:
     return f"{cif} сервера"
  else:
     return f"{cif} серверов"

def mac_address():
    return "%02x:%02x:%02x:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def log_channel(guild_id):
  cur.execute("SELECT channel_id FROM logs WHERE guild_id = %s", (str(guild_id),))
  return cur.fetchone()

def is_autopub(guild_id):
  cur.execute("SELECT guild_id FROM autopub WHERE guild_id = %s", (str(guild_id),))
  return cur.fetchone() != None

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

def random_phone_num_generator():
    first = str(random.randint(100, 999))
    second = str(random.randint(1, 888)).zfill(3)
    last = (str(random.randint(1, 9998)).zfill(4))
    while last in ['1111', '2222', '3333', '4444', '5555', '6666', '7777', '8888']:
        last = (str(random.randint(1, 9998)).zfill(4))
    return '{}-{}-{}'.format(first, second, last)

@tasks.loop(seconds=3600)
async def snipes_update():
  global esnipes, snipes
  esnipes = {}
  snipes = {}

@tasks.loop(seconds=3600)
async def con_update():
  global con, cur
  co1 = con
  co2 = psycopg2.connect(os.environ.get('DATABASE_URL'), **keepalive_kwargs)
  cu2 = co2.cursor()
  con, cur = co2, cu2
  co1.close()

@tasks.loop(seconds=5)
async def activity_update():
  if not bot.activity:
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{serverss()} | {userss()}"))
  cur.execute("SELECT * FROM giveaways")
  giveaways = cur.fetchall()
  for giveaway in giveaways:
    if int(giveaway[3]) <= int(datetime.now(timezone.utc).timestamp()):
      try:
        givmes = await (await bot.fetch_channel(giveaway[0])).fetch_message(giveaway[2])
        reaction = [reaction for reaction in givmes.reactions if reaction.emoji == '🎉'][0]
        givuch = [user async for user in reaction.users() if isinstance(user, Member) and not user.bot]
        givpob = []
        if len(givuch) >= int(giveaway[5]):
          for i in range(int(giveaway[5])):
            sdel = False
            while not sdel:
              predv = random.choice(givuch)
              if predv not in givpob:
                givpob.append(predv)
                sdel = True
          givpob_str = '\n'.join([f'{pob} ({pob.mention})' for pob in givpob])
          givpob_ment = ', '.join([pob.mention for pob in givpob])
        await givmes.clear_reaction('🎉')
        if givpob:
          await givmes.edit(embed=discord.Embed(title="🎉 Розыгрыш!", description=f"**Розыгрыш окончен!**\nПриз: {giveaway[4]}\nУчастников розыгрыша: {len(givuch)}\nПобедители ({len(givpob)}):\n{givpob_str}", color=0x69FF00, timestamp=datetime.fromtimestamp(int(giveaway[3]), timezone.utc)))
          await givmes.reply(content=f"{givpob_ment}\nПоздравляю вас с победой и получением приза **{giveaway[4]}**!")
        else:
          await givmes.edit(embed=discord.Embed(title="🎉 Розыгрыш!", description=f"**Розыгрыш окончен!**\nПриз: {giveaway[4]}\nПобедителей нет", color=0x69FF00, timestamp=datetime.fromtimestamp(int(giveaway[3]), timezone.utc)))
          await givmes.reply(embed=discord.Embed(description=f"Победителей не удалось установить, так как участников розыгрыша ({len(givuch)}) меньше, чем установленных победителей ({len(givpob)}).", title="Ошибка! ❌", color=0xff0000))
        cur.execute("DELETE FROM giveaways WHERE message_id = %s;", (giveaway[2],))
        con.commit()
      except:
        cur.execute("DELETE FROM giveaways WHERE message_id = %s;", (giveaway[2],))
        con.commit()

async def start_zh(key):
  try:
    channel = await bot.fetch_channel(key[2])
    if isinstance(channel, discord.Thread):
      wchannel = channel.parent
    else:
      wchannel = channel
    webhooks = await wchannel.webhooks()
    webhook = [webhook for webhook in webhooks if(webhook.name == "Крутяк")]
    if webhook:
      webhook = webhook[0]
    else:
      webhook = await wchannel.create_webhook(name="Крутяк", avatar=await bot.user.avatar.read())
  except:
    return
  if key[4]:
    duration = datetime.fromtimestamp(int(key[4]), timezone.utc)
    if datetime.now(timezone.utc) >= duration:
      cur.execute("DELETE FROM spams WHERE channel_id = %s;", (str(channel.id),))
      con.commit()
      await channel.send("Спам остановлен по причине длительности! ☑️")
      lchannel = log_channel(channel.guild.id)
      if lchannel:
        try:
          lchannel = await bot.fetch_channel(lchannel[0])
          embed = discord.Embed(title="Спам остановлен по причине длительности! ☑️", color=0x42adf5)
          embed.add_field(name="Канал спама:", value=f"{channel.mention} (`#{channel.name}`)")
          await lchannel.send(embed=embed)
        except:
          try:
            await channel.guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
          except:
            pass
      return
    task = asyncio.create_task(spamt(key[0], key[1], channel, webhook, key[3], duration))
  else:
    task = asyncio.create_task(spamt(key[0], key[1], channel, webhook, key[3], key[4]))
  task.name = "Автоспам"
  task.channel_id = channel.id

@bot.event
async def on_ready():
  logging.info(f'Бот вошёл в систему как:\n{bot.user.name} (ID: {bot.user.id})\n------')
  cur.execute("select * from spams")
  results = cur.fetchall()
  [await start_zh(key) for key in results]
  con_update.start()
  activity_update.start()
  snipes_update.start()

@bot.event
async def on_raw_message_delete(event):
  cur.execute("DELETE FROM giveaways WHERE message_id = %s;", (str(event.message_id),))
  con.commit()

@bot.event
async def on_raw_bulk_message_delete(payload):
  for message_id in payload.message_ids:
    cur.execute("DELETE FROM giveaways WHERE message_id = %s;", (str(message_id),))
    con.commit()

@bot.event
async def on_guild_emojis_update(guild, before, after):
  now = datetime.now(timezone.utc) 
  lchannel = log_channel(guild.id)
  if not lchannel:
    return
  delemoji = None
  newemoji = None
  if len(before) > len(after):
    delemoji = [emoji for emoji in before if emoji not in after][0]
  elif len(before) < len(after):
    newemoji = [emoji for emoji in after if emoji not in before][0]
  else:
    try:
      upemoji = [emoji for emoji in after if emoji.name not in [emoji.name for emoji in before]][0]
      updemoji = [emoji for emoji in before if emoji.id == upemoji.id][0]
    except:
      return
  sdelal = None
  try:
    if delemoji:
      async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.emoji_delete):
        if entry.target.id == delemoji.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
          sdelal = entry.user
    elif newemoji:
      async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.emoji_create):
        if entry.target.id == newemoji.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
          sdelal = entry.user 
    else:
      async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.emoji_update):
        if entry.target.id == upemoji.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
          sdelal = entry.user 
  except:
    pass
  if delemoji:
    embed = discord.Embed(title="Удалено эмодзи!", description=f"Было удалено эмодзи [{delemoji.name}]({delemoji.url})", color=0xff3b05, timestamp=now).set_footer(text=f"ID эмодзи: {delemoji.id}")
  elif newemoji:
    embed = discord.Embed(title="Добавлено эмодзи!", description=f"Было добавлено эмодзи [{newemoji.name}]({newemoji.url}) ({newemoji})", color=0x75f542, timestamp=now).set_footer(text=f"ID эмодзи: {newemoji.id}")
  else:
    embed = discord.Embed(title="Обновлено эмодзи!", description=f"У эмодзи {upemoji} изменилось имя с [{updemoji.name}]({updemoji.url}) на [{upemoji.name}]({upemoji.url})", color=0x05cdff, timestamp=now).set_footer(text=f"ID эмодзи: {upemoji.id}")
  if sdelal:
    embed.add_field(name="Сделал это:", value=f"{sdelal} ({sdelal.mention})")
  try:
    lchannel = await bot.fetch_channel(lchannel[0])
    await lchannel.send(embed=embed)
  except:
    try:
      await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
    except:
      pass

@bot.event
async def on_guild_stickers_update(guild, before, after):
  now = datetime.now(timezone.utc) 
  lchannel = log_channel(guild.id)
  if not lchannel:
    return
  delstick = None
  newstick = None
  upstick = None
  if len(before) > len(after):
    delstick = [sticker for sticker in before if sticker not in after][0]
  elif len(before) < len(after):
    newstick = [sticker for sticker in after if sticker not in before][0]
  else:
    try:
      upstick = [sticker for sticker in after if [sticker.name, sticker.description, sticker.emoji] not in [[sticker.name, sticker.description, sticker.emoji] for sticker in before]][0]
      updstick = [sticker for sticker in before if sticker.id == upstick.id][0]
    except:
      return
  sdelal = None
  try:
    if delstick:
      async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.sticker_delete):
        if entry.target.id == delstick.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
          sdelal = entry.user
    elif newstick:
      async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.sticker_create):
        if entry.target.id == newstick.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
          sdelal = entry.user 
    else:
      async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.sticker_update):
        if entry.target.id == upstick.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
          sdelal = entry.user
  except:
    pass
  if delstick:
    embed = discord.Embed(title="Удалён стикер!", description=f"Был удалён стикер [{delstick.name}](https://cdn.discordapp.com/stickers/{delstick.id}.png)", color=0xff3b05, timestamp=now).set_footer(text=f"ID стикера: {delstick.id}").add_field(name="Привязанное эмодзи:", value=f":{delstick.emoji}:")
    if delstick.description:
      embed.add_field(name="Описание стикера:", value=delstick.description)
  elif newstick:
    embed = discord.Embed(title="Добавлен стикер!", description=f"Был добавлен стикер [{newstick.name}](https://cdn.discordapp.com/stickers/{newstick.id}.png)", color=0x75f542, timestamp=now).set_footer(text=f"ID стикера: {newstick.id}").add_field(name="Привязанное эмодзи:", value=f":{newstick.emoji}:")
    if newstick.description:
      embed.add_field(name="Описание стикера:", value=newstick.description)
  else:
    up_description = ""
    if updstick.name != upstick.name:
      up_description += f"Было изменено название стикера с `{updstick.name}` на `{upstick.name}`\n"
    if updstick.description != upstick.description:
      up_description += f"Было изменено описание стикера с `{updstick.description}` на `{upstick.description}`\n"
    if updstick.emoji != upstick.emoji:
      up_description += f"Было изменено привязанное эмодзи стикера с :{updstick.emoji}: на :{upstick.emoji}:"
    embed = discord.Embed(title="Обновлён стикер!", description=f"Был обновлён стикер [{upstick.name}](https://cdn.discordapp.com/stickers/{upstick.id}.png)", color=0x05cdff, timestamp=now).set_footer(text=f"ID стикера: {upstick.id}").add_field(name="Изменения:", value=up_description)
  if sdelal:
    embed.add_field(name="Сделал это:", value=f"{sdelal} ({sdelal.mention})")
  try:
    lchannel = await bot.fetch_channel(lchannel[0])
    try:
      await lchannel.send(embed=embed, stickers=[newstick or upstick])
    except:
      await lchannel.send(embed=embed)
  except:
    try:
      await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
    except:
      pass

@bot.event
async def on_message_edit(message_before, message_after):
    now = datetime.now(timezone.utc)
    guild = message_after.guild 
    if not guild:
      return
    lchannel = log_channel(guild.id)
    if message_after.author.bot:
      return
    try:
      esnipes[message_after.channel.id].append({'before': message_before, 'after': message_after})
    except:
      esnipes[message_after.channel.id] = []
      esnipes[message_after.channel.id].append({'before': message_before, 'after': message_after})
    if not lchannel:
      return
    embed = discord.Embed(color=0x03fcd7, title="Сообщение было изменено!", timestamp=now)
    if message_before.content and message_after.content:
      embed.description=f"**До:**```\n{message_before.content}```**После:**```\n{message_after.content}```"
    if message_after.content and not message_before.content:
      embed.description=f"**До этого не было содержания**\n**После:**```\n{message_after.content}```"
    embed.add_field(name="Канал:", value=f"{message_before.channel.mention} (`#{message_before.channel}`)")
    embed.add_field(name="Ссылка на сообщение:", value=f"[Перейти]({message_before.jump_url})")
    embed.set_author(name=message_before.author.display_name, icon_url=message_before.author.display_avatar, url=f"https://discord.com/users/{message_before.author.id}")
    embed.set_footer(text=f"ID: {message_before.id}")
    try:
      lchannel = await bot.fetch_channel(lchannel[0])
      await lchannel.send(embed=embed)
    except:
      try:
        await message_after.guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
      except:
        pass

async def add_message(message: discord.Message):
        mentioned = bot.user.mentioned_in(message)
        if mentioned and message.mention_everyone:
          return
        if message.type == discord.MessageType.reply and len(message.reference.resolved.embeds) != 0 and message.reference.resolved.author == bot.user and (bot.user.mentioned_in(message) or message.reference.resolved.type == discord.MessageType.chat_input_command):
          return
        if message.content:
          contex_regex = re.sub("https?://(?:www\.)?.+|(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?|<@!?(\d+)>|<@&(\d+)>|<#(\d+)>|@everyone|@here", "", message.content).strip()
          if contex_regex:
            cur.execute("SELECT data FROM markov_chain WHERE data = %s;", (contex_regex,))
            if not cur.fetchone():
              cur.execute("INSERT INTO markov_chain (data) VALUES (%s);", (contex_regex,))
              con.commit()
        try:
          cur.execute("SELECT reply_chance FROM channels_reply WHERE channel_id = %s", (str(message.channel.id),))
          if mentioned or random.random() <= float(cur.fetchone()[0]):
            await message.channel.typing()
            phrase = generator.generate_phrase(validators=[validators.chars_count(maximal=2000), validators.words_count(minimal=1)])
            phrase = random.choice([phrase, phrase.upper(), usual_syntax(phrase)])
            if mentioned:
              await message.reply(phrase, mention_author=True)
            else:
              if random.choice([True, False]):
                await message.reply(phrase, mention_author=False)
              else:
                await message.channel.send(phrase)
        except:
          pass

def is_blocked(user_id):
  cur.execute("SELECT id FROM chs WHERE id = %s;", (str(user_id),))
  if cur.fetchone():
    return True
  else:
    return False 

@bot.event
async def on_message(message: discord.Message):
      if not message.guild:
        return await bot.process_commands(message)
      if message.author == bot.user:
        return
      if isinstance(message.channel, discord.TextChannel):
        if message.channel.is_news():
          if is_autopub(message.guild.id):
            try:
              await message.publish()
            except:
              pass
      cur.execute("SELECT channel_id FROM channels_likes WHERE channel_id = %s", (str(message.channel.id),))
      if cur.fetchone():
        if bot.cd_mapping.get_bucket(message).update_rate_limit():
          cur.execute("DELETE FROM channels_likes WHERE channel_id = %s;", (str(message.channel.id),))
          con.commit()
          await message.channel.send(embed=discord.Embed(title="⚠️ Внимание! Шкала лайков была отключена!", description="Причина: флуд в канале шкалы", color=0xf59e42))
        else:
          try:
            await message.add_reaction('👍')
            await asyncio.sleep(0.5)
            await message.add_reaction('👎')
          except:
            pass
      if message.author.bot:
        return
      if message.content == bot.user.mention:
        try:
          await message.reply("Введи </хелп:1136698980584136804> для справки о командах!")
        except:
          pass
        return
      if isinstance(message.channel, discord.Thread):
        cur.execute("SELECT channel_id FROM channels_reply WHERE channel_id = %s", (str(message.channel.parent_id),))
      else:
        cur.execute("SELECT channel_id FROM channels_reply WHERE channel_id = %s", (str(message.channel.id),))
      if cur.fetchone():
        if not message.content.lower().startswith(('$', '&', '%', '€', '¥', '!', '.', '?', '+', '=', '~', '-', '_', 's?', 'L.', 'cp!', 'g.', 'g?', 'pls', ';', "'", 'NQN')):
          await add_message(message)
      await bot.process_commands(message)

@bot.event
async def on_thread_create(thread: discord.Thread):
  if isinstance(thread.parent, discord.ForumChannel):
    cur.execute("SELECT channel_id FROM channels_likes WHERE channel_id = %s", (str(thread.parent.id),))
    if cur.fetchone():
      try:
        message = await thread.fetch_message(thread.id)
        await message.add_reaction('👍')
        await asyncio.sleep(0.5)
        await message.add_reaction('👎')
      except:
        pass

@bot.tree.command(name='хелп', description='Справка о командах')
@app_commands.guild_only
async def help(interaction: Interaction):
  description = '''
</хелп:1136698980584136804> — Показывает это сообщение.
</логи:1136698980881944688> — Включает/Выключает логи на сервере.
</автопубликация:1136698980881944689> — Включает/Выключает автопубликацию новостей на сервере.
</спам активировать:1136698981578178594> — Начинает спам в указанном канале. Также команда может упоминать роль/участника. Могут использовать только люди с правом модерировать участников и упоминать @here с @everyone.
</спам остановить:1136698981578178594> — Останавливает спам в указанном канале.
</снайп:1136698980584136806> — Показывает удалённые сообщения в канале.
</еснайп:1136698980584136805> — Показывает изменённые сообщения.
</бусты:1136698980881944690> — Показывает информацию про бусты.
</генсообщений:1136698980584136809> — Устанавливает канал, где бот будет по умолчанию отвечать на сообщения людей. Могут использовать люди с правом управления сервером.
</лайки:1136698980584136810> — Устанавливает канал для шкалы лайков. В указанном канале под сообщениями/публикациями будут ставиться реакции 👍 и 👎.
</розыгрыши создать:1136698981578178593> — Создаёт розыгрыш.
</розыгрыши закончить:1136698981578178593> — Оканчивает розыгрыш раньше времени.
</розыгрыши удалить:1136698981578178593> — Удаляет розыгрыш.
</розыгрыши список:1136698981578178593> — Показывает список розыгрышей.
</аватар:1136698980584136813> — Показывает аватар участника.
</баннер:1136698980584136812> — Показывает баннер участника.
</токен:1136698981578178592> — Показывает начало токена участника.
</юзеринфо:1136698981578178591> — Выводит информацию об участнике.
</инфо:1136698980881944687> — Показывает информацию о боте.
</кнб:1136698981578178590> — Сыграем в камень-ножницы-бумага?
</iq:1136698980584136807> — Показывает IQ упомянутого человека, или ваш.
</взломжопы:1136698980584136808> — ~~Шуточно~~ взламывает жопу упомянутого человека, или вашу.
</дон:1136698980584136811> — Бот связывается с Рамзаном Кадыровым, чтобы спросить о вас/упомянутом пользователе и понять награждать ли пользователя, или нет.
'''
  embed = discord.Embed(title='Справка', description=description, color=interaction.user.color)
  embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar, url=f"https://discord.com/users/{interaction.user.id}")
  await interaction.response.send_message(embed=embed)

@bot.event
async def on_bulk_message_delete(messages):
  now = int(datetime.now(timezone.utc).timestamp())
  now1 = datetime.now(timezone.utc)
  try:
    snipes[messages[0].channel.id]
  except:
    snipes[messages[0].channel.id] = []
  deleted_user = False
  perms = False
  try:
    async for entry in messages[0].guild.audit_logs(limit=1, action=discord.AuditLogAction.message_bulk_delete):
      perms = True
      if entry.target.id == messages[0].channel.id and int(entry.created_at.timestamp()) == now:
        deleted_user = entry.user
  except:
    pass
  for message in messages:
    if not message.is_system():
      try:
        try:
          snipes[message.channel.id].append({'msg': message, 'perms': perms, 'deleted_user': deleted_user, 'files': [{'bytes': await a.read(use_cached=True), 'filename': a.filename} for a in message.attachments]})
        except:
          snipes[messages[0].channel.id] = []
          snipes[message.channel.id].append({'msg': message, 'perms': perms, 'deleted_user': deleted_user, 'files': [{'bytes': await a.read(use_cached=True), 'filename': a.filename} for a in message.attachments]})
      except:
        try:
          snipes[message.channel.id].append({'msg': message, 'perms': perms, 'deleted_user': deleted_user, 'files': [{'bytes': await a.read(use_cached=False), 'filename': a.filename} for a in message.attachments]})
        except:
          snipes[messages[0].channel.id] = []
          snipes[message.channel.id].append({'msg': message, 'perms': perms, 'deleted_user': deleted_user, 'files': [{'bytes': await a.read(use_cached=False), 'filename': a.filename} for a in message.attachments]})
  guild = messages[0].guild
  lchannel = log_channel(guild.id)
  if lchannel:
      embed = discord.Embed(color=0xfc4103, title=f"Очищено {len(messages)} сообщений!", description=f"Канал: {messages[0].channel.mention} (`#{messages[0].channel}`)", timestamp=now1)
      if deleted_user != False:
        embed.add_field(name="Сообщения удалил:", value = f"{deleted_user} ({deleted_user.mention})")
      messages_str = ""
      for message in messages:
        if not message.author.bot:
          message_str = f"<{message.author}>\n{message.content}"
          if message.attachments:
            message_str += f"\n[Вложения:]\n{', '.join([a.proxy_url for a in message.attachments])}"
          if message.stickers:
            message_str += f"\n[Стикеры:]\n{', '.join([s.url for s in message.stickers])}"
          message_str += "\n"
          messages_str += f"\n{message_str}"
      with open(f"{messages[0].channel.id}.txt", "w+", encoding="utf-8") as ds:
        ds.write(messages_str)
      try:
        lchannel = await bot.fetch_channel(lchannel[0])
        await lchannel.send(embed=embed, file=discord.File(f"{messages[0].channel.id}.txt"))
      except:
        try:
          await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass 
      os.remove(f"{messages[0].channel.id}.txt")
  
@bot.event
async def on_message_delete(message: discord.Message):
  if message.is_system() or message.author == bot.user:
    return
  if not message.guild:
    return
  now = int(datetime.now(timezone.utc).timestamp())
  now1 = datetime.now(timezone.utc)
  try:
    snipes[message.channel.id]
  except:
    snipes[message.channel.id] = []
  sdict = {}
  sdict['msg'] = message
  sdict['deleted_user'] = False
  sdict['perms'] = False
  try:
    sdict['files'] = [{'bytes': await a.read(use_cached=True), 'filename': a.filename} for a in message.attachments]
  except:
    sdict['files'] = [{'bytes': await a.read(use_cached=False), 'filename': a.filename} for a in message.attachments]
  try:
    async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
      sdict['perms'] = True
      if entry.target == message.author and entry.extra.channel.id == message.channel.id and int(entry.created_at.timestamp()) == now:
        sdict['deleted_user'] = entry.user
  except:
    pass
  snipes[message.channel.id].append(sdict)
  guild = message.guild
  lchannel = log_channel(guild.id)
  if lchannel:
      embed = discord.Embed(color=0xfc4103, title="Удалено сообщение!", timestamp=now1)
      if message.content:
        embed.description = f"**Содержание:**```\n{message.content}```"
      embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url, url=f"https://discord.com/users/{message.author.id}")
      embed.add_field(name="Канал:", value=f"{message.channel.mention} (`#{message.channel}`)")
      if message.type == discord.MessageType.reply:
        embed.add_field(name="Ответил на:", value=f"[Это сообщение]({message.reference.resolved.jump_url})")
      if sdict['deleted_user'] != False:
        embed.add_field(name="Сообщение удалил:", value = f"{sdict['deleted_user']} ({sdict['deleted_user'].mention})")
      if message.stickers:
        sr = ""
        for sticker in message.stickers:
          sr += f"\n[{sticker.name}]({sticker.url}) (ID: {sticker.id})"
        embed.add_field(name="Стикеры:", value = sr)
      files = [discord.File(BytesIO(field['bytes']), filename=field['filename']) for field in sdict['files']]
      embed.set_footer(text=f"ID: {message.id}")
      try:
        lchannel = await bot.fetch_channel(lchannel[0])
        await lchannel.send(embed=embed, files=files)
      except:
        try:
          await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass

async def snippet(ci: Interaction, channel, index: int, view=None, method: str=None):
  snipess = snipes[channel.id]
  rpos = len(snipess)
  try:
    snipess = snipess[int(index)]
  except:
    return await ci.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Произошло неожиданное изменение записей, вызовите команду, или нажмите кнопку ещё раз"), ephemeral=True)
  await ci.response.defer()
  s: discord.Message = snipess['msg']
  prava = snipess['perms']
  sniped_embed = discord.Embed(timestamp=s.created_at, color=s.author.color, description=s.content)
  sniped_embed.set_author(name=s.author.display_name, icon_url=s.author.display_avatar.url, url=f"https://discord.com/users/{s.author.id}")
  if s.type == discord.MessageType.reply:
    try:
      sniped_embed.add_field(name="Ответил на:", value=f"[Это сообщение]({s.reference.resolved.jump_url})")
    except:
      sniped_embed.add_field(name="Ответил на:", value=f"Удалённое сообщение")
  if prava:
    deleted_user = snipess['deleted_user']
    if deleted_user:
     sniped_embed.add_field(name="Сообщение удалил:", value = f"{deleted_user} ({deleted_user.mention})")
  else:
    sniped_embed.add_field(name="Внимание!", value = "Бот не имеет доступа к журналу аудита для корректной работы команды!")
  files = [discord.File(BytesIO(field['bytes']), filename=field['filename']) for field in snipess['files']]
  if s.stickers:
    sr = ""
    for sticker in s.stickers:
      sr += f"\n[{sticker.name}]({sticker.url}) (ID: {sticker.id})"
    sniped_embed.add_field(name="Стикеры:", value = sr)
  if s.components:
    cr = ""
    for component in s.components:
      if isinstance(component, discord.Button):
        opis = f"{component.emoji or component.label}"
        if component.label and component.emoji:
          opis += f"{ component.label}"
        cr += f"\nКнопка ({opis})"

    sniped_embed.add_field(name="Компоненты:", value=cr)
  sniped_embed.add_field(name="Позиция:", value=f"{index + 1} / {rpos}")
  if not view:
    view = snipe_archive(timeout=300)
  else:
    view.timeout = 300
  view.channel_id = channel.id
  view.author_id = ci.user.id
  embeds = [sniped_embed]
  if s.embeds and s.author.bot:
    if embeds[0].type == 'rich':
      embeds.insert(0, s.embeds[0])
  try:
    if method == "send":
      await ci.followup.send(embeds=embeds, files=files, view=view)
      view.message = await ci.original_response()
    elif method == "button_response":
      view.message = await ci.original_response()
      await ci.edit_original_response(embeds=embeds, attachments=files, view=view)
  except:
    if method == "send":
      await ci.followup.send(embeds=embeds, view=view, content="\n".join([a.proxy_url for a in s.attachments]))
      view.message = await ci.original_response()
    elif method == "button_response":
      view.message = await ci.original_response()
      await ci.edit_original_response(embeds=embeds, view=view, content="\n".join([a.proxy_url for a in s.attachments]))

@bot.tree.command(name="еснайп", description = "Показывает изменённые сообщения")
@app_commands.guild_only
@app_commands.describe(channel='Выберите канал для отображения', position='Введите позицию')
async def esnipe(interaction: Interaction, channel: typing.Union[discord.StageChannel, discord.TextChannel, discord.VoiceChannel, discord.Thread]=None, position: int=None):
  if not channel:
    channel = interaction.channel
  if channel.is_nsfw() and not interaction.channel.is_nsfw():
    return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Нельзя смотреть материалы с NSFW канала в канале без этой метки!"), ephemeral=True)
  rpos = len(esnipes[channel.id])
  if not position:
    position = rpos - 1
  else:
    position = position - 1
  es = esnipes[channel.id][position]
  before = es['before']
  after = es['after']
  if not before.content:
    before.content = "**Нет содержания**"
  if not after.content:
    after.content = "**Нет содержания**"
  view = esnipe_archive(timeout=300)
  view.channel_id = channel.id
  view.author_id = interaction.user.id
  await interaction.response.send_message(view=view, embed=discord.Embed(description=f"**До изменения:**\n{before.content}\n**После:**\n{after.content}", color=before.author.color).set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url, url=f"https://discord.com/users/{before.author.id}").add_field(name="Позиция:", value=f"{position + 1} / {rpos}").add_field(name="Ссылка на сообщение", value=f"[Перейти]({after.jump_url})"))
  view.message = await interaction.original_response()

@bot.tree.command(name='снайп', description='Показывает удалённые сообщения в канале')
@app_commands.guild_only
@app_commands.describe(channel='Выберите канал для отображения', position='Введите позицию')
async def snipe(interaction: Interaction, channel: typing.Union[discord.StageChannel, discord.TextChannel, discord.VoiceChannel, discord.Thread]=None, position: int=None):
  if not channel:
    channel = interaction.channel
  if channel.is_nsfw() and not interaction.channel.is_nsfw():
    return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Нельзя смотреть материалы с NSFW канала в канале без этой метки!"), ephemeral=True)
  if not position:
    position = len(snipes[channel.id]) - 1
  else:
    position = position - 1
  await snippet(interaction, channel, position, None, "send")

@snipe.error
async def snipe_error(interaction, error):
  if isinstance(getattr(error, "original", error), KeyError):
    await interaction.response.send_message(embed=discord.Embed(description="Нет удалённых сообщений в канале, либо вы ввели неверную позицию!", color=interaction.user.color), ephemeral=True)
  
@esnipe.error
async def esnipe_error(interaction, error):
  if isinstance(getattr(error, "original", error), KeyError):
    await interaction.response.send_message(embed=discord.Embed(description="Нет изменённых сообщений в канале, либо вы ввели неверную позицию!", color=interaction.user.color), ephemeral=True)

class esnipe_archive(discord.ui.View):
  async def on_timeout(self) -> None:
    if self.message.embeds[0].title == "✅ Успешно!":
      return
    for item in self.children:
      item.disabled = True
    try:
      await self.message.edit(view=self)
    except:
      pass

  @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="⬅")
  async def eback(self, interaction: Interaction, button: discord.ui.Button):
    ipos = None
    for field in interaction.message.embeds[0].fields:
      if field.name == "Позиция:":
        ipos = int(field.value.split()[0]) - 2
    if interaction.user.id != self.author_id:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Использовать интеграцию может только тот человек, который вызывал команду!", color=0xff0000), ephemeral=True)
    if ipos < 0:
      ipos = len(esnipes[self.channel_id]) - 1
    try:
      rpos = len(esnipes[self.channel_id])
      esnipes[self.channel_id][ipos]
    except:
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Вызовите новую команду из-за того, что кто-то сбросил, или изменил архив"), ephemeral=True)
    await interaction.response.defer()
    channel = await bot.fetch_channel(self.channel_id)
    self.timeout = 300
    es = esnipes[channel.id][ipos]
    before = es['before']
    after = es['after']
    if not before.content:
      before.content = "**Нет содержания**"
    if not after.content:
      after.content = "**Нет содержания**"
    await interaction.edit_original_response(view=self, embed=discord.Embed(description=f"**До изменения:**\n{before.content}\n**После:**\n{after.content}", color=before.author.color).set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url, url=f"https://discord.com/users/{before.author.id}").add_field(name="Позиция:", value=f"{ipos + 1} / {rpos}").add_field(name="Ссылка на сообщение", value=f"[Перейти]({after.jump_url})"))

  @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="➡")
  async def esoon(self, interaction: Interaction, button: discord.ui.Button):
    ipos = None
    for field in interaction.message.embeds[0].fields:
      if field.name == "Позиция:":
        ipos = int(field.value.split()[0])
    if interaction.user.id != self.author_id:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Использовать интеграцию может только тот человек, который вызывал команду!", color=0xff0000), ephemeral=True)
    if ipos >= len(esnipes[self.channel_id]):
      ipos = 0
    try:
      rpos = len(esnipes[self.channel_id])
      esnipes[self.channel_id][ipos]
    except:
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Вызовите новую команду из-за того, что кто-то сбросил, или изменил архив"), ephemeral=True)
    await interaction.response.defer()
    channel = await bot.fetch_channel(self.channel_id)
    self.timeout = 300
    es = esnipes[channel.id][ipos]
    before = es['before']
    after = es['after']
    if not before.content:
      before.content = "**Нет содержания**"
    if not after.content:
      after.content = "**Нет содержания**"
    await interaction.edit_original_response(view=self, embed=discord.Embed(description=f"**До изменения:**\n{before.content}\n**После:**\n{after.content}", color=before.author.color).set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url, url=f"https://discord.com/users/{before.author.id}").add_field(name="Позиция:", value=f"{ipos + 1} / {rpos}").add_field(name="Ссылка на сообщение", value=f"[Перейти]({after.jump_url})"))

  @discord.ui.button(style=discord.ButtonStyle.red, emoji="🗑️")
  async def edelete(self, interaction: Interaction, button: discord.ui.Button):
    if len(interaction.message.embeds) > 1:
      epos = 1
    else:
      epos = 0
    for field in interaction.message.embeds[epos].fields:
      if field.name == "Позиция:":
        position = int(field.value.split()[0]) - 1
    channel = await bot.fetch_channel(self.channel_id)
    if not channel.permissions_for(interaction.user).manage_messages:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="У вас нет права управлять сообщениями для использования этой кнопки!", color=0xff0000), ephemeral=True)
    try:
      snipess = esnipes[self.channel_id][position]
      if int(interaction.message.embeds[epos].author.url.replace("https://discord.com/users/", "")) == snipess['msg'].author.id:
        esnipes[self.channel_id].pop(position)
      else:
        await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Данное сообщение уже было удалено из архива!", color=0xff0000), ephemeral=True)
        return await interaction.followup.delete_message(interaction.message.id)
    except:
      await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Данное сообщение уже было удалено из архива!", color=0xff0000), ephemeral=True)
      return await interaction.followup.delete_message(interaction.message.id)
    emb = discord.Embed(title="✅ Успешно!", color=0x2ecc71, description=f"Заархивированное сообщение с позицией {position + 1} было удалено!", timestamp=datetime.now(timezone.utc))
    emb.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar, url=f"https://discord.com/users/{interaction.user.id}")
    await interaction.response.edit_message(embed=emb, attachments=[], view=None)

  @discord.ui.button(style=discord.ButtonStyle.red, emoji="🧹")
  async def ereset(self, interaction: Interaction, button: discord.ui.Button):
    if not interaction.user.guild_permissions.manage_messages:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="У вас нет права управлять сообщениями для использования этой кнопки!", color=0xff0000), ephemeral=True)
    try:
      esnipes.pop(self.channel_id)
    except:
      pass
    emb = discord.Embed(title="✅ Успешно!", color=0x2ecc71, description=f"Весь архив этого канала был стёрт!", timestamp=datetime.now(timezone.utc))
    emb.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar, url=f"https://discord.com/users/{interaction.user.id}")
    await interaction.response.edit_message(embed=emb, attachments=[], view=None)

class snipe_archive(discord.ui.View):
  async def on_timeout(self) -> None:
    if self.message.embeds[0].title == "✅ Успешно!":
      return
    for item in self.children:
      item.disabled = True
    try:
      await self.message.edit(view=self)
    except:
      pass

  @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="⬅")
  async def back(self, interaction: Interaction, button: discord.ui.Button):
    ipos = None
    epos = 0
    if len(interaction.message.embeds) > 1:
      epos = 1
    for field in interaction.message.embeds[epos].fields:
      if field.name == "Позиция:":
        ipos = int(field.value.split()[0]) - 2
    if interaction.user.id != self.author_id:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Использовать интеграцию может только тот человек, который вызывал команду!", color=0xff0000), ephemeral=True)
    if ipos < 0:
      ipos = len(snipes[self.channel_id]) - 1
    try:
      snipes[self.channel_id][ipos]
    except:
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Вызовите новую команду из-за того, что кто-то сбросил, или изменил архив"), ephemeral=True)
    channel = await bot.fetch_channel(self.channel_id)
    await snippet(interaction, channel, ipos, self, "button_response")

  @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="➡")
  async def soon(self, interaction: Interaction, button: discord.ui.Button):
    ipos = None
    epos = 0
    if len(interaction.message.embeds) > 1:
      epos = 1
    for field in interaction.message.embeds[epos].fields:
      if field.name == "Позиция:":
        ipos = int(field.value.split()[0])
    if interaction.user.id != self.author_id:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Использовать интеграцию может только тот человек, который вызывал команду!", color=0xff0000), ephemeral=True)
    if ipos >= len(snipes[self.channel_id]):
      ipos = 0
    try:
      snipes[self.channel_id][ipos]
    except:
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Вызовите новую команду из-за того, что кто-то сбросил, или изменил архив"), ephemeral=True)
    channel = await bot.fetch_channel(self.channel_id)
    await snippet(interaction, channel, ipos, self, "button_response")

  @discord.ui.button(style=discord.ButtonStyle.red, emoji="🗑️")
  async def sdelete(self, interaction: Interaction, button: discord.ui.Button):
    if len(interaction.message.embeds) > 1:
      epos = 1
    else:
      epos = 0
    for field in interaction.message.embeds[epos].fields:
      if field.name == "Позиция:":
        position = int(field.value.split()[0]) - 1
    channel = await bot.fetch_channel(self.channel_id)
    if not channel.permissions_for(interaction.user).manage_messages:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="У вас нет права управлять сообщениями для использования этой кнопки!", color=0xff0000), ephemeral=True)
    try:
      snipess = snipes[self.channel_id][position]
      if int(interaction.message.embeds[epos].author.url.replace("https://discord.com/users/", "")) == snipess['msg'].author.id:
        snipes[self.channel_id].pop(position)
      else:
        await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Данное сообщение уже было удалено из архива!", color=0xff0000), ephemeral=True)
        return await interaction.followup.delete_message(interaction.message.id)
    except:
      await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Данное сообщение уже было удалено из архива!", color=0xff0000), ephemeral=True)
      return await interaction.followup.delete_message(interaction.message.id)
    emb = discord.Embed(title="✅ Успешно!", color=0x2ecc71, description=f"Заархивированное сообщение с позицией {position + 1} было удалено!", timestamp=datetime.now(timezone.utc))
    emb.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar, url=f"https://discord.com/users/{interaction.user.id}")
    await interaction.response.edit_message(embed=emb, attachments=[], view=None)

  @discord.ui.button(style=discord.ButtonStyle.red, emoji="🧹")
  async def sreset(self, interaction: Interaction, button: discord.ui.Button):
    if not interaction.user.guild_permissions.manage_messages:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="У вас нет права управлять сообщениями для использования этой кнопки!", color=0xff0000), ephemeral=True)
    try:
      snipes.pop(self.channel_id)
    except:
      pass
    emb = discord.Embed(title="✅ Успешно!", color=0x2ecc71, description=f"Весь архив этого канала был стёрт!", timestamp=datetime.now(timezone.utc))
    emb.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar, url=f"https://discord.com/users/{interaction.user.id}")
    await interaction.response.edit_message(embed=emb, attachments=[], view=None)

def verbose_timedelta(t: timedelta) -> str:
    cif_str = ""
    if t >= timedelta(days=365):
      cif = int(t.days/365)
      t = t - timedelta(days=cif*365)
      if cif in [1, 21, 31, 41, 51]:
        cif_str += f"{cif} год "
      elif cif in [2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54]:
        cif_str += f"{cif} года "
      else:
        cif_str += f"{cif} лет "
    if t < timedelta(days=365) and t >= timedelta(days=30):
      cif = int(t.days/30)
      t = t - timedelta(days=cif*30)
      if cif in [1, 21, 31, 41, 51]:
        cif_str += f"{cif} месяц "
      elif cif in [2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54]:
        cif_str += f"{cif} месяца "
      else:
        cif_str += f"{cif} месяцев " 
    if t < timedelta(days=30) and t >= timedelta(days=1):
      cif = t.days
      t = t - timedelta(days=cif)
      if cif in [1, 21, 31, 41, 51]:
        cif_str += f"{cif} день "
      elif cif in [2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54]:
        cif_str += f"{cif} дня "
      else:
        cif_str += f"{cif} дней "
    if t < timedelta(days=1) and t >= timedelta(hours=1):
      cif = int(t.total_seconds()/3600)
      t = t - timedelta(hours=cif)
      if cif in [1, 21, 31, 41, 51]:
        cif_str += f"{cif} час "
      elif cif in [2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54]:
        cif_str += f"{cif} часа "
      else:
        cif_str += f"{cif} часов "
    if t < timedelta(hours=1) and t >= timedelta(minutes=1):
      cif = int(t.total_seconds()/60)
      t = t - timedelta(minutes=cif)
      if cif in [1, 21, 31, 41, 51]:
        cif_str += f"{cif} минуту "
      elif cif in [2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54]:
        cif_str += f"{cif} минуты "
      else:
        cif_str += f"{cif} минут " 
    if t < timedelta(minutes=1) and t >= timedelta(seconds=1):
      cif = t.seconds
      t = t - timedelta(seconds=cif)
      if cif in [1, 21, 31, 41, 51]:
        cif_str += f"{cif} секунду"
      elif cif in [2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54]:
        cif_str += f"{cif} секунды"
      else:
        cif_str += f"{cif} секунд"
    if cif_str[len(cif_str) - 1] == " ":
      cif_str = cif_str[:-1]
    return cif_str

@bot.event
async def on_member_remove(member: Member):
    now = datetime.now(timezone.utc)
    guild = member.guild
    channel = log_channel(guild.id)
    if channel:
      if member.bot:
        embed = discord.Embed(color=0x03fcf0, description=f"Бот **{member}** ({member.mention}) удалён с сервера", timestamp=now)
        embed.set_footer(text=f"ID: {member.id}")
        embed.set_thumbnail(url=member.display_avatar.url)
        try:
          channel = await bot.fetch_channel(channel[0])
          return await channel.send(embed=embed)
        except:
          try:
            await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
          except:
            pass
      try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
          if entry.target.id == member.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
            return
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
          if entry.target.id == member.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
            embed = discord.Embed(color=0xeb7d34, description=f"Участник **{member}** ({member.mention}) кикнут с сервера", timestamp=now)
            embed.set_footer(text=f"ID: {member.id}")
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Аккаунт создан:", value=f"<t:{int(member.created_at.timestamp())}:R>")
            embed.add_field(name="Пробыл на сервере:", value=f"{verbose_timedelta(datetime.now(timezone.utc) - member.joined_at)} (Зашёл: <t:{int(member.joined_at.timestamp())}>)")
            embed.add_field(name=f"Роли ({len(member.roles)}):", value="\n".join(list(reversed([role.mention if role != guild.default_role else "@everyone" for role in member.roles]))))
            embed.add_field(name="Модератор:", value=f"{entry.user} ({entry.user.mention})")
            if entry.reason:
              embed.add_field(name="Причина:", value=entry.reason)
            return await channel.send(embed=embed)
      except:
        pass
      embed = discord.Embed(color=0xe1eb34, description=f"Участник **{member}** ({member.mention}) вышел с сервера", timestamp=now)
      embed.set_footer(text=f"ID: {member.id}")
      embed.set_thumbnail(url=member.display_avatar.url)
      embed.add_field(name="Аккаунт создан:", value=f"<t:{int(member.created_at.timestamp())}:R>")
      embed.add_field(name="Пробыл на сервере:", value=f"{verbose_timedelta(datetime.now(timezone.utc) - member.joined_at)} (Зашёл: <t:{int(member.joined_at.timestamp())}>)")
      embed.add_field(name=f"Роли ({len(member.roles)}):", value="\n".join(list(reversed([role.mention if role != guild.default_role else "@everyone" for role in member.roles]))))
      try:
        channel = await bot.fetch_channel(channel[0])
        await channel.send(embed=embed)
      except:
        try:
          await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass

@bot.event
async def on_member_join(member: Member):
  guild = member.guild
  channel = log_channel(guild.id)
  if channel:
    if member.bot:
      embed = discord.Embed(color=0x03fcf0, description=f"Бот **{member}** ({member.mention}) добавлен на сервер", timestamp=member.joined_at)
      embed.set_footer(text=f"ID: {member.id}")
      embed.set_thumbnail(url=member.display_avatar.url)
      try:
        channel = await bot.fetch_channel(channel[0])
        return await channel.send(embed=embed)
      except:
        try:
          await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass
    embed = discord.Embed(color=0xa3ff5c, description=f"Участник **{member}** ({member.mention}) зашёл на сервер", timestamp=member.joined_at)
    embed.set_footer(text=f"ID: {member.id}")
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Аккаунт создан:", value=f"<t:{int(member.created_at.timestamp())}:R>")
    try:
      channel = await bot.fetch_channel(channel[0])
      await channel.send(embed=embed)
    except:
      try:
        await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
      except:
        pass

@bot.event
async def on_member_update(before, after):
 now = datetime.now(timezone.utc)
 lchannel = log_channel(after.guild.id)
 if not (after.guild.id in [967133588422266890, 956636182903652364] or lchannel):
     return
 if len(before.roles) < len(after.roles):
     newRole = next(role for role in after.roles if role not in before.roles)
     guild = after.guild
     embed = discord.Embed(color=0x42e6f5, title="Изменение ролей участника", description=f"Участнику {after} ({after.mention}) добавили роль {newRole.mention} (`@{newRole}`)", timestamp=now)
     embed.set_thumbnail(url=after.display_avatar.url)
     embed.set_footer(text=f"ID: {after.id}")
     try:
       async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
         if entry.target.id == after.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
           embed.add_field(name="Сделал это:", value=f"{entry.user} ({entry.user.mention})")
     except:
       pass
     try:
       lchannel = await bot.fetch_channel(lchannel[0])
       await lchannel.send(embed=embed)
     except:
       try:
         await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
       except:
         pass
 if len(before.roles) > len(after.roles):
     newRole = next(role for role in before.roles if role not in after.roles)
     guild = after.guild
     try:
       guild.get_role(newRole.id)
     except:
       return
     embed = discord.Embed(color=0x42e6f5, title="Изменение ролей участника", description=f"У {after} ({after.mention}) убрали роль {newRole.mention} (`@{newRole}`)", timestamp=now) 
     embed.set_footer(text=f"ID: {after.id}")
     embed.set_thumbnail(url=after.display_avatar.url)
     try:
       async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
         if entry.target.id == after.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
           embed.add_field(name="Сделал это:", value=f"{entry.user} ({entry.user.mention})")
     except:
       pass
     try:
       lchannel = await bot.fetch_channel(lchannel[0])
       await lchannel.send(embed=embed)
     except:
       try:
         await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
       except:
         pass
 if before.nick != after.nick:
     guild = after.guild
     embed = discord.Embed(color=0x42e6f5, title="Изменение никнейма участника", timestamp=now)
     embed.set_footer(text=f"ID: {after.id}")
     embed.set_thumbnail(url=after.display_avatar.url)
     if before.nick and after.nick:
       embed.description=f"У {after} ({after.mention}) поменялся никнейм с **{before.nick}** на **{after.nick}**"
     elif before.nick and not after.nick:
       embed.description=f"У {after} ({after.mention}) был удалён никнейм **{before.nick}**"
     else:
       embed.description=f"У {after} ({after.mention}) появился новый никнейм **{after.nick}**"
     try:
       async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
         if entry.target.id == after.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
           embed.add_field(name="Сделал это:", value=f"{entry.user} ({entry.user.mention})")
     except:
       pass
     try:
       lchannel = await bot.fetch_channel(lchannel[0])
       await lchannel.send(embed=embed)
     except:
       try:
         await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
       except:
         pass

@bot.event
async def on_member_unban(guild, user):
    now = datetime.now(timezone.utc)
    channel = log_channel(guild.id)
    if channel:
      embed = discord.Embed(color=0x49fc03, description=f"Участник **{user}** ({user.mention}) был разбанен", timestamp=now)
      embed.set_footer(text=f"ID: {user.id}")
      embed.set_thumbnail(url=user.display_avatar.url)
      embed.add_field(name="Аккаунт создан:", value=f"<t:{int(user.created_at.timestamp())}:R>")
      try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
          if entry.target.id == user.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
            embed.add_field(name="Модератор:", value=f"{entry.user} ({entry.user.mention})")
            if entry.reason:
              embed.add_field(name="Причина:", value=entry.reason)
      except:
        pass
      try:
        channel = await bot.fetch_channel(channel[0])
        await channel.send(embed=embed)
      except:
        try:
          await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass
  
@bot.event
async def on_guild_role_create(role):
    guild = role.guild
    lchannel = log_channel(guild.id)
    if lchannel:
      embed = discord.Embed(color=0x2cadf5, description=f"Создана новая роль: {role.mention} (`@{role}`)", timestamp=datetime.now(timezone.utc))
      embed.set_footer(text=f"ID: {role.id}")
      try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
          if entry.target.id == role.id:
            embed.add_field(name="Сделал это:", value=f"{entry.user} ({entry.user.mention})")
      except:
        pass
      try:
        lchannel = await bot.fetch_channel(lchannel[0])
        await lchannel.send(embed=embed)
      except:
        try:
          await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass

@bot.event
async def on_guild_role_delete(role):
    guild = role.guild
    lchannel = log_channel(guild.id)
    if lchannel:
      embed = discord.Embed(color=0xf5412c, description=f"Удалена роль: `@{role}`", timestamp=datetime.now(timezone.utc))
      embed.set_footer(text=f"ID: {role.id}")
      try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
          if entry.target.id == role.id:
            embed.add_field(name="Сделал это:", value=f"{entry.user} ({entry.user.mention})")
      except:
        pass
      try:
        lchannel = await bot.fetch_channel(lchannel[0])
        await lchannel.send(embed=embed)
      except:
        try:
          await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass

@bot.event
async def on_guild_channel_create(channel):
  guild = channel.guild
  lchannel = log_channel(guild.id)
  if lchannel:
      embed = discord.Embed(color=0x34ebae, description=f"Создан новый канал: {channel.mention} (`#{channel}`)", timestamp=datetime.now(timezone.utc))
      embed.set_footer(text=f"ID: {channel.id}")
      try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
          if entry.target.id == channel.id:
            embed.add_field(name="Сделал это:", value=f"{entry.user} ({entry.user.mention})")
      except:
        pass
      try:
        lchannel = await bot.fetch_channel(lchannel[0])
        await lchannel.send(embed=embed)
      except:
        try:
          await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass

@bot.event
async def on_member_ban(guild, member):
  now = datetime.now(timezone.utc)
  channel = log_channel(guild.id)
  if channel:
      if member.bot:
        return
      embed = discord.Embed(color=0xf59b42, description=f"Участник **{member}** ({member.mention}) был забанен", timestamp=now)
      embed.set_footer(text=f"ID: {member.id}")
      embed.set_thumbnail(url=member.display_avatar.url)
      embed.add_field(name="Аккаунт создан:", value=f"<t:{int(member.created_at.timestamp())}:R>")
      if isinstance(member, Member):
        embed.add_field(name="Пробыл на сервере:", value=f"{verbose_timedelta(datetime.now(timezone.utc) - member.joined_at)} (Зашёл: <t:{int(member.joined_at.timestamp())}>)")
        embed.add_field(name=f"Роли ({len(member.roles)}):", value="\n".join(list(reversed([role.mention if role != guild.default_role else "@everyone" for role in member.roles]))))
      try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
          if entry.target.id == member.id and int(entry.created_at.timestamp()) == int(now.timestamp()):
            embed.add_field(name="Модератор:", value=f"{entry.user} ({entry.user.mention})")
            if entry.reason:
              embed.add_field(name="Причина:", value=entry.reason)
      except:
        pass
      try:
        channel = await bot.fetch_channel(channel[0])
        await channel.send(embed=embed)
      except:
        try:
          await guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass
     
@bot.tree.command(name="iq", description="Вычисляет IQ пользователя")
@app_commands.guild_only
@app_commands.describe(member='Выберите участника')
async def intelligence(interaction: Interaction, member: User=None):
    if not member:
      member = interaction.user
    await interaction.response.send_message(content=member.mention, embed=discord.Embed(title = 'IQ вычислено!', description = f'{member.mention} У вас {random.randint(0, 200)} IQ!', color = 0x4FFFB7))

@bot.tree.command(name="взломжопы", description="Взламывает жопу пользователю")
@app_commands.guild_only
@app_commands.describe(member='Выберите участника')
async def hack(interaction: Interaction, member: User=None):
   if not member:
      member = interaction.user
   await interaction.response.defer()
   await interaction.followup.send(content=f"\nIP адрес (IPv4): {random.randint(100, 250)}.{random.randint(100, 250)}.{random.randint(0, 9)}.{random.randint(0, 9)}")
   try:
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"IP адрес (IPv6): {ipaddress.IPv6Address(random.randint(0, 2**128-1))}")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"MAC адрес: {mac_address()}")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"Номер телефона: {random_phone_num_generator()}")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"Местоположение (город): {Faker().address()}")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"Местоположение (координаты): {random.randint(0, 90)} градусов {random.choice(['северной широты', 'южной широты'])}, {random.randint(0, 180)} градусов {random.choice(['восточной долготы', 'западной долготы'])}")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"Настоящее ИОФ: {RussianNames().get_person()}")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"Захожу в аккаунт {member.mention} на YouTube'е")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content="Продаю канал на бирже")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"Взлымываю аккаунт {member.mention} в Discord'е")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content="Выхожу со всех серверов")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"Пишу маме {member.mention}")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content="Написал")
     await asyncio.sleep(1)
     await interaction.edit_original_response(content=f"~~Точно настоящий~~ взлом жопы {member.mention} проведён успешно! ✅")
   except:
     pass

def check_sp(channel_id):
  cur.execute("SELECT channel_id FROM spams WHERE channel_id = %s", (channel_id,))
  return cur.fetchone() != None
              
async def spamt(type, method, channel, webhook, ments=None, duration=None):
  if type == "default":
    if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.VoiceChannel):
      if channel.is_nsfw():
        stexts = stexts_nsfw
      else:
        stexts = stexts_ordinary
    else:
      stexts = stexts_ordinary
  else:
    stexts = [stext.strip() for stext in type.split("|")]
  if isinstance(channel, discord.Thread):
    thread = channel
  else:
    thread = None
  try:
    while check_sp(str(channel.id)):
      if duration:
        if datetime.now(timezone.utc) >= duration:
          cur.execute("DELETE FROM spams WHERE channel_id = %s;", (str(channel.id),))
          con.commit()
          await channel.send("Спам остановлен по причине длительности! ☑️")
          lchannel = log_channel(channel.guild.id)
          if lchannel:
            try:
              lchannel = await bot.fetch_channel(lchannel[0])
              embed = discord.Embed(title="Спам остановлен по причине длительности! ☑️", color=0x42adf5)
              embed.add_field(name="Канал спама:", value=f"{channel.mention} (`#{channel.name}`)")
              await lchannel.send(embed=embed)
            except:
              try:
                await channel.guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
              except:
                pass
          break
      text = random.choice(stexts)
      if ments:
        text = ments + "\n" + text
      if method == "webhook":
        if thread:
          await webhook.send(wait=True, content=text, thread=thread)
        else:
          await webhook.send(wait=True, content=text)
      else:
        await channel.send(content=text)
  except discord.errors.NotFound:
    cur.execute("DELETE FROM spams WHERE channel_id = %s;", (str(channel.id),))
    con.commit()
    return
  except discord.errors.HTTPException:
    await asyncio.sleep(3)
  except (discord.errors.DiscordServerError, aiohttp.client_exceptions.ClientOSError, aiohttp.client_exceptions.ServerDisconnectedError) as e:
    cur.execute("DELETE FROM spams WHERE channel_id = %s;", (str(channel.id),))
    con.commit()
    embed = discord.Embed(title=f'⚠️ Спам остановлен!', color=0xfcb603, timestamp=datetime.now(timezone.utc), description=f'Причина: Ошибка сервера Discord')
    await channel.send(embed=embed)
    lchannel = log_channel(channel.guild.id)
    if lchannel:
      try:
        lchannel = await bot.fetch_channel(lchannel[0])
        embed.add_field(name="Канал спама:", value=f"{channel.mention} (`#{channel.name}`)")
        await lchannel.send(embed=embed)
      except:
        try:
          await channel.guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass
    return

class InvalidDuration(AppCommandError):
  pass

class Duration(Transformer):
  async def transform(self, interaction: Interaction, value: str, /) -> timedelta:
    value = value.replace(" ", "")
    time = 0
    for v, k in time_regex.findall(value.lower()):
      time += time_dict[k]*float(v)
    if time == 0:
      await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Вы указали невалидную длительность!"), ephemeral=True)
      raise InvalidDuration()
    return timedelta(seconds=time)

class CustomSpamModal(discord.ui.Modal, title='Кастомный текст'):
    appeal = discord.ui.TextInput(label='Текст:', placeholder='Введите сюда текст. Если вы хотите несколько текстов, то разделите их символом |', required=True, style=discord.TextStyle.long)
    async def on_submit(self, interaction: Interaction):
      await spam_activate(interaction=interaction, type=self.appeal.value, method=self.method, channel=self.channel, duration=self.duration, mention=self.mention)

async def spam_activate(interaction, type, method, channel, duration, mention):
  if method == "webhook":
    try:
      if isinstance(channel, discord.Thread):
        wchannel = channel.parent
      else:
        wchannel = channel
      webhooks = await wchannel.webhooks()
      webhook = [webhook for webhook in webhooks if(webhook.name == "Крутяк")]
      if webhook:
        webhook = webhook[0]
      else:
        webhook = await wchannel.create_webhook(name="Крутяк", avatar=await bot.user.avatar.read())
    except:
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="У бота нет права управлять вебхуками для использования этой команды!"), ephemeral=True)
  else:
    webhook = None
  cur.execute("SELECT channel_id FROM spams WHERE channel_id = %s", (str(channel.id),)) 
  if cur.fetchone():
    await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", description="Спам уже включён в данном канале!", color=0xff0000), ephemeral=True)
  else:
    await interaction.response.defer()
    if duration:
      duration_timedelta = duration
      duration = datetime.now(timezone.utc) + duration
      await interaction.followup.send(f'Спам активирован на {verbose_timedelta(duration_timedelta)} (<t:{int(duration.timestamp())}:D>)! ☑️')
    else:
      await interaction.followup.send('Спам активирован! ☑️')
    if not channel == interaction.channel:
      if duration:
        await channel.send(f'Спам активирован по команде {interaction.user.mention} на {verbose_timedelta(duration_timedelta)} (<t:{int(duration.timestamp())}:D>)! ☑️')
      else:
        await channel.send(f'Спам активирован по команде {interaction.user.mention}! ☑️')
    if duration:
      cur.execute("INSERT INTO spams (type, method, channel_id, ments, timestamp) VALUES(%s, %s, %s, %s, %s);", (type, method, channel.id, mention, f"{int(duration.timestamp())}"))
    else:
      cur.execute("INSERT INTO spams (type, method, channel_id, ments, timestamp) VALUES(%s, %s, %s, %s, %s);", (type, method, channel.id, mention, duration))
    con.commit()
    task = asyncio.create_task(spamt(type, method, channel, webhook, mention, duration))
    task.name = "Спам"
    task.channel_id = channel.id
    lchannel = log_channel(interaction.guild.id)
    if lchannel:
      try:
        lchannel = await bot.fetch_channel(lchannel[0])
        embed = discord.Embed(title="Спам активирован! ☑️", color=0x42adf5).add_field(name="Сделал это:", value=f"{interaction.user} ({interaction.user.mention})")
        if channel != interaction.channel:
          embed.add_field(name="Канал спама:", value=f"{channel.mention} (`#{channel.name}`)")
          embed.add_field(name="Канал команды:", value=f"{interaction.channel.mention} (`#{interaction.channel.name}`)")
        else:
          embed.add_field(name="Канал спама и команды:", value=f"{channel.mention} (`#{channel.name}`)")
        if duration:
          embed.add_field(name="Длительность:", value=f"{verbose_timedelta(duration_timedelta)} (<t:{int(duration.timestamp())}:D>)")
        await lchannel.send(embed=embed)
      except:
        try:
          await interaction.guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass 

spam_group = app_commands.Group(name="спам", description="Спам в канале", guild_only=True, default_permissions=discord.Permissions(mention_everyone=True, moderate_members=True))

@spam_group.command(name="остановить", description="Останавливает спам в канале")
@app_commands.describe(channel='Выберите канал для спама')
async def spam_stop_command(interaction: Interaction, channel: typing.Union[discord.TextChannel, discord.Thread, discord.VoiceChannel]=None):
  if not channel:
    channel = interaction.channel
  cur.execute("SELECT channel_id FROM spams WHERE channel_id = %s", (str(channel.id),)) 
  if cur.fetchone():
    await interaction.response.defer()
    cur.execute("DELETE FROM spams WHERE channel_id = %s;", (str(channel.id),))
    con.commit()
    await interaction.followup.send('Спам остановлен! ☑️')
    if not channel == interaction.channel:
      await channel.send(f'Спам остановлен по команде {interaction.user.mention}! ☑️')
    lchannel = log_channel(interaction.guild.id)
    if lchannel:
      try:
        lchannel = await bot.fetch_channel(lchannel[0])
        embed = discord.Embed(title="Спам остановлен! ☑️", color=0x42adf5).add_field(name="Сделал это:", value=f"{interaction.user} ({interaction.user.mention})")
        if channel != interaction.channel:
          embed.add_field(name="Канал спама:", value=f"{channel.mention} (`#{channel.name}`)")
          embed.add_field(name="Канал команды:", value=f"{interaction.channel.mention} (`#{interaction.channel.name}`)")
        else:
          embed.add_field(name="Канал спама и команды:", value=f"{channel.mention} (`#{channel.name}`)")
        await lchannel.send(embed=embed)
      except:
        try:
          await interaction.guild.owner.send(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав для отправки логов!"))
        except:
          pass
  else:
    await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", description="Спам не включён в данном канале!", color=0xff0000), ephemeral=True)

@spam_group.command(name="активировать", description="Начинает спам в канале")
@app_commands.choices(type=[Choice(name="Спам текстом по умолчанию", value="default"), Choice(name="Спам кастомным текстом", value="custom")], method=[Choice(name="Спам через бота", value="bot"), Choice(name="Спам через вебхук", value="webhook")])
@app_commands.describe(type="Выберите тип спама", method="Выберите метод спама", channel='Выберите канал для спама', duration='Укажите длительность спама', mention_1='Упомяните роль/участника, которые будут пинговаться', mention_2='Упомяните роль/участника, которые будут пинговаться', mention_3='Упомяните роль/участника, которые будут пинговаться', mention_4='Упомяните роль/участника, которые будут пинговаться', mention_5='Упомяните роль/участника, которые будут пинговаться')
async def spam_activate_command(interaction: Interaction, type: str, method: str, channel: typing.Union[discord.TextChannel, discord.Thread, discord.VoiceChannel]=None, duration: Transform[str, Duration]="", mention_1: typing.Union[discord.Role, User]=None, mention_2: typing.Union[discord.Role, User]=None, mention_3: typing.Union[discord.Role, User]=None, mention_4: typing.Union[discord.Role, User]=None, mention_5: typing.Union[discord.Role, User]=None):
  if not channel:
    channel = interaction.channel
  if duration:
    if duration > timedelta(days=365) or duration < timedelta(seconds=3):
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Вы указали длительность, которая больше, чем 1 год, либо меньше, чем 3 секунды!"), ephemeral=True)
  if not isinstance(channel, typing.Union[discord.TextChannel, discord.Thread, discord.VoiceChannel]):
    return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Команду можно применять только к текстовым каналам, веткам и голосовым каналам!"), ephemeral=True)
  mention = []
  if mention_1:
    mention.append(mention_1)
  if mention_2:
    mention.append(mention_2)
  if mention_3:
    mention.append(mention_3)
  if mention_4:
    mention.append(mention_4)
  if mention_5:
    mention.append(mention_5)
  mention = [u.mention if u != interaction.guild.default_role else "@everyone" for u in mention]
  if mention:
    if bot.user.mention in mention:
      mention.remove(bot.user.mention)
    mention = " ".join(list(set(mention)))
  else:
    mention = ""
  if type == "custom":
    customspammodal = CustomSpamModal()
    customspammodal.method = method
    customspammodal.channel = channel
    customspammodal.duration = duration
    customspammodal.mention = mention
    await interaction.response.send_modal(customspammodal)
    return
  await spam_activate(interaction=interaction, type=type, method=method, channel=channel, duration=duration, mention=mention)

@bot.command(aliases=['сервера'])
@commands.is_owner()
async def guilds(ctx):
  guilds = ""
  for guild in bot.guilds:
    guilds += f"\n{guild.name} (ID: {guild.id}) — {len(guild.members)} участников"
  with open("guilds.txt", "w+", encoding="utf-8") as gs:
    gs.write(f"Сервера:{guilds}")
  await ctx.reply(file=discord.File("guilds.txt"))

@bot.tree.command(name="генсообщений", description="Устанавливает канал для бредовых ответов бота")
@app_commands.guild_only
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(channel='Выберите канал для ответов', reply_chance='Введите вероятность ответа бота в % (без %)')
async def set_channel(interaction: Interaction, channel: typing.Union[discord.TextChannel, discord.ForumChannel, discord.Thread, discord.VoiceChannel]=None, reply_chance: float=None):
  if not channel:
    channel = interaction.channel
  if channel.is_nsfw():
    return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Нельзя установить NSFW канал для ответов бота!"), ephemeral=True)
  cur.execute("SELECT channel_id FROM channels_reply WHERE channel_id = %s", (str(channel.id),))
  if cur.fetchone():
    cur.execute("DELETE FROM channels_reply WHERE channel_id = %s;", (str(channel.id),))
    con.commit()
    await interaction.response.send_message(embed=discord.Embed(description=f"Теперь бот игнорирует сообщения в канале {channel.mention}! ☑️", color=0x43ccfa))
  else:
    chperms = channel.permissions_for(interaction.guild.me)
    if not (chperms.read_messages and chperms.send_messages and chperms.read_message_history):
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав отправлять сообщения в канале и/или просматривать канал и/или читать историю сообщений"), ephemeral=True)
    if not reply_chance:
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Введите `reply_chance` для установки канала!"), ephemeral=True)
    if reply_chance < 0.01 or reply_chance > 100.0:
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Введите значение от 0.01 до 100!"), ephemeral=True)
    cur.execute("INSERT INTO channels_reply (channel_id, reply_chance) VALUES (%s, %s);", (channel.id, reply_chance/100))
    con.commit()
    await interaction.response.send_message(embed=discord.Embed(description=f"Теперь бот отвечает на сообщения в канале {channel.mention}! ☑️", color=0x43ccfa))

@bot.tree.command(name="лайки", description="Устанавливает канал для шкалы лайков")
@app_commands.guild_only
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(channel='Выберите канал для шкалы лайков')
async def set_likes_channel(interaction: Interaction, channel: typing.Union[discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.ForumChannel]=None):
  if not channel:
    channel = interaction.channel
  cur.execute("SELECT channel_id FROM channels_likes WHERE channel_id = %s", (str(channel.id),))
  if cur.fetchone():
    cur.execute("DELETE FROM channels_likes WHERE channel_id = %s;", (str(channel.id),))
    con.commit()
    await interaction.response.send_message(embed=discord.Embed(description=f"Шкала лайков убрана из канала {channel.mention}! ☑️", color=0x43ccfa))
  else:
    chperms = channel.permissions_for(interaction.guild.me)
    if not (chperms.read_messages and chperms.add_reactions and chperms.read_message_history):
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав добавлять реакции в канале и/или просматривать канал и/или читать историю сообщений"), ephemeral=True)
    cur.execute("INSERT INTO channels_likes (channel_id) VALUES (%s);", (channel.id,))
    con.commit()
    if isinstance(channel, discord.ForumChannel):
      await interaction.response.send_message(embed=discord.Embed(description=f"Шкала лайков добавлена в канал {channel.mention}! ☑️\nТеперь под публикациями форума будут ставиться реакции 👍 и 👎.", color=0x43ccfa))
    else:
      await interaction.response.send_message(embed=discord.Embed(description=f"Шкала лайков добавлена в канал {channel.mention}! ☑️\nТеперь под сообщениями канала будут ставиться реакции 👍 и 👎.", color=0x43ccfa))

@bot.tree.command(name='дон', description='Бот связывается с Рамзаном Кадыровым')
@app_commands.guild_only
async def don(interaction: Interaction):
  await interaction.response.send_message(random.choice(['Чечня гордица вами дон!\nРазман катырав предаставмц вам 2 авца жына дон!\nПрадалжайте радовать чечня!', 'Чечня не гордица вами дон!\nРазман катырав атаброл у вос 2 авца жына дон!']))

def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

@bot.command(name="run", description="Запустить команду", guild=discord.Object(id=guild_id))
@commands.is_owner()
async def run(ctx, *, cmd: str):
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
        'ctx': ctx,
        '__import__': __import__
    }
    exec(compile(parsed, filename="<ast>", mode="exec"), env)
    await eval(f"{fn_name}()", env)
    await ctx.reply(content="✅ Команда выполнена!")

@run.error
async def run_error(ctx, error):
  await ctx.reply(embed=discord.Embed(title="❌ Произошла ошибка!", color=0xff0000, description=f"```py\n{error}```"))

@bot.command()
@commands.is_owner()
async def sync(ctx: commands.Context, guild_id: int=None):
  if guild_id:
    await bot.tree.sync(guild=discord.Object(id=guild_id))
  else:
    await bot.tree.sync(guild=None)
  await ctx.send("☑️ Синхронизировано!")

def db_remove(channel):
  cur.execute("DELETE FROM spams WHERE channel_id = %s;", (str(channel.id),))
  cur.execute("DELETE FROM giveaways WHERE channel_id = %s;", (str(channel.id),))
  con.commit()

@bot.event
async def on_guild_remove(guild: Guild):
  async with aiohttp.ClientSession() as session:
    webhook = discord.Webhook.from_url(os.environ['WEBHOOK_URL'], session=session)
    cur.execute("DELETE FROM giveaways WHERE guild_id = %s;", (str(guild.id),))
    con.commit()
    [db_remove(channel) for channel in guild.channels]
    embed = discord.Embed(title="Бот был кикнут/забанен с сервера", description=f"Данные о нём были стёрты\nУчастников: {guild.member_count}\nID сервера: {guild.id}", color=0x9f0000, timestamp=datetime.now(timezone.utc))
    if guild.icon:
      embed.set_footer(icon_url=guild.icon.url, text=guild.name)
    else:
      embed.set_footer(text=guild.name)
    await webhook.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
  guild = channel.guild
  lchannel = log_channel(guild.id)
  db_remove(channel)
  cur.execute("DELETE FROM channels_reply WHERE channel_id = %s;", (str(channel.id),))
  cur.execute("DELETE FROM logs WHERE channel_id = %s;", (str(channel.id),))
  con.commit()
  if lchannel:
    try:
      lchannel = await bot.fetch_channel(lchannel[0])
      embed = discord.Embed(color=0xf52c3f, description=f"Удалён канал: `#{channel}`", timestamp=datetime.now(timezone.utc))
      embed.set_footer(text=f"ID: {channel.id}")
      try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
          if entry.target.id == channel.id:
            embed.add_field(name="Сделал это:", value=f"{entry.user} ({entry.user.mention})")
      except:
        pass
      await lchannel.send(embed=embed)
    except:
      pass

@bot.event
async def on_guild_join(guild: Guild):
  uspeh = False
  for channel in guild.text_channels:
    if uspeh:
      break
    try:
      await channel.send(embed=discord.Embed(color=0x42f593, title="Привет! 👋", description=f"Спасибо, что добавили меня на ваш сервер!\nЯ — крутой бот с кучей функций! Подробнее о командах — </хелп:1136698980584136804>\nЕсли возникнут вопросы, обращайтесь в наш [Discord сервер]({discord_url})!\nВсего доброго!"))
      uspeh = True
    except:
      pass
  async with aiohttp.ClientSession() as session:
    webhook = discord.Webhook.from_url(os.environ['WEBHOOK_URL'], session=session)
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
    await webhook.send(embed=embed)

@bot.tree.command(name='баннер', description='Показывает баннер участника')
@app_commands.describe(member='Выберите участника')
async def banner_cmd(interaction: Interaction, member: typing.Union[Member, User]=None):
  if not member:
    member = interaction.user
  user = await bot.fetch_user(member.id)
  if not user.banner:
    return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="У участника нет баннера!"), ephemeral=True)
  await interaction.response.defer()
  user_banner = await user.banner.to_file()
  await interaction.followup.send(embed=discord.Embed(title=f"Баннер {user}", color=member.color).set_image(url=f"attachment://{user_banner.filename}").set_footer(text="Внимание! Бот не может отображать баннер участника на определённом сервере, а только общий баннер, это ограничение Discord"), file=user_banner)

@bot.tree.command(name='аватар', description='Показывает аватар участника')
@app_commands.describe(member='Выберите участника')
async def avatar_cmd(interaction: Interaction, member: typing.Union[Member, User]=None):
  await interaction.response.defer()
  if not member:
    member = interaction.user
  embeds = []
  avatars = []
  user = await bot.fetch_user(member.id)
  try:
    user_avatar = await user.display_avatar.to_file()
  except:
    user_avatar = await user.display_avatar.to_file(use_cached=True)
  embeds.append(discord.Embed(title=f"Аватар {user}", color=member.color, url=f"https://discord.com/users/{member.id}").set_image(url=f"attachment://{user_avatar.filename}"))
  avatars.append(user_avatar)
  if isinstance(member, Member):
    if member.guild_avatar:
      try:
        guild_avatar = await member.display_avatar.to_file()
      except:
        guild_avatar = await member.display_avatar.to_file(use_cached=True)
      embeds.append(discord.Embed(title=f"Аватар {user} на сервере", color=member.color, url=f"https://discord.com/users/{member.id}").set_image(url=f"attachment://{guild_avatar.filename}"))
      avatars.append(guild_avatar)
  await interaction.followup.send(embeds=embeds, files=avatars)

class info_view(discord.ui.View):
  def __init__(self):
    super().__init__()
    self.add_item(discord.ui.Button(style=discord.ButtonStyle.url, url=bot_invite_url, emoji='🔗', label='Добавить бота!'))
    self.add_item(discord.ui.Button(style=discord.ButtonStyle.url, url=discord_url, emoji='🛠️', label='Discord сервер'))

def userss():
  cif = str(len(bot.users))
  if cif[len(cif)-1] == '1' and cif[len(cif) - 2] + cif[len(cif) - 1] != '11':
     return f"{cif} пользователь"
  elif cif[len(cif)-1] in ['2', '3', '4'] and cif[len(cif) - 2] + cif[len(cif) - 1] not in ['12', '13', '14']:
     return f"{cif} пользователя"
  else:
     return f"{cif} пользователей"

def frazess():
  cur.execute("SELECT count(*) FROM markov_chain;")
  cif = str(cur.fetchone()[0])
  if cif[len(cif)-1] == '1' and cif[len(cif) - 2] + cif[len(cif) - 1] != '11':
     return f"{cif} фраза"
  elif cif[len(cif)-1] in ['2', '3', '4'] and cif[len(cif) - 2] + cif[len(cif) - 1] not in ['12', '13', '14']:
     return f"{cif} фразы"
  else:
     return f"{cif} фраз"

@bot.tree.command(name='инфо', description='Показывает информацию о боте')
@app_commands.guild_only
async def info_cmd(interaction: Interaction):
  embed = discord.Embed(title="Информация о боте", color=0x4287f5, description=f"Shard {interaction.guild.shard_id + 1} / {bot.shard_count}")
  embed.add_field(name="Разработчик", value=f"<@{owner_id}>", inline=True)
  embed.add_field(name="Статистика", value=f"{serverss()}\n{userss()}\n{frazess()}", inline=True)
  embed.add_field(name="Программные характеристики", value=f"ОС: [Linux](https://www.linux.org/)\nХостинг: [Railway](https://railway.app/)\nВерсия [Python](https://www.python.org/): {platform.python_version()}\nВерсия [discord.py](https://discordpy.readthedocs.io/en/stable/intro.html#installing): {discord.__version__}", inline=True)
  embed.add_field(name="Предыстория", value="*Повествование ведётся от имени разработчика*\nУвидел я на сервере Failure Project бота с функцией публикации ембедов, потом сделал такого же и осваивал питон, затем понял, что бот говно нефункциональное и удалил его, затем создал этого. Потом я удалил Крутяка и пересоздал его, ибо бот не был рассчитан на широкие массы", inline=False)
  embed.add_field(name="Ссылки", value="[Политика конфиденциальности](https://docs.google.com/document/d/1dcsigKBWaju9-3L2VVOt7-zltu9-tNFE_dkaAcE8P7w)\n[Условия использования](https://docs.google.com/document/d/1qJAtNv4Skl5rh5epdahXzCeaDU5kwRwbg3CYqsU-esw)")
  await interaction.response.send_message(embed=embed, view=info_view())

@bot.tree.command(name='логи', description='Включает/Выключает логи на сервере')
@app_commands.guild_only
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(channel='Выберите канал для логов')
async def logs_cmd(interaction: Interaction, channel: discord.TextChannel=None):
  if not channel:
    channel = interaction.channel
  if log_channel(interaction.guild.id):
    cur.execute("DELETE FROM logs WHERE guild_id = %s;", (str(interaction.guild.id),))
    con.commit()
    return await interaction.response.send_message(embed=discord.Embed(color=0x0ffc03, title="✅ Успешно!", description="Логи были выключены!"))
  else:
    chperms = channel.permissions_for(interaction.guild.me)
    if not (chperms.read_messages and chperms.send_messages and chperms.read_message_history):
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не имеет прав отправлять сообщения в канале и/или просматривать канал и/или читать историю сообщений"), ephemeral=True)
    cur.execute("INSERT INTO logs (guild_id, channel_id) VALUES(%s, %s);", (interaction.guild.id, channel.id))
    con.commit()
    return await interaction.response.send_message(embed=discord.Embed(color=0x0ffc03, title="✅ Успешно!", description=f"Логи были включены! Они будут присылаться в {channel.mention}"))

@bot.tree.command(name='автопубликация', description='Включает/Выключает автопубликацию новостей на сервере')
@app_commands.guild_only
@app_commands.default_permissions(manage_guild=True)
async def autopub_cmd(interaction: Interaction):
  if is_autopub(interaction.guild.id):
    cur.execute("DELETE FROM autopub WHERE guild_id = %s;", (str(interaction.guild.id),))
    con.commit()
    return await interaction.response.send_message(embed=discord.Embed(color=0x0ffc03, title="✅ Успешно!", description="Автопубликация была выключена!"))
  else:
    news_channels = [channel for channel in interaction.guild.text_channels if channel.is_news()]
    if not news_channels:
      return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="На сервере нет новостных каналов!"), ephemeral=True)
    for channel in news_channels:
      chperms = channel.permissions_for(interaction.guild.me)
      if not (chperms.read_messages and chperms.send_messages and chperms.manage_messages and chperms.read_message_history):
        return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Бот не может публиковать сообщения в новостных каналах! Убедитесь, что в каждом новостном канале бот может просматривать сам канал, отправлять сообщения, управлять ими и читать историю сообщений"), ephemeral=True)
    cur.execute("INSERT INTO autopub (guild_id) VALUES(%s);", (interaction.guild.id,))
    con.commit()
    return await interaction.response.send_message(embed=discord.Embed(color=0x0ffc03, title="✅ Успешно!", description=f"Автопубликация включена!"))

@bot.tree.command(name='бусты', description='Показывает информацию про бусты')
@app_commands.guild_only
async def boosts_command(interaction: Interaction):
  guild = interaction.guild
  if guild.premium_subscription_count == 0:
    return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="На сервере нет бустов!", color=0xff0000), ephemeral=True)
  boosters = guild.premium_subscribers
  boosters_str = ""
  for booster in boosters:
    boosters_str += f"\n{booster} ({booster.mention}) — Бустит с <t:{int(booster.premium_since.timestamp())}>"
  if boosters:
    return await interaction.response.send_message(embed=discord.Embed(title="Информация про бусты", color=0xf569fa, description=f"Уровень сервера: {guild.premium_tier}\nКоличество бустеров: {len(boosters)}\nКоличество бустов: {guild.premium_subscription_count}\nРоль для бустеров: {guild.premium_subscriber_role.mention}\nБустеры:{boosters_str}"))
  else:
    return await interaction.response.send_message(embed=discord.Embed(title="Информация про бусты", color=0xf569fa, description=f"Уровень сервера: {guild.premium_tier}\nКоличество бустеров: {len(boosters)}\nКоличество бустов: {guild.premium_subscription_count}\nРоль для бустеров: {guild.premium_subscriber_role.mention}"))

class knb_bot(discord.ui.Select):
    def __init__(self):
      super().__init__(placeholder='Ваш вариант', min_values=1, max_values=1, options=[discord.SelectOption(label='Камень', description='Выбрать камень', emoji='✊'), discord.SelectOption(label='Ножницы', description='Выбрать ножницы', emoji='✌️'), discord.SelectOption(label='Бумага', description='Выбрать бумагу', emoji='✋')])

    async def callback(self, interaction: Interaction):
      if self.view.author == interaction.user:
        uvy = self.values[0]
        bvy = random.choice(["Камень", "Ножницы", "Бумага"])
        if bvy == "Камень":
          if uvy == "Ножницы":
            pobeda = True
          elif uvy == "Бумага":
            pobeda = False
          else:
            pobeda = None
        elif bvy == "Ножницы":
          if uvy == "Ножницы":
            pobeda = None
          elif uvy == "Бумага":
            pobeda = True
          else:
            pobeda = False
        else:
          if uvy == "Ножницы":
            pobeda = False
          elif uvy == "Бумага":
            pobeda = None
          else:
            pobeda = True
        if pobeda == True:
          await interaction.response.edit_message(embed=discord.Embed(title="КНБ", description=f"Ваш выбор: `{uvy}`\nМой выбор: `{bvy}`\nЯ победил! Хихихиха <:hihihiha:1006949852845965435>", color=self.view.message.embeds[0].color), view=None)
        elif pobeda == False:
          await interaction.response.edit_message(embed=discord.Embed(title="КНБ", description=f"Ваш выбор: `{uvy}`\nМой выбор: `{bvy}`\nВы победили! Я плакаю 😭", color=self.view.message.embeds[0].color), view=None)
        else:
          await interaction.response.edit_message(embed=discord.Embed(title="КНБ", description=f"Ваш выбор: `{uvy}`\nМой выбор: `{bvy}`\nНичья!", color=self.view.message.embeds[0].color), view=None)
      else:
        return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Использовать интеграцию может только тот человек, который вызывал команду!", color=0xff0000), ephemeral=True)

class knb_bot_view(discord.ui.View):
  async def on_timeout(self) -> None:
    try:
      message = await self.message.channel.fetch_message(self.message.id)
      if not message.embeds[0].title == "КНБ выбор":
        return
      for item in self.children:
        item.disabled = True
      await message.edit(view=self, embed=discord.Embed(title="КНБ выбор", description="Проигнорили...", color=0x747880))
    except:
      return

  def __init__(self, timeout):
    super().__init__()
    self.add_item(knb_bot())

class knb_user(discord.ui.Select):
    def __init__(self):
      super().__init__(placeholder='Ваш вариант', min_values=1, max_values=1, options=[discord.SelectOption(label='Камень', description='Выбрать камень', emoji='✊'), discord.SelectOption(label='Ножницы', description='Выбрать ножницы', emoji='✌️'), discord.SelectOption(label='Бумага', description='Выбрать бумагу', emoji='✋')])

    async def callback(self, interaction: Interaction):
      selected1 = None
      user1 = self.view.user1
      user2 = self.view.user2
      if interaction.user.id not in [user1.id, user2.id]:
        return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Вы не участвуете в этой игре!", color=0xff0000), ephemeral=True)
      try:
        selected1 = self.view.selected1
      except:
        pass
      if (interaction.user.id == user2.id and selected1 == None) or (interaction.user.id == user1.id and selected1):
        return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Сейчас не ваш ход!", color=0xff0000), ephemeral=True)
      if not selected1:
        self.view.selected1 = self.values[0]
        await interaction.response.edit_message(embed=discord.Embed(title="КНБ выбор", description=f"{user1.mention} совершил ход\n{user2.mention} ваша очередь!", color=self.view.message.embeds[0].color), view=self.view)
      else:
        selected2 = self.values[0]
        if selected1 == "Камень":
          if selected2 == "Ножницы":
            pobeda = user1
          elif selected2 == "Бумага":
            pobeda = user2
          else:
            pobeda = None
        elif selected1 == "Ножницы":
          if selected2 == "Ножницы":
            pobeda = None
          elif selected2 == "Бумага":
            pobeda = user1
          else:
            pobeda = user2
        else:
          if selected2 == "Ножницы":
            pobeda = user2
          elif selected2 == "Бумага":
            pobeda = None
          else:
            pobeda = user1
        if not pobeda:
          await interaction.response.edit_message(embed=discord.Embed(title="КНБ", description=f"Выбор {user1.mention}: `{selected1}`\nВыбор {user2.mention}: `{selected2}`\nНичья!", color=self.view.message.embeds[0].color), view=None)
        else:
          await interaction.response.edit_message(embed=discord.Embed(title="КНБ", description=f"Выбор {user1.mention}: `{selected1}`\nВыбор {user2.mention}: `{selected2}`\nПобедил: {pobeda.mention}", color=self.view.message.embeds[0].color), view=None)

class knb_user_view(discord.ui.View):
  async def on_timeout(self) -> None:
    try:
      message = await self.message.channel.fetch_message(self.message.id)
      if not message.embeds[0].title == "КНБ выбор":
        return
      for item in self.children:
        item.disabled = True
      await message.edit(view=self, embed=discord.Embed(title="КНБ выбор", description="Проигнорили...", color=0x747880))
    except:
      return

  def __init__(self, timeout):
    super().__init__()
    self.add_item(knb_user())

@bot.tree.command(name='кнб', description='Сыграем в камень-ножницы-бумага?')
@app_commands.guild_only
@app_commands.describe(member='Выберите с кем играть')
async def knb(interaction: Interaction, member: Member=None):
  if not member:
    view = knb_bot_view(timeout=300)
    view.author = interaction.user
    await interaction.response.send_message(embed=discord.Embed(title="КНБ выбор", description="Хорошо, вы предпочли играть с ботом. Выберите вариант в меню снизу", color=discord.Color.random()), view=view)
    view.message = await interaction.original_response()
  else:
    if member.bot:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Выберите человека, а не бота!", color=0xff0000), ephemeral=True)
    if member == interaction.user:
      return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Нельзя играть с самим собой!", color=0xff0000), ephemeral=True)
    view = knb_user_view(timeout=300)
    ralis = [interaction.user, member]
    view.user1 = random.choice(ralis)
    ralis.remove(view.user1)
    view.user2 = ralis[0]
    await interaction.response.send_message(content=" ".join([mem.mention for mem in [interaction.user, member]]), embed=discord.Embed(title="КНБ выбор", description=f"Начинаем игру!\nХод за {view.user1.mention}", color=discord.Color.random()), view=view)
    view.message = await interaction.original_response()

@bot.tree.command(name="юзеринфо", description="Выводит информацию об участнике")
@app_commands.describe(member="Выберите участника")
async def userinfo(interaction: Interaction, member: typing.Union[Member, User]=None):
  if not member:
    member = interaction.user
  ring = [f"Тэг: {member}", f"Создал аккаунт: <t:{int(member.created_at.timestamp())}:R>"]
  if member.global_name:
    ring.append(f"Глобальный никнейм: {member.global_name}")
  if isinstance(member, Member):
    ring.append(f"Присоединился к серверу: <t:{int(member.joined_at.timestamp())}:R>")
    if member.nick:
      ring.insert(1, f"Никнейм на сервере: {member.nick}")
    if member.premium_since:
      ring.append(f"Бустит сервер с <t:{int(member.premium_since.timestamp())}>")
    ring.append(f"Роли ({len(member.roles)}): {', '.join(list(reversed([role.mention if role != interaction.guild.default_role else '@everyone' for role in member.roles])))}")
  if member.public_flags:
    flags = []
    if member.public_flags.bot_http_interactions:
      flags.append('Бот со слэш командами')
    if member.public_flags.active_developer:
      flags.append("`Активный разработчик`")
    if member.public_flags.bug_hunter:
      flags.append("`БагХантер`")
    if member.public_flags.bug_hunter_level_2:
      flags.append("`БагХантер 2 уровня`")
    if member.public_flags.discord_certified_moderator:
      flags.append("`Сертифицированный модератор Discord`")
    if member.public_flags.early_supporter:
      flags.append("`Раннеподдержавший (купил Discord Nitro в ранний период Discord)`")
    if member.public_flags.early_verified_bot_developer:
      flags.append("`Ранний разработчик верифицированного бота (верифицировал бота в ранний период Discord)`")
    if member.public_flags.hypesquad:
      flags.append("`HypeSquad Events;")
    if member.public_flags.hypesquad_balance:
      flags.append("`HypeSquad Balance`")
    if member.public_flags.hypesquad_bravery:
      flags.append("`HypeSquad Bravery`")
    if member.public_flags.hypesquad_brilliance:
      flags.append("`HypeSquad Brilliance`")
    if member.public_flags.partner:
      flags.append("`Партнёр Discord`")
    if member.public_flags.spammer:
      flags.append("`Спаммер`")
    if member.public_flags.staff:
      flags.append("`Персонал Discord`")
    if member.public_flags.system:
      flags.append("`Система (сам Discord)`")
    if member.public_flags.team_user:
      flags.append("`Участник команды`")
    if member.public_flags.verified_bot:
      flags.append("`Верифицированный бот`")
    if member.public_flags.verified_bot_developer:
      flags.append("`Разработчик верифицированного бота`")
    ring.append(f"Значки ({len(flags)}): {', '.join(flags)}")
  await interaction.response.send_message(embed=discord.Embed(title=f"Информация о {member}", description="\n".join(ring), color=member.accent_color or member.color).set_thumbnail(url=member.display_avatar.url).set_footer(text=f"ID: {member.id}"))

giveaways_dict = {}

giveaways_group = app_commands.Group(name="розыгрыши", description="Управление розыгрышами", guild_only=True, default_permissions=discord.Permissions(manage_guild=True))

@giveaways_group.command(name="создать", description="Создаёт розыгрыш")
@app_commands.describe(duration="Укажите длительность розыгрыша", prize="Укажите приз", winners="Укажите количество победителей")
async def giveaway_create(interaction: Interaction, duration: Transform[str, Duration], prize: app_commands.Range[str, None, 500], winners: app_commands.Range[int, 1, 50]):
  perms = interaction.channel.permissions_for(interaction.guild.me)
  if not (perms.read_messages and perms.send_messages and perms.embed_links and perms.read_message_history and perms.manage_messages):
    return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Бот не имеет одно, или несколько прав для выполнения команды! Предоставьте ему следующие права в этом канале: `Просмотр канала`, `Отправлять сообщения`, `Читать историю сообщений` и `Управлять сообщениями` для выполнения команды!", color=0xff0000), ephemeral=True)
  if duration > timedelta(days=365) or duration < timedelta(seconds=10):
    return await interaction.response.send_message(embed=discord.Embed(title="❌ Ошибка!", color=0xff0000, description="Вы указали длительность, которая больше, чем 1 год, либо меньше, чем 10 секунд!"), ephemeral=True)
  duration = datetime.now(timezone.utc) + duration
  await interaction.response.send_message(embed=discord.Embed(title="🎉 Розыгрыш!", description=f"**Для участия нажимайте на 🎉**\nПриз: {prize}\nПобедителей: {winners}\nЗакончится: <t:{int(duration.timestamp())}:R> (<t:{int(duration.timestamp())}:D>)", color=0x69FF00, timestamp=duration))
  interaction.message = await interaction.original_response()
  await interaction.message.add_reaction('🎉')
  cur.execute("INSERT INTO giveaways (channel_id, guild_id, message_id, duration, prize, winners) VALUES (%s, %s, %s, %s, %s, %s);", (interaction.channel.id, interaction.guild.id, interaction.message.id, str(int(duration.timestamp())), prize, str(winners)))
  con.commit()

@giveaways_group.command(name="закончить", description="Оканчивает розыгрыш раньше времени")
@app_commands.describe(giveaway="Введите приз розыгрыша, или ID его сообщения")
async def giveaway_end(interaction: Interaction, giveaway: str):
  cur.execute("SELECT * FROM giveaways WHERE message_id = %s;", (giveaway,))
  giveaway = cur.fetchone()
  givchan = await bot.fetch_channel(giveaway[0])
  perms = givchan.permissions_for(interaction.guild.me)
  if not (perms.read_messages and perms.send_messages and perms.embed_links and perms.read_message_history and perms.manage_messages):
    return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Бот не имеет одно, или несколько прав для выполнения команды! Предоставьте ему следующие права в канале розыгрыша: `Просмотр канала`, `Отправлять сообщения`, `Читать историю сообщений` и `Управлять сообщениями` для выполнения команды!", color=0xff0000), ephemeral=True)
  else:
    await interaction.response.send_message(embed=discord.Embed(title="✅ Успешно", description="Указанный розыгрыш был окончен!", color=0x69FF00), ephemeral=True)
  givmes = await givchan.fetch_message(giveaway[2])
  reaction = [reaction for reaction in givmes.reactions if reaction.emoji == '🎉'][0]
  givuch = [user async for user in reaction.users() if isinstance(user, Member) and not user.bot]
  givpob = []
  if len(givuch) >= int(giveaway[5]):
    for i in range(int(giveaway[5])):
      sdel = False
      while not sdel:
        predv = random.choice(givuch)
        if predv not in givpob:
          givpob.append(predv)
          sdel = True
    givpob_str = '\n'.join([f'{pob} ({pob.mention})' for pob in givpob])
    givpob_ment = ', '.join([pob.mention for pob in givpob])
  await givmes.clear_reaction('🎉')
  if givpob:
    await givmes.edit(embed=discord.Embed(title="🎉 Розыгрыш!", description=f"**Розыгрыш окончен!**\nПриз: {giveaway[4]}\nУчастников розыгрыша: {len(givuch)}\nПобедители ({len(givpob)}):\n{givpob_str}", color=0x69FF00, timestamp=datetime.now(timezone.utc)))
    await givmes.reply(content=f"{givpob_ment}\nПоздравляю вас с победой и получением приза **{giveaway[4]}**!")
  else:
    await givmes.edit(embed=discord.Embed(title="🎉 Розыгрыш!", description=f"**Розыгрыш окончен!**\nПриз: {giveaway[4]}\nПобедителей нет", color=0x69FF00, timestamp=datetime.now(timezone.utc)))
    await givmes.reply(embed=discord.Embed(description=f"Победителей не удалось установить, так как участников розыгрыша ({len(givuch)}) меньше, чем установленных победителей ({len(givpob)}).", title="Ошибка! ❌", color=0xff0000))
  if givpob:
    cur.execute("INSERT INTO ended_giveaways (channel_id, guild_id, message_id, ended_at, prize, winners, members) VALUES (%s, %s, %s, %s, %s, %s, %s);", (giveaway[0], giveaway[1], giveaway[2], str(int(datetime.now(timezone.utc).timestamp())), giveaway[4], giveaway[5], " ".join([str(user.id) for user in givuch])))
  cur.execute("DELETE FROM giveaways WHERE message_id = %s;", (giveaway[2],))
  con.commit()

@giveaway_end.autocomplete('giveaway')
async def giveaway_end_search(interaction: Interaction, current: str):
  cur.execute("SELECT * FROM giveaways WHERE guild_id = %s;", (str(interaction.guild.id),))
  results = cur.fetchall()
  if current:
    return [Choice(name=f"Приз: {giveaway[4]} (ID сообщения: {giveaway[2]})", value=giveaway[2]) for giveaway in results if giveaway[2].startswith(current) or giveaway[4].startswith(current)]
  else:
    return [Choice(name=f"Приз: {giveaway[4]} (ID сообщения: {giveaway[2]})", value=giveaway[2]) for giveaway in results]

@giveaway_end.error
async def giveaway_end_error(interaction, error):
  error = getattr(error, 'original', error)
  if isinstance(error, TypeError):
    await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description=f"Вы не выбрали розыгрыш для его окончания!", color=0xff0000), ephemeral=True)

@giveaways_group.command(name="удалить", description="Удаляет розыгрыш")
@app_commands.describe(giveaway="Введите приз розыгрыша, или ID его сообщения")
async def giveaway_delete(interaction: Interaction, giveaway: str):
  cur.execute("SELECT channel_id FROM giveaways WHERE message_id = %s;", (giveaway,))
  givchan = await bot.fetch_channel(cur.fetchone()[0])
  perms = givchan.permissions_for(interaction.guild.me)
  if not (perms.read_messages and perms.send_messages and perms.embed_links and perms.read_message_history and perms.manage_messages):
    return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="Бот не имеет одно, или несколько прав для выполнения команды! Предоставьте ему следующие права в канале розыгрыша: `Просмотр канала`, `Отправлять сообщения`, `Читать историю сообщений` и `Управлять сообщениями` для выполнения команды!", color=0xff0000), ephemeral=True)
  else:
    await interaction.response.send_message(embed=discord.Embed(title="✅ Успешно", description="Указанный розыгрыш был удалён!", color=0x69FF00), ephemeral=True)
  givmes = await givchan.fetch_message(giveaway)
  await givmes.delete()
  cur.execute("DELETE FROM giveaways WHERE message_id = %s;", (giveaway[2],))
  con.commit()

@giveaway_delete.autocomplete('giveaway')
async def giveaway_delete_search(interaction: Interaction, current: str):
  cur.execute("SELECT * FROM giveaways WHERE guild_id = %s;", (str(interaction.guild.id),))
  results = cur.fetchall()
  if current:
    return [Choice(name=f"Приз: {giveaway[4]} (ID сообщения: {giveaway[2]})", value=giveaway[2]) for giveaway in results if giveaway[2].startswith(current) or giveaway[4].startswith(current)]
  else:
    return [Choice(name=f"Приз: {giveaway[4]} (ID сообщения: {giveaway[2]})", value=giveaway[2]) for giveaway in results]

@giveaway_delete.error
async def giveaway_delete_error(interaction, error):
  error = getattr(error, 'original', error)
  if isinstance(error, TypeError):
    await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description=f"Вы не выбрали розыгрыш для его удаления!", color=0xff0000), ephemeral=True)

@giveaways_group.command(name="список", description="Показывает список розыгрышей")
async def giveaway_list(interaction: Interaction):
  cur.execute("SELECT * FROM giveaways WHERE guild_id = %s;", (str(interaction.guild.id),))
  results = cur.fetchall()
  if not results:
    return await interaction.response.send_message(embed=discord.Embed(title="Ошибка! ❌", description="На сервере нет активных розыгрышей!", color=0xff0000), ephemeral=True)
  await interaction.response.send_message(embed=discord.Embed(title="Список розыгрышей", color=0x69FF00, description="\n\n".join([f'Розыгрыш с призом **{giveaway[4]}** и ID сообщения [{giveaway[2]}](https://discord.com/channels/{giveaway[1]}/{giveaway[0]}/{giveaway[2]})' for giveaway in results])))

@bot.tree.command(name="токен", description="Показывает начало токена участника")
@app_commands.describe(member='Выберите участника')
async def token_cmd(interaction: Interaction, member: typing.Union[Member, User]=None):
  if not member:
    member = interaction.user
  await interaction.response.send_message(content=member.mention, embed=discord.Embed(color=0xff0000, description=f"Начало токена {member.mention}: `{base64.b64encode(str(member.id).encode('ascii')).decode('ascii').replace('=', '')}.`"))

bot.tree.add_command(giveaways_group)
bot.tree.add_command(spam_group)

if __name__ == '__main__':
  discord.gateway.DiscordWebSocket.identify = mobile
  discord.utils.setup_logging(handler=DiscordHandler(service_name="Логи Крутяка", webhook_url=os.environ['WEBHOOK_URL'], avatar_url=f'https://cdn.discordapp.com/avatars/1136693304826806342/43689bd9e44328e1b98b9be9a2e55c65.png'), formatter=logging.Formatter("%(message)s"))
  bot.run(os.environ['TOKEN'], log_level=logging.DEBUG)
