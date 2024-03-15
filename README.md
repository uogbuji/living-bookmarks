# living-bookmarks
Uses [OgbujiPT (language AI toolkit)](https://github.com/OoriData/OgbujiPT) to Help a user manage their bookmarks in context of various chat, etc.

# Setting up

Prerequisites:

* Account on Raindrop
* Integration app you've set up on the Raindrop site, and its API token
* Discord app and token
* PGVector instance running
* llama.cpp server running an LLM model

## Raindrop setup

Go to the [integrations](https://app.draindrop.api/settings/integrations) page & select or create an app

Do Create test token and copy the token provided, which will only give you access to bookmarks within your own account. Save this token into your environment or password manager. You can specify the `living_bookmarks` token on the command line (`--raindrop-key`) or environment (`LIVING_BOOKMARKS_RAINDROP_KEY`)

## Discord setup

You need a discord app (bot) set up. [The discord.py docs](https://discordpy.readthedocs.io/en/stable/discord.html) has a useful primer on this. Save the token to your password manager.

You can specify the token on the command line (`--discord-token`) or environment (`LIVING_BOOKMARKS_DISCORD_TOKEN`)

## PGVector setup

This is easiest with Docker. You can just do:

```bash
# Replace the following with your preferred shell's way of updating environment
export $DB_HOST="localhost"
export $DB_PORT="5432"
export $DB_USER="me"
export $DB_PASSWORD="my_secret_secret"
export $DB_NAME="my_embeddings"

docker pull ankane/pgvector
docker run --name mydb -p 5432:5432 \
    -e POSTGRES_USER=$DB_USER -e POSTGRES_PASSWORD=$DB_PASSWORD -e POSTGRES_DB=$DB_NAME \
    -d ankane/pgvector
```

Make sure you don't have anything running on port 5432, or update the port in the environment and in the command.

## llama.cpp setup

For now you probably have to [download, build and run the llama.cpp server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md)

TODO: Hosted Docker image for llama.cpp running [Phi-2-super GGUF](https://huggingface.co/MaziyarPanahi/phi-2-super-GGUF)
