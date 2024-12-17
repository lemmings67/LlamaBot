import requests
import os

import discord
from discord.ext import commands

from configparser import ConfigParser

config = ConfigParser()

# Loading configuration from file
config.read("config.ini")

LLAMA_MODEL = config.get("ai", "model")

DEFAULT_SERVER = "https://api.openai.com"
COMPLETIONS_ENDPOINT="/v1/chat/completions"

DISCORD_TOKEN = config.get("discord", "token")

# Loading prompt file
def load_prompt_from_file(file_path):
    with open(file_path, "r") as file:
        prompt = file.read()
    return prompt

# Setting up the prompt 
prompt = load_prompt_from_file(config.get("ai", "prompt_file"))
context_messages = [
    {"role": "system", "content": prompt},
]

# Setting up the AI service URL
if config.has_option("ai", "base_url"):
    AI_SERVICE_URL = config.get("ai", "base_url") + COMPLETIONS_ENDPOINT
else:
    AI_SERVICE_URL = DEFAULT_SERVER + COMPLETIONS_ENDPOINT
    
# Getting the API KEY
API_KEY = config.get("ai","api_key")

# Request headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Prepare the data to send to the AI service
data = {
    "messages": context_messages,
    "temperature": 0.7
}

# Send a question to the AI model
async def ask_question(question):
    # Mettre la question dans le contexte
    context_messages.append({"role": "user", "content": question})
    data["messages"] = context_messages
    # Affiche la question dans la console
    print(f"Question: {question}")

    # Ajout d'une gestion des erreurs
    try:
        # Envoyer la requête POST
        response = requests.post(AI_SERVICE_URL, json=data, headers=headers)

        # Vérifier le statut de la réponse et afficher le contenu
        if response.status_code == 200:
            # Affiche la réponse dans la console
            print(f"Réponse: {response.json()['choices'][0]['message']['content']}")
            response_message = response.json()["choices"][0]["message"]["content"]
            return response_message
        else:
            return f"Request failed with status code {response.status_code}: {response.text}"
    except Exception as e:
        return f"An error occurred: {e}"

# Bot prefix and intents
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# On ready event to print the bot name
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

# Ping test commande
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# On message event to handle the messages
@bot.event
async def on_message(message):
    # Ignore own messages
    if message.author == bot.user:
        return

    # Ignore messages without mentions
    if bot.user.mentioned_in(message):
        # Getting message content
        question = message.content

        # Sending the question to the AI model
        answer = await ask_question(question)

        # Sending the answer back to the user
        await message.channel.send(answer)

    # Continue processing commands
    await bot.process_commands(message)

# Starting the bot
bot.run(DISCORD_TOKEN)
