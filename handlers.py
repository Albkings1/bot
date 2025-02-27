from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
import config
from database import Database
from forex import get_forex_data, format_signal_message
import random
import string
import logging
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username

    if not db.get_user(user_id):
        db.create_user(user_id, username)

    keyboard = [
        [KeyboardButton("📊 Manual Signal"), KeyboardButton("📈 Status")],
        [KeyboardButton("❓ Help"), KeyboardButton("Buy License 🔐")],
        [KeyboardButton("💎 Activate License")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(config.WELCOME_MESSAGE, reply_markup=reply_markup)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📊 Manual Signal":
        await manual_signal_command(update, context)
    elif text == "📈 Status":
        await status_command(update, context)
    elif text == "❓ Help":
        await help_command(update, context)
    elif text == "Buy License 🔐":
        keyboard = [
            [InlineKeyboardButton("USDT (Tron)", callback_data="pay_usdt")],
            [InlineKeyboardButton("BTC", callback_data="pay_btc")],
            [InlineKeyboardButton("LTC", callback_data="pay_ltc")],
            [InlineKeyboardButton("ETH", callback_data="pay_eth")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "💎 Zgjidhni metodën e pagesës për licencë premium:",
            reply_markup=reply_markup
        )
    elif text == "💎 Activate License":
        await update.message.reply_text(
            "Për të aktivizuar licencën, përdorni komandën:\n/activatelicense [çelësi_i_licencës]"
        )
    elif text == "🔐 Admin Commands" and update.effective_user.id == config.ADMIN_ID:
        await help_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == config.ADMIN_ID:
        # Admin menu without buttons
        await update.message.reply_text(config.ADMIN_HELP)
    else:
        # Create keyboard with Buy License and Activate License buttons
        keyboard = [
            [KeyboardButton("Buy License 🔐")],
            [KeyboardButton("💎 Activate License")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            config.HELP_MESSAGE,  
            reply_markup=reply_markup
        )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)

    if user:
        status = "Premium ✨" if user["is_premium"] else "Free 🆓"
        signals_used = user["signals_used"]
        daily_signals = user.get("daily_signals", 0)

        message = f"""
📊 Statusi juaj:
👤 Niveli: {status}
📈 Sinjale të përdorura: {signals_used}
"""
        if user["is_premium"]:
            message += f"🔄 Sinjale sot: {daily_signals}/{config.PREMIUM_DAILY_LIMIT}\n"
            message += "✨ Ju keni akses në të gjitha funksionet premium!"
            keyboard = [[InlineKeyboardButton("📊 Merr Sinjal të Ri", callback_data="get_manual_signal")]]
        else:
            remaining = max(0, config.FREE_SIGNAL_LIMIT - signals_used)
            message += f"🔄 Sinjale të mbetura: {remaining}/{config.FREE_SIGNAL_LIMIT}\n"

            if remaining == 0:
                message += "\n" + config.LIMIT_REACHED_MESSAGE
                keyboard = [
                    [InlineKeyboardButton("💎 Blej Premium", callback_data="pay_options")],
                    [InlineKeyboardButton("🔑 Aktivizo Licencë", callback_data="activate_license")]
                ]
            else:
                message += f"\n⚠️ Kujdes: Ju keni vetëm {remaining} sinjale të mbetura falas!"
                keyboard = [
                    [InlineKeyboardButton("📊 Merr Sinjal", callback_data="get_manual_signal")],
                    [InlineKeyboardButton("💎 Blej Premium", callback_data="pay_options")]
                ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)


async def manual_signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Manual signal requested by user {user_id}")

    user = db.get_user(user_id)

    if not user:
        logger.warning(f"User {user_id} not found in database")
        await update.message.reply_text("Ju lutem filloni bot-in së pari me /start")
        return

    if not user["is_premium"]:
        signals_used = user.get("signals_used", 0)
        if signals_used >= config.FREE_SIGNAL_LIMIT:
            logger.info(f"Free user {user_id} reached signal limit")
            keyboard = [
                [InlineKeyboardButton("💎 Blej Premium", callback_data="pay_options")],
                [InlineKeyboardButton("🔑 Aktivizo Licencë", callback_data="activate_license")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                config.LIMIT_REACHED_MESSAGE,
                reply_markup=reply_markup
            )
            return
    else:
        # Check daily signal limit for premium users
        daily_signals = db.get_daily_signals(user_id)
        if daily_signals >= config.PREMIUM_DAILY_LIMIT:
            logger.info(f"Premium user {user_id} reached daily manual signal limit")
            # Calculate time until next reset (midnight)
            now = datetime.now()
            next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if now >= next_reset:
                next_reset = next_reset.replace(day=now.day + 1)

            hours_until_reset = int((next_reset - now).total_seconds() / 3600)
            minutes_until_reset = int(((next_reset - now).total_seconds() % 3600) / 60)

            await update.message.reply_text(
                "🕒 Keni arritur limitin ditor prej 10 sinjalesh.\n"
                f"Ju lutemi prisni edhe {hours_until_reset} orë dhe {minutes_until_reset} minuta "
                "për të marrë sinjale të tjera."
            )
            return

    keyboard = [[InlineKeyboardButton(pair, callback_data=f"signal_{pair}")] for pair in config.FOREX_PAIRS]
    reply_markup = InlineKeyboardMarkup(keyboard)

    daily_signals = db.get_daily_signals(user_id)
    if user["is_premium"]:
        signals_remaining = config.PREMIUM_DAILY_LIMIT - daily_signals
        limit_text = f"(Sinjale të mbetura sot: {signals_remaining}/{config.PREMIUM_DAILY_LIMIT})"
    else:
        signals_remaining = config.FREE_SIGNAL_LIMIT - daily_signals
        limit_text = f"(Sinjale të mbetura falas: {signals_remaining}/{config.FREE_SIGNAL_LIMIT})"

    logger.info(f"Showing forex pair selection to user {user_id}")
    await update.message.reply_text(
        f"📊 Zgjidhni një çift forex për të marrë sinjal:\n{limit_text}",
        reply_markup=reply_markup
    )

async def signal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    logger.info(f"Signal callback received from user {user_id}")

    user = db.get_user(user_id)
    if not user:
        logger.warning(f"User {user_id} not found in database during callback")
        await query.edit_message_text("Ju lutem filloni bot-in së pari me /start")
        return

    if not user["is_premium"]:
        logger.info(f"Non-premium user {user_id} attempted to access manual signals through callback")
        keyboard = [[InlineKeyboardButton("💎 Aktivizo Premium", callback_data="activate_premium")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "⭐️ Sinjalet manuale janë vetëm për përdoruesit premium!\n"
            "Aktivizoni premium për të përdorur këtë funksion.",
            reply_markup=reply_markup
        )
        return

    # Check daily signal limit for premium users
    daily_signals = db.get_daily_signals(user_id)
    if daily_signals >= config.PREMIUM_DAILY_LIMIT:
        logger.info(f"Premium user {user_id} reached daily manual signal limit during callback")
        # Calculate time until next reset (midnight)
        now = datetime.now()
        next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now >= next_reset:
            next_reset = next_reset.replace(day=now.day + 1)

        hours_until_reset = int((next_reset - now).total_seconds() / 3600)
        minutes_until_reset = int(((next_reset - now).total_seconds() % 3600) / 60)

        await query.edit_message_text(
            "🕒 Keni arritur limitin ditor prej 10 sinjalesh.\n"
            f"Ju lutemi prisni edhe {hours_until_reset} orë dhe {minutes_until_reset} minuta "
            "për të marrë sinjale të tjera."
        )
        return

    pair = query.data.replace("signal_", "")
    logger.info(f"Getting forex data for pair {pair}")
    await query.edit_message_text("⏳ Duke marrë sinjalet më të fundit...")

    try:
        # Pass user's premium status to get_forex_data
        signal_data = get_forex_data(pair, is_premium=user["is_premium"])
        if signal_data:
            logger.info(f"Successfully got forex data for pair {pair}")
            message = format_signal_message(signal_data)

            # Add refresh time information
            cache_time = datetime.fromisoformat(signal_data['timestamp'])
            time_since_cache = (datetime.now() - cache_time).total_seconds()
            time_until_refresh = max(0, config.CACHE_DURATION - time_since_cache)
            refresh_msg = f"\n\n🔄 Sinjali përditësohet pas {int(time_until_refresh/60)} minutave dhe {int(time_until_refresh%60)} sekondave"

            message += refresh_msg

            # Update daily signals count
            signals_used = db.add_signal_use(user_id)
            signals_remaining = config.PREMIUM_DAILY_LIMIT - db.get_daily_signals(user_id)
            message += f"\n\n📊 Sinjale të mbetura sot: {signals_remaining}/{config.PREMIUM_DAILY_LIMIT}"

            keyboard = [
                [InlineKeyboardButton("🔄 Përditëso Sinjal", callback_data=f"signal_{pair}")],
                [InlineKeyboardButton("📊 Zgjidh Çift Tjetër", callback_data="get_manual_signal")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=message, reply_markup=reply_markup)
        else:
            logger.error(f"Failed to get forex data for pair {pair}")
            keyboard = [
                [InlineKeyboardButton("🔄 Provo Përsëri", callback_data=f"signal_{pair}")],
                [InlineKeyboardButton("📊 Zgjidh Çift Tjetër", callback_data="get_manual_signal")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Nuk u mor dot sinjali. Ju lutemi provoni përsëri më vonë.",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error in signal_callback for user {user_id}, pair {pair}: {str(e)}")
        keyboard = [
            [InlineKeyboardButton("🔄 Provo Përsëri", callback_data=f"signal_{pair}")],
            [InlineKeyboardButton("📊 Zgjidh Çift Tjetër", callback_data="get_manual_signal")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Ndodhi një gabim. Ju lutemi provoni përsëri.",
            reply_markup=reply_markup
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "pay_options":
        keyboard = [
            [InlineKeyboardButton("USDT (Tron)", callback_data="pay_usdt")],
            [InlineKeyboardButton("BTC", callback_data="pay_btc")],
            [InlineKeyboardButton("LTC", callback_data="pay_ltc")],
            [InlineKeyboardButton("ETH", callback_data="pay_eth")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "💎 Zgjidhni metodën e pagesës për licencë premium:",
            reply_markup=reply_markup
        )
    elif query.data == "activate_license":
        await query.edit_message_text(
            "Për të aktivizuar licencën, përdorni komandën:\n/activatelicense [çelësi_i_licencës]"
        )
    elif query.data.startswith("pay_"):
        payment_method = query.data.replace("pay_", "")
        message = ""
        address = ""

        if payment_method == "usdt":
            message = "🔹 Për të aktivizuar licencën premium, dërgo 29.99 USDT (Tron) në adresën:"
            address = "TLAsrC4uq2TvAzcQKBvJoiKNC2cJmPQ5FM"
        elif payment_method == "btc":
            message = "🔹 Për të aktivizuar licencën premium, dërgo 0.00030 BTC në adresën:"
            address = "bc1qmj9d6cs9n56ngr50wlupv4kaytk7dj0xwx0zxa"
        elif payment_method == "ltc":
            message = "🔹 Për të aktivizuar licencën premium, dërgo 0.22 LTC në adresën:"
            address = "ltc1q8zaxzsyz72ug7r0twacqzqsl6jpksts3ykcjd5"
        elif payment_method == "eth":
            message = "🔹 Për të aktivizuar licencën premium, dërgo 0.011 ETH në adresën:"
            address = "0xf94f082B639E4be0Ebf5Bd9982BbB34A660f544d"

        keyboard = [[InlineKeyboardButton("📋 Kopjo Adresën", callback_data=f"copy_{payment_method}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"{message}\n\n`{address}`\n\nPas pagesës, kontaktoni administratorin për aktivizimin.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif query.data.startswith("copy_"):
        payment_method = query.data.replace("copy_", "")
        addresses = {
            "usdt": "TLAsrC4uq2TvAzcQKBvJoiKNC2cJmPQ5FM",
            "btc": "bc1qmj9d6cs9n56ngr50wlupv4kaytk7dj0xwx0zxa",
            "ltc": "ltc1q8zaxzsyz72ug7r0twacqzqsl6jpksts3ykcjd5",
            "eth": "0xf94f082B639E4be0Ebf5Bd9982BbB34A660f544d"
        }
        await query.answer(f"Adresa u kopjua: {addresses[payment_method]}", show_alert=True)
    else:
        await existing_button_callback(update, context)


async def existing_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_manual_signal":
        await manual_signal_command(update, context)
    elif query.data == "activate_premium":
        await query.edit_message_text(
            "Për të aktivizuar premium, përdorni komandën:\n/activatelicense [çelësi_i_licencës]"
        )
    elif query.data == "check_status":
        await status_command(update, context)
    elif query.data.startswith("admin_"):
        if query.from_user.id != config.ADMIN_ID:
            await query.edit_message_text("⚠️ Ju nuk keni të drejta administratori.")
            return

        action = query.data.replace("admin_", "")
        if action == "send_signal":
            await query.edit_message_text("Përdorni komandën:\n/sendsignal [teksti_i_sinjalit]")
        elif action == "create_license":
            await query.edit_message_text("Përdorni komandën:\n/createlicence [ditët_e_kohëzgjatjes]")
        elif action == "remove_license":
            await query.edit_message_text(
                "Përdorni komandën:\n/removelicense [user_id]\n\n"
                "Për të parë listën e përdoruesve, klikoni 'View Users'"
            )
        elif action == "view_users":
            await view_users_command(update, context)


async def create_license_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != config.ADMIN_ID:
        await update.message.reply_text("⚠️ Kjo komandë është vetëm për administratorët.")
        return

    try:
        duration = int(context.args[0]) if context.args else 30
        license_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        db.create_license(license_key, duration)
        message = f"""
🔑 Licenca e re u krijua:
Çelësi: `{license_key}`
Kohëzgjatja: {duration} ditë
"""
        await update.message.reply_text(message, parse_mode='Markdown')
    except:
        await update.message.reply_text("Përdorimi: /createlicence [ditët_e_kohëzgjatjes]")

async def activate_license_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        license_key = context.args[0]
        if db.activate_license(user_id, license_key):
            keyboard = [[InlineKeyboardButton("📊 Shiko Statusin", callback_data="check_status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "✅ Licenca u aktivizua me sukses! Tani keni qasje premium.",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ Çelës licence i pavlefshëm ose i përdorur.")
    except:
        await update.message.reply_text("Përdorimi: /activatelicense [çelësi]")

async def send_signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != config.ADMIN_ID:
        await update.message.reply_text("⚠️ Kjo komandë është vetëm për administratorët.")
        return

    try:
        signal_text = ' '.join(context.args)
        if not signal_text:
            await update.message.reply_text("Përdorimi: /sendsignal [teksti_i_sinjalit]")
            return

        signal_data = {
            "text": signal_text,
            "sent_by": user_id
        }
        db.save_signal(signal_data)

        users = db._load_data(db.users_file)
        sent_count = 0
        for user_id_str, user_data in users.items():
            user_id = int(user_id_str)
            if user_data["is_premium"] or user_data["signals_used"] < config.FREE_SIGNAL_LIMIT:
                try:
                    if not user_data["is_premium"]:
                        db.add_signal_use(user_id)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🔔 Sinjal i Ri Forex:\n\n{signal_text}"
                    )
                    sent_count += 1
                except Exception as e:
                    print(f"Dërgimi i sinjalit dështoi për përdoruesin {user_id}: {str(e)}")
                    continue

        await update.message.reply_text(f"✅ Sinjali u dërgua me sukses tek {sent_count} përdorues!")
    except Exception as e:
        await update.message.reply_text(f"❌ Gabim në dërgimin e sinjalit: {str(e)}")

async def remove_license_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != config.ADMIN_ID:
        await update.message.reply_text("⚠️ Kjo komandë është vetëm për administratorët.")
        return

    try:
        target_user_id = int(context.args[0])
        if db.remove_user_license(target_user_id):
            await update.message.reply_text(f"✅ Licenca u hoq me sukses për përdoruesin {target_user_id}")
            try:
                # Njofto përdoruesin
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="⚠️ Licenca juaj është çaktivizuar nga administratori."
                )
            except Exception as e:
                logger.error(f"Couldn't notify user {target_user_id}: {str(e)}")
        else:
            await update.message.reply_text("❌ Përdoruesi nuk u gjet ose nuk ka licencë aktive.")
    except ValueError:
        await update.message.reply_text("Përdorimi: /removelicense [user_id]")
    except Exception as e:
        await update.message.reply_text(f"❌ Gabim gjatë heqjes së licencës: {str(e)}")

async def view_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != config.ADMIN_ID:
        await update.message.reply_text("⚠️ Kjo komandë është vetëm për administratorët.")
        return

    try:
        users = db._load_data(db.users_file)
        if not users:
            await update.message.reply_text("Nuk ka përdorues të regjistruar.")
            return

        message = "👥 Lista e përdoruesve:\n\n"
        for user_id, user_data in users.items():
            status = "Premium ✨" if user_data["is_premium"] else "Free 🆓"
            join_date = datetime.fromisoformat(user_data["join_date"]).strftime("%Y-%m-%d")

            message += f"🆔 ID: {user_id}\n"
            message += f"👤 Username: @{user_data['username']}\n"
            message += f"⭐️ Status: {status}\n"
            message += f"📊 Sinjale të përdorura: {user_data['signals_used']}\n"
            if user_data["is_premium"]:
                message += f"📅 Sinjale sot: {user_data.get('daily_signals', 0)}/{config.PREMIUM_DAILY_LIMIT}\n"
                message += f"🔑 Licenca: {user_data.get('license_key', 'N/A')}\n"
            message += f"📆 Regjistruar më: {join_date}\n"
            message += "──────────────\n"

        # Ndaj mesazhin në pjesë për shkak të limitit të Telegram
        max_length = 4096
        messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]

        for msg in messages:
            await update.message.reply_text(msg)

    except Exception as e:
        logger.error(f"Error in view_users_command: {e}")
        await update.message.reply_text(f"❌ Gabim gjatë marrjes së listës së përdoruesve: {str(e)}")