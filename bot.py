import json
import os
import random
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

LIMITE_DIARIO = 3
PONTOS_ACERTO = 10
PONTOS_ERRO = -5
ARQUIVO = "dados.json"

IMAGEM_MOEDA = "https://i.imgur.com/YnrL6Ee.png"


def carregar_dados():
    try:
        with open(ARQUIVO, "r") as f:
            return json.load(f)
    except:
        return {}


def salvar_dados(dados):
    with open(ARQUIVO, "w") as f:
        json.dump(dados, f)


def resetar_diario(dados, chat_id):
    hoje = str(date.today())
    if dados[chat_id]["data"] != hoje:
        dados[chat_id]["data"] = hoje
        dados[chat_id]["usuarios"] = {}


async def jogar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)

    dados = carregar_dados()

    if chat_id not in dados:
        dados[chat_id] = {
            "data": str(date.today()),
            "usuarios": {}
        }

    resetar_diario(dados, chat_id)

    usuario = dados[chat_id]["usuarios"].get(
        user_id, {"jogadas": 0, "pontos": 0}
    )

    if usuario["jogadas"] >= LIMITE_DIARIO:
        await update.message.reply_text("❌ Você atingiu o limite diário de jogadas!")
        return

    dados[chat_id]["usuarios"][user_id] = usuario
    salvar_dados(dados)

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🪙 CARA", callback_data="cara"),
            InlineKeyboardButton("🪙 COROA", callback_data="coroa")
        ]
    ])

    await update.message.reply_photo(
        photo=IMAGEM_MOEDA,
        caption="Escolha **Cara** ou **Coroa**",
        reply_markup=teclado,
        parse_mode="Markdown"
    )


async def escolher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = str(query.message.chat.id)
    user_id = str(query.from_user.id)
    escolha = query.data

    dados = carregar_dados()
    resetar_diario(dados, chat_id)

    usuario = dados[chat_id]["usuarios"][user_id]

    resultado = random.choice(["cara", "coroa"])
    usuario["jogadas"] += 1

    if escolha == resultado:
        usuario["pontos"] += PONTOS_ACERTO
        texto = f"✅ Deu **{resultado.upper()}**!\n+{PONTOS_ACERTO} pontos"
    else:
        usuario["pontos"] += PONTOS_ERRO
        texto = f"❌ Deu **{resultado.upper()}**!\n{PONTOS_ERRO} pontos"

    dados[chat_id]["usuarios"][user_id] = usuario
    salvar_dados(dados)

    await query.edit_message_caption(caption=texto, parse_mode="Markdown")


async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    dados = carregar_dados()

    if chat_id not in dados:
        await update.message.reply_text("Ainda não há ranking hoje.")
        return

    resetar_diario(dados, chat_id)

    usuarios = dados[chat_id]["usuarios"]
    if not usuarios:
        await update.message.reply_text("Ainda não há ranking hoje.")
        return

    ranking_ordenado = sorted(
        usuarios.items(),
        key=lambda x: x[1]["pontos"],
        reverse=True
    )

    texto = "🏆 **Ranking Diário**\n\n"
    for i, (_, info) in enumerate(ranking_ordenado[:10], start=1):
        texto += f"{i}️⃣ {info['pontos']} pontos\n"

    await update.message.reply_text(texto, parse_mode="Markdown")


app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("jogar", jogar))
app.add_handler(CommandHandler("ranking", ranking))
app.add_handler(CallbackQueryHandler(escolher))
app.run_polling()
