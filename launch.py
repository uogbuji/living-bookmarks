'''
Main launcher for Discord bot. Uses OgbujiPT (language AI toolkit) to Help a user manage their bookmarks in context of various chat, etc.

Reference:

* Discord cogs: https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html
* Raindrop API: https://raindrop-io-py.readthedocs.io/en/latest/raindropiopy.models.html

'''

import os
import asyncio
import tomllib

import discord
from discord.ext import commands
import click
from raindropiopy import API, Collection, CollectionRef, Raindrop
from sentence_transformers import SentenceTransformer

from ogbujipt.llm_wrapper import llama_cpp_http_chat
from ogbujipt.embedding.pgvector import DataDB  # , MessageDB


class living_bookmarks(commands.Cog):
    def __init__(self, bot, config, db_connect):
        self.bot = bot
        self.config = config
        self.db_connect = db_connect
        self.embedding_model = SentenceTransformer(self.config['vectordb']['embedding_model'])

    async def setup(self):
        '''
        Initialize vector DB from Raindrop.io & launch LLM
        '''
        print(f'Initializing LLM {self.config["llm_endpoint"]["label"]}')
        self.llm = llama_cpp_http_chat(base_url=self.config['llm_endpoint']['base_url'])
        self.vdb = await DataDB.from_conn_params(table_name=self.config['vectordb']['bookmarks_table_name'], embedding_model=self.embedding_model, **self.db_connect)
        await self.vdb.create_table()
        self.sysmsg = self.config['llm_endpoint']['sysmsg']
        self.sys_postscript = self.config['llm_endpoint']['sys_postscript']
        self.model_params = self.config['model_params']
        with API(os.environ['RAINDROP_TOKEN']) as api:
            for collection in Collection.get_collections(api):
                # print(f'Collection: {collection.title}')
                # print(dir(collection))

                # Unsorted Raindrop Bookmarks
                for item in Raindrop.search(api, collection=collection):
                    print(f'Item: {item.title}')
                    # print(dir(item))
                    content = f'[{item.title}]({item.link})\n{item.excerpt}\nCollection: {collection.title}\n### Tags\n{"  * ".join(item.tags)}\n'
                    print(content)
                    await self.vdb.insert(content, [f'url={item.link}'])

            # Unsorted Raindrop Bookmarks
            for item in Raindrop.search(api, collection=CollectionRef.Unsorted):
                print(f'Unsorted item: {item.title}')
                # print(dir(item))
                content = f'[{item.title}]({item.link})\n{item.excerpt}\nCollection: Unsorted\n### Tags\n{"  * ".join(item.tags)}\n\n'

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:  # Ignore the bot's own messages
            return

        if message.author.bot:  # Ignore messages from bots
            return

        # Respond only to @mentions. client.user.id check screens out @everyone & @here pings
        # FIXME: Better content check—what if the bot's id is a common word?
        # if not self.bot.user.mentioned_in(message) and str(self.bot.user.id) not in message.content:
        #     return

        if message.guild:
            # XXX: In future, update chat context?
            pass
        else:  # Message is a DM
            # await message.channel.send(f"Hey {message.author.mention}, thanks for your message! I can only respond to commands in servers.")

            # Send throbber placeholder message to discord:
            return_msg = await message.channel.send('<a:oori_throbber:1142173241499197520>')

            nneighbors = await self.vdb.search(message.content, limit=5)
            print(nneighbors)
            nn_context = '[CONTEXT]\n' + '\n'.join([f'{i+1}. {n["content"]}' for i, n in enumerate(nneighbors)]) + '\n[END CONTEXT]'
            messages = [
                {'role': 'system', 'content': self.sysmsg},
                {'role': 'system', 'content': nn_context},
                {'role': 'system', 'content': self.sys_postscript},
                {'role': 'user', 'content': message.content},
                ]
            response = await self.send_llm_msg(messages)

            await return_msg.edit(content=response[:2000])  # Discord messages cap at 2k characters

    @commands.Cog.listener()
    async def on_ready(self):
        await self.setup()
        print(f"Bot is ready. Connected to {len(self.bot.guilds)} guild(s).")

    async def send_llm_msg(self, messages):
        '''
        Schedule the LLM request
        '''
        print('\nSending messages to LLM:\n', messages)
        print(self.model_params)
        response = await self.llm(messages, **self.model_params)
        print(response)

        # print('\nFull response data from LLM:\n', response)

        response_text = response.first_choice_text
        print('\nResponse text from LLM:\n', response_text)

        return response_text


def load_config(ctx, param, value):  # noqa: ARG001
    '''
    Callback for processing --config option

    Note: Only process raw data here. No e.g. constructing/manipulating objects based on that data
    '''
    if not value:
        return None
    with open(value, 'rb') as fp:
        config = tomllib.load(fp)

    assert 'model_params' in config, 'Config missing required table (section) model_params'
    assert 'vectordb' in config, 'Config missing required table (section) vectordb'
    config['vectordb'].setdefault('bookmarks_table_name', 'bookmarks')
    assert 'llm_endpoint' in config, 'Config missing required table (section) llm_endpoint'
    config['llm_endpoint'].setdefault('class', 'llama_cpp_http_chat')
    config['llm_endpoint'].setdefault('label', '[UNLABELED]')
    assert config['llm_endpoint'].get('class') == 'llama_cpp_http_chat', 'Only class supported for now is ' 'llama_cpp_http_chat'
    return config


@click.command()
@click.option('--raindrop-key', required=True, help='raindrop.io API key')
@click.option('--discord-token', required=True, help='Discord app token')
@click.option('--config', '-c', required=True, type=click.Path(dir_okay=False), callback=load_config,
              help='TOML Config file')
def cli(raindrop_key, discord_token, config):
    # Set up LLM wrapper
    os.environ["RAINDROP_TOKEN"] = raindrop_key  # Required by raindrop-io-py
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_USER = os.getenv('DB_USER', 'oori')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'example')
    DB_NAME = os.getenv('DB_NAME', 'PGv')

    db_connect = {'user': DB_USER, 'password': DB_PASSWORD, 'db_name': DB_NAME,
                'host': DB_HOST, 'port': DB_PORT}

    # Set up bot https://discord.com/developers/docs/topics/gateway#list-of-intents
    # Will also need to enable message content intent on the bot app's dashboard (Bot tab)
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix=['/'], intents=intents, description='Oori Chat Bot Framework')

    lb = living_bookmarks(bot, config, db_connect)
    asyncio.run(bot.add_cog(lb))
    # launch Discord client event loop
    bot.run(discord_token)


if __name__ == '__main__':
    cli(auto_envvar_prefix='LIVING_BOOKMARKS')
