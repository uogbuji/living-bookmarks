# living-bookmarks
Uses OgbujiPT (language AI toolkit) to Help a user manage their bookmarks in context of various chat, etc.

# Setting up

Prerequisites:

* An account on Raindrop
* An integration app you've set up on the Raindrop site, and its API token
* llama.cpp server running an LLM model

## Raindrop setup

Go to the [integrations](https://app.draindrop.api/settings/integrations) page & select or create an app

Do Create test token and copy the token provided, which will only give you access to bookmarks within your own account. Save this token into your environment or password manager. You can specify the `living_bookmarks` token on the command line (`--raindrop-key`) or environment (`LIVING_BOOKMARKS_RAINDROP_KEY`)

## Discord setup

You need a discord app (bot) set up. [The discord.py docs](https://discordpy.readthedocs.io/en/stable/discord.html) has a useful primer on this. Save the token to your password manager.

You can specify the token on the command line (`--discord-token`) or environment (`LIVING_BOOKMARKS_DISCORD_TOKEN`)

