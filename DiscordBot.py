import requests
import os

import discord
from discord.ext import commands

# Chargement de la configuration depuis fichier ini
from configparser import ConfigParser

config = ConfigParser()

# Charger le fichier de configuration
config.read("config.ini")

# Modèle LLaMA à utiliser
LLAMA_MODEL = config.get("ai", "model")

DEFAULT_SERVER = "https://api.openai.com"
COMPLETIONS_ENDPOINT="/v1/chat/completions"

DISCORD_TOKEN = config.get("discord", "token")

# Loading prompt from file
def load_prompt_from_file(file_path):
    with open(file_path, "r") as file:
        prompt = file.read()
    return prompt

# Charge le fichier "prompt.cfg" et l'uilise comme prompt avec le role "system"
prompt = load_prompt_from_file(config.get("ai", "prompt_file"))

context_messages = [
    {"role": "system", "content": prompt},
]

if config.has_option("ai", "base_url"):
    AI_SERVICE_URL = config.get("ai", "base_url") + COMPLETIONS_ENDPOINT
else:
    AI_SERVICE_URL = DEFAULT_SERVER + COMPLETIONS_ENDPOINT
    

# Clé API (ou toute clé d'autorisation nécessaire)
API_KEY = config.get("ai","api_key")

# En-têtes de la requête
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Données de la requête
data = {
    "messages": context_messages,
    "temperature": 0.7
}

# Fonction pour envoyer une question au serveur et renvoyer la réponse
def ask_question(question):
    # Mettre la question dans le contexte
    context_messages.append({"role": "user", "content": question})
    data["messages"] = context_messages
    # Affiche la question dans la console
    print(f"Question: {question}")

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


# Créer un objet Intents et activer les intents nécessaires
intents = discord.Intents.default()
intents.message_content = True  # Activer l'intent de contenu de message
intents.presences = True  # Activer l'intent de présence, si nécessaire
intents.members = True  # Activer l'intent des membres

# Le bot réponds au mention de son nom
bot = commands.Bot(command_prefix='!', intents=intents)

# Événement on_ready
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

# Commande simple 'ping'
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# Sur un message reçu
@bot.event
async def on_message(message):
    # Ignorer les messages de soi-même
    if message.author == bot.user:
        return

    # Ignorer les messages sans mention
    if bot.user.mentioned_in(message):
        # Obtenir le contenu du message
        question = message.content

        # Envoyer la question au modèle LLaMA
        answer = ask_question(question)

        # Envoyer la réponse
        await message.channel.send(answer)

    # Continuer le traitement des commandes
    await bot.process_commands(message)

# Lancer le bot
bot.run(DISCORD_TOKEN)
