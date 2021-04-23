import discord
import nacl
import os
import asyncio
import youtube_dl

from discord.ext import commands
from waiting import wait

# Command Aliases
squidwardDaBabyAlias = ["squidbaby", "squidwardbaby", "dababy"]

# Sound urls
squidwardDaBabyURL = "https://youtu.be/fzhDGZD44hE"


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}


ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Joins a voice channel
	@commands.command()
	async def join(self, ctx, *, channel: discord.VoiceChannel):
		if ctx.voice_client is not None:
			return await ctx.voice_client.move_to(channel)

		await channel.connect()

	# Plays a file from the local filesystem
	@commands.command()
	async def play(self, ctx, *, query):
		source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
		ctx.voice_client.play(source, after=lambda e: print('Player error: %s' %e) if e else None)

		await ctx.send('Now playing: {}'.format(query))

	# Change player volume
	@commands.command()
	async def volume(self, ctx, volume: int):
		if ctx.voice_client is None:
			return await ctx.send("You're not in a voice channel, puhi")

		ctx.voice_cleint.source.volume = volume / 100
		await ctx.send("Changed volume to {}%".format(volume))

	# Streams from a url
	@commands.command()
	async def stream(self, ctx, *, url):
		async with ctx.typing():
			player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
			ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)


	# Stops and disconnects the bot from voice
	@commands.command()
	async def stop(self, ctx):

		await ctx.voice_client.disconnect()

	@commands.command(aliases=squidwardDaBabyAlias)
	async def squidwardDaBaby(self, ctx):
		await ctx.invoke(self.bot.get_command('stream'), url = squidwardDaBabyURL)
		while(ctx.voice_client.is_playing()):
			await asyncio.sleep(1)
		await ctx.voice_client.disconnect()

	@play.before_invoke
	@stream.before_invoke
	@squidwardDaBaby.before_invoke
	async def ensure_voice(self, ctx):
		if ctx.voice_client is None:
			if ctx.author.voice:
				await ctx.author.voice.channel.connect()
			else:
				await ctx.send("You're not in a voice channel, puhi")
				raise commands.CommandError("Author not connected to a voice channel.")
		elif ctx.voice_client.is_playing():
			await ctx.send("I'm already playing something, puhi")






bot = commands.Bot(command_prefix = commands.when_mentioned_or("~"), description = 'Plays cool sounds, puhi', case_insensitive=True)


@bot.event
async def on_ready():
	print('Logged in as {0} ({0.id})'.format(bot.user))
	print('-------')

bot.add_cog(Music(bot))
bot.run(os.getenv('botkey'))