# Bot configuration
TELEGRAM_BOT_TOKEN = "7943385629:AAGjnTp-3oBj_yW-Xze_EpR693Y2ZdPdC6s"
ADMIN_ID = 7151308102
FREE_SIGNAL_LIMIT = 2
PREMIUM_DAILY_LIMIT = 10

# API Configuration
ALPHA_VANTAGE_API_KEYS = {
    "free": "GUZYT7XQMZCNHBNH",
    "premium": "QUFLIODYF08MMRKO"
}

FOREX_PAIRS = [
    "EUR/USD",
    "GBP/USD", 
    "USD/JPY",
    "USD/CHF",
    "AUD/USD",
    "EUR/GBP",
    "EUR/JPY"
]
SIGNAL_STRENGTH_THRESHOLD = 0.75

# Cache Configuration
CACHE_DURATION = 300  # 5 minutes in seconds
CACHE_DURATION_MESSAGE = "📊 Sinjalet përditësohen çdo 5 minuta"

# Message templates
WELCOME_MESSAGE = """
🤖 Mirë se vini në Forex Signals Bot!
Përdoruesit falas kanë akses në vetëm 2 sinjale gjithsej
Përdoruesit premium kanë akses në 10 sinjale në ditë

Shtypni butonat më poshtë për të përdorur komandat:
"""

HELP_MESSAGE = """
📈 Sinjalet e forex janë të sigurta! 

🔄 Sinjalet përditësohen automatikisht çdo 5 minuta

🔒 Ju lutemi blini premium për të pasur akses tek 📊 Manual Signal.

💪 Ky bot është krijuar nga profesionistët në kodim në Python dhe është i lidhur direkt me API të forex. Të gjitha sinjalet rekomandohen nga API - 100% të sigurta!

💎 Kliko butonin Buy License 🔐 për të blerë licencën.

⚡️ Përdoruesit premium kanë:
✨ Limit 10 sinjale për 24 orë
✨ Sinjale të personalizuara
✨ Rekomandime të sakta

💰 Ju rekomandojmë që pas blerjes së licencës të bëni trade në forex me shuma të konsiderueshme parash, pasi sinjalet tona janë tejet të besueshme!

Komandat kryesore:
🔹 /start - Fillo bot-in
🔹 /help - Shfaq këtë mesazh ndihme
🔹 /status - Kontrollo përdorimin e sinjaleve
🔹 /manualsignal - Merr sinjal manual (vetëm premium)
🔹 /activatelicense - Aktivizo licencën premium
"""

LIMIT_REACHED_MESSAGE = """
⚠️ Keni arritur limitin tuaj prej 2 sinjalesh!
💎 Bëhuni premium për të marrë deri në 10 sinjale në ditë.
"""

ADMIN_HELP = """
Sinjalet e forex jan te sigurta ju lutemi bleni premiumin per te pas akses tek 📊 Manual Signal ky bot eshte krijuar nga profesionalistat ne kodim ne python dhe boti ka akses ne forex i lidhur me api dhe te gjitha signalet rekomandohen nga api kliko butonin Buy License 🔐 per ta bler licencen 100 % secure ju rekomandojm pas blerjes te beni trade ne forex me shuma te konsiderushme parash sepse premium users kan limit 10 signal per 24 H
"""

SIGNAL_STRENGTH_MESSAGES = {
    "STRONG_BUY": "🟢 SINJAL I FORTË BLERJEJE",
    "STRONG_SELL": "🔴 SINJAL I FORTË SHITJEJE",
    "MODERATE_BUY": "🟡 SINJAL MESATAR BLERJEJE",
    "MODERATE_SELL": "🟡 SINJAL MESATAR SHITJEJE",
    "NEUTRAL": "⚪ NEUTRAL - Pa sinjal të qartë"
}