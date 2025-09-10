import time
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from tenacity import retry, stop_after_attempt, wait_fixed
import matplotlib.pyplot as plt
import io
import asyncio


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


TOKEN = '' # Ваш_token
API_URL = 'https://api.coingecko.com/api/v3/'
CRYPTO_PANIC_API_KEY = 'REDACTED_ROTATED_KEY'
CRYPTO_PANIC_URL = f'https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTO_PANIC_API_KEY}&currencies='


translations = {
    'uk': {
        'welcome': "🚀 *Ласкаво просимо до @WolfCryptoBot\\!* 🚀\n\n💰 *Хочеш бути в курсі всіх змін на крипторинку\\?* Ти в правильному місці\\! 📊\n\n[Reach Out to the Developer](https://github.com/ASTAPENKO777)\n\n🔥 *ТОП\\-20 криптовалют прямо зараз:* 🔥\n\n{0}\n\n💡 _Натисни номер криптовалюти\\, щоб отримати її курс і детальну інформацію\\._",
        'currency_selection': "Оберіть фіатну валюту:",
        'currency_selected': "Вибрана валюта: {0}",
        'crypto_details': "**{0}**\n\n💰 Ціна: {1:,.0f} {2}\n📈 Максимум 24 год: {3:,.0f} {2}\n📉 Мінімум 24 год: {4:,.0f} {2}\n🕒 Зміна за 1 год: {5:.2f}% {6}\n📅 Зміна за 24 год: {7:.2f}% {8}\n📆 Зміна за 7 днів: {9:.2f}% {10}\n🏦 Ринкова капіталізація: {11:,.2f}T {2}\n💼 Обсяг торгів (24 год): {12:,.2f}B {2}",
        'convert_instructions': "Введіть команду у форматі:\n`/convert <кількість> <з валюти> <в валюту>`\n\nНаприклад:\n`/convert 1 Bitcoin USD`\n`/convert 0.5 Ethereum UAH`",
        'conversion_result': "💱 *Результат конвертації:*\n`{0} {1} = {2:.2f} {3}`",
        'error_fetching_data': "❌ Упс\\! Не вдалося отримати дані\\. Спробуйте пізніше\\.",
        'invalid_number': "Невірний формат числа\\. Спробуйте ще раз\\.",
        'invalid_command_format': "Невірний формат команди\\. Використовуйте `/convert <кількість> <з валюти> <в валюту>`\\.",
        'refresh_button': "🔄 Оновити",
        'graph_button': "📊 Графік",
        'convert_button': "💱 Конвертувати",
        'monitoring_button': "📈 Моніторинг ціни",
        'choose_language': "Оберіть мову / Choose language:",
        'language_selected': "Вибрана мова / Selected language: {0}",
        'monitoring_started': "Моніторинг ціни запущено. Ви будете отримувати повідомлення при зміні ціни.",
        'monitoring_settings_updated': "Налаштування моніторингу оновлено: інтервал - {0} хвилин, поріг - {1}%.",
        'price_change_alert': "Ціна {0} змінилася на {1:.2f}% за останні {2} хвилин.\n\nМинула ціна: {3} {4}\nПоточна ціна: {5} {4}",
        'choose_monitoring_interval': "Оберіть інтервал моніторингу:",
        'monitoring_interval_selected': "Моніторинг ціни запущено з інтервалом {0} хвилин.",
        'monitoring_stopped': "Моніторинг ціни зупинено.",
        'market_analysis': "📊 *Аналіз ринку:*\n\n{0}",
        'top_gainers': "🚀 *Топ-5 криптовалют за зростанням за 24 години:*\n\n{0}",
        'top_losers': "🔻 *Топ-5 криптовалют за падінням за 24 години:*\n\n{0}",
        'monitoring_interval_5': "5 хвилин",
        'monitoring_interval_30': "30 хвилин",
        'monitoring_interval_120': "2 години",
        'stop_monitoring': "Зупинити моніторинг",
        'subscribe_news': "Ви успішно підписались на сповіщення про важливі події!",
        'unsubscribe_news': "Ви успішно відписались від сповіщень про важливі події.",
        'already_subscribed': "Ви вже підписані на сповіщення.",
        'not_subscribed': "Ви не підписані на сповіщення."
    },
    'en': {
        'welcome': "🚀 *Welcome to @WolfCryptoBot\\!* 🚀\n\n💰 *Want to stay updated on all cryptocurrency changes\\?* You're in the right place\\! 📊\n\n[Reach Out to the Developer](https://github.com/ASTAPENKO777)\n\n🔥 *TOP\\-20 cryptocurrencies right now:* 🔥\n\n{0}\n\n💡 _Press the number of the cryptocurrency to get its rate and detailed information\\._",
        'currency_selection': "Choose a fiat currency:",
        'currency_selected': "Selected currency: {0}",
        'crypto_details': "**{0}**\n\n💰 Price: {1:,.0f} {2}\n📈 24h High: {3:,.0f} {2}\n📉 24h Low: {4:,.0f} {2}\n🕒 1h Change: {5:.2f}% {6}\n📅 24h Change: {7:.2f}% {8}\n📆 7d Change: {9:.2f}% {10}\n🏦 Market Cap: {11:,.2f}T {2}\n💼 24h Volume: {12:,.2f}B {2}",
        'convert_instructions': "Enter the command in the format:\n`/convert <amount> <from currency> <to currency>`\n\nFor example:\n`/convert 1 Bitcoin USD`\n`/convert 0.5 Ethereum UAH`",
        'conversion_result': "💱 *Conversion result:*\n`{0} {1} = {2:.2f} {3}`",
        'error_fetching_data': "❌ Oops\\! Failed to fetch data\\. Please try again later\\.",
        'invalid_number': "Invalid number format\\. Please try again\\.",
        'invalid_command_format': "Invalid command format\\. Use `/convert <amount> <from currency> <to currency>`\\.",
        'refresh_button': "🔄 Refresh",
        'graph_button': "📊 Graph",
        'convert_button': "💱 Convert",
        'monitoring_button': "📈 Price Monitoring",
        'choose_language': "Choose language / Оберіть мову:",
        'language_selected': "Selected language / Вибрана мова: {0}",
        'monitoring_started': "Price monitoring started. You will receive alerts on price changes.",
        'monitoring_settings_updated': "Monitoring settings updated: interval - {0} minutes, threshold - {1}%.",
        'price_change_alert': "Price of {0} changed by {1:.2f}% in the last {2} minutes.\n\nPrevious price: {3} {4}\nCurrent price: {5} {4}",
        'choose_monitoring_interval': "Choose monitoring interval:",
        'monitoring_interval_selected': "Price monitoring started with an interval of {0} minutes.",
        'monitoring_stopped': "Price monitoring stopped.",
        'market_analysis': "📊 *Market Analysis:*\n\n{0}",
        'top_gainers': "🚀 *Top 5 cryptocurrencies by 24h growth:*\n\n{0}",
        'top_losers': "🔻 *Top 5 cryptocurrencies by 24h decline:*\n\n{0}",
        'monitoring_interval_5': "5 minutes",
        'monitoring_interval_30': "30 minutes",
        'monitoring_interval_120': "2 hours",
        'stop_monitoring': "Stop monitoring",
        'subscribe_news': "You have successfully subscribed to important event notifications!",
        'unsubscribe_news': "You have successfully unsubscribed from important event notifications.",
        'already_subscribed': "You are already subscribed to notifications.",
        'not_subscribed': "You are not subscribed to notifications."
    }
}


def get_text(language, key, *args):
    return translations.get(language, translations['uk'])[key].format(*args)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_top_cryptos(currency='usd'):
    try:
        response = requests.get(f'{API_URL}coins/markets', params={'vs_currency': currency, 'order': 'market_cap_desc', 'per_page': 20, 'page': 1}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [(coin['id'], coin['name']) for coin in data]
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при запиті до API: {e}")
        return []


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_crypto_details(crypto_id, currency='usd'):
    try:
        response = requests.get(f'{API_URL}coins/{crypto_id}', timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при запиті до API: {e}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_crypto_price(crypto_id, currency='usd'):
    try:
        response = requests.get(f'{API_URL}simple/price', params={'ids': crypto_id, 'vs_currencies': currency}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[crypto_id][currency] if crypto_id in data else None
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при запиті до API: {e}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_crypto_history(crypto_id, days=30, currency='usd'):
    try:
        response = requests.get(f'{API_URL}coins/{crypto_id}/market_chart', params={'vs_currency': currency, 'days': days}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['prices']
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при запиті до API: {e}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_latest_news():
    try:
        response = requests.get(CRYPTO_PANIC_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Отримано новини: {data}")
        return data['results']
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при отриманні новин: {e}")
        return None


def plot_crypto_history(prices):
    timestamps = [x[0] for x in prices]
    prices_usd = [x[1] for x in prices]
    
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, prices_usd, label='Ціна в USD', color='b')
    plt.title('Історичний графік ціни')
    plt.xlabel('Час')
    plt.ylabel('Ціна (USD)')
    plt.grid(True)
    plt.legend()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf


async def subscribe_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if 'subscribed_users' not in context.bot_data:
        context.bot_data['subscribed_users'] = set()
    
    language = context.user_data.get('language', 'uk')
    
    if user_id in context.bot_data['subscribed_users']:
        await update.message.reply_text(get_text(language, 'already_subscribed'))
        return
    
    context.bot_data['subscribed_users'].add(user_id)
    logger.info(f"Користувач {user_id} підписався на новини")
    await update.message.reply_text(get_text(language, 'subscribe_news'))


async def send_news_alerts(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Функція send_news_alerts викликана")
    if 'subscribed_users' not in context.bot_data or not context.bot_data['subscribed_users']:
        logger.info("Немає підписаних користувачів")
        return

    latest_news = get_latest_news()
    if not latest_news:
        logger.info("Не вдалося отримати новини")
        return

    for user_id in context.bot_data['subscribed_users']:
        for news_item in latest_news[:1]:  # Надсилаємо останні 1 новин
            title = news_item.get('title', 'Без назви')
            url = news_item.get('url', '#')
            created_at = news_item.get('created_at', 'Невідомо')
            message = f"🚨 *Нова подія!* 🚨\n\n*{title}*\n\n[Читати далі]({url})\n\n_Опубліковано: {created_at}_"
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
            logger.info(f"Надіслано новину користувачу {user_id}")


async def unsubscribe_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    language = context.user_data.get('language', 'uk')
    
    if 'subscribed_users' in context.bot_data and user_id in context.bot_data['subscribed_users']:
        context.bot_data['subscribed_users'].remove(user_id)
        await update.message.reply_text(get_text(language, 'unsubscribe_news'))
    else:
        await update.message.reply_text(get_text(language, 'not_subscribed'))


async def start_news_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Запуск завдання для надсилання новин")
    context.job_queue.run_repeating(send_news_alerts, interval=10800, first=10)  # 10800 секунд = 3 години


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uk')
    currency = context.user_data.get('selected_currency', 'usd')
    top_cryptos = get_top_cryptos(currency)
    if not top_cryptos:
        await update.message.reply_text(get_text(language, 'error_fetching_data'), parse_mode="MarkdownV2")
        return

    crypto_names = [f"🔹 {i+1}\\. `{name}`" for i, (id, name) in enumerate(top_cryptos)] 

    keyboard = [
        [f"{i+1}", f"{i+6}", f"{i+11}", f"{i+16}"]  
        for i in range(5)  
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        get_text(language, 'welcome', "\n".join(crypto_names)),
        parse_mode="MarkdownV2",  
        reply_markup=reply_markup
    )


async def set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uk')
    currencies = ['USD', 'EUR', 'UAH', 'GBP', 'JPY']  
    keyboard = [[InlineKeyboardButton(currency, callback_data=f"set_currency_{currency}") for currency in currencies]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(get_text(language, 'currency_selection'), reply_markup=reply_markup)


async def handle_currency_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()  

        selected_currency = query.data.split('_')[-1]  
        context.user_data['selected_currency'] = selected_currency.lower()  
        language = context.user_data.get('language', 'uk')
        
        await query.edit_message_text(get_text(language, 'currency_selected', selected_currency), parse_mode="MarkdownV2")

        new_update = Update(update.update_id, message=query.message)
        await start(new_update, context)
    except Exception as e:
        logger.error(f"Помилка при обробці вибору валюти: {e}")
        await query.answer("Сталася помилка. Спробуйте ще раз.")


async def select_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uk')
    try:
        selected_index = int(update.message.text) - 1
        currency = context.user_data.get('selected_currency', 'usd')
        top_cryptos = get_top_cryptos(currency)
        
        if not top_cryptos:
            await update.message.reply_text(get_text(language, 'error_fetching_data'), parse_mode="MarkdownV2")
            return
        
        if selected_index < 0 or selected_index >= len(top_cryptos):
            await update.message.reply_text("Будь ласка, вибери правильний номер криптовалюти.")
            return
        
        context.user_data['selected_crypto'] = top_cryptos[selected_index][0]
        context.user_data['previous_price'] = get_crypto_price(context.user_data['selected_crypto'], currency)
        context.user_data['monitoring'] = True

        details = get_crypto_details(context.user_data['selected_crypto'])
        if not details:
            await update.message.reply_text(get_text(language, 'error_fetching_data'), parse_mode="MarkdownV2")
            return
        
        current_price = details['market_data']['current_price'][currency]
        high_24h = details['market_data']['high_24h'][currency]
        low_24h = details['market_data']['low_24h'][currency]
        price_change_1h = details['market_data']['price_change_percentage_1h_in_currency'][currency]
        price_change_24h = details['market_data']['price_change_percentage_24h_in_currency'][currency]
        price_change_7d = details['market_data']['price_change_percentage_7d_in_currency'][currency]
        market_cap = details['market_data']['market_cap'][currency]
        volume_24h = details['market_data']['total_volume'][currency]

        smiley_1h = "😊" if price_change_1h > 0 else "😞" if price_change_1h < 0 else "😏"
        smiley_24h = "😊" if price_change_24h > 0 else "😞" if price_change_24h < 0 else "😏"
        smiley_7d = "😊" if price_change_7d > 0 else "😞" if price_change_7d < 0 else "😏"

        message_text = get_text(
            language,
            'crypto_details',
            top_cryptos[selected_index][1],
            current_price,
            currency.upper(),
            high_24h,
            low_24h,
            price_change_1h,
            smiley_1h,
            price_change_24h,
            smiley_24h,
            price_change_7d,
            smiley_7d,
            market_cap,
            volume_24h
        )

        keyboard = [
            [InlineKeyboardButton(get_text(language, 'refresh_button'), callback_data="update_crypto")],
            [InlineKeyboardButton(get_text(language, 'graph_button'), callback_data="send_graph")],
            [InlineKeyboardButton(get_text(language, 'convert_button'), callback_data="convert_crypto")],
            [InlineKeyboardButton(get_text(language, 'monitoring_button'), callback_data="start_monitoring")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = await update.message.reply_text(message_text, parse_mode='Markdown', reply_markup=reply_markup)
        context.user_data['last_message_id'] = message.message_id  
    except (ValueError, IndexError) as e:
        logger.error(f"Помилка при виборі криптовалюти: {e}")
        await update.message.reply_text("Сталася помилка. Спробуйте ще раз.")


async def update_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    try:
        await query.answer() 

        language = context.user_data.get('language', 'uk')
        last_update_time = context.user_data.get('last_update_time', 0)
        current_time = time.time()
        if current_time - last_update_time < 60:  
            await query.answer(get_text(language, 'error_fetching_data'))
            return
        
        context.user_data['last_update_time'] = current_time

        selected_crypto = context.user_data.get('selected_crypto')
        currency = context.user_data.get('selected_currency', 'usd')
        if not selected_crypto:
            await query.answer(get_text(language, 'error_fetching_data'))
            return

        details = get_crypto_details(selected_crypto)
        if not details:
            await query.answer(get_text(language, 'error_fetching_data'))
            return
        
        current_price = details['market_data']['current_price'][currency]
        high_24h = details['market_data']['high_24h'][currency]
        low_24h = details['market_data']['low_24h'][currency]
        price_change_1h = details['market_data']['price_change_percentage_1h_in_currency'][currency]
        price_change_24h = details['market_data']['price_change_percentage_24h_in_currency'][currency]
        price_change_7d = details['market_data']['price_change_percentage_7d_in_currency'][currency]
        market_cap = details['market_data']['market_cap'][currency]
        volume_24h = details['market_data']['total_volume'][currency]
        
        smiley_1h = "😊" if price_change_1h > 0 else "😞" if price_change_1h < 0 else "😏"
        smiley_24h = "😊" if price_change_24h > 0 else "😞" if price_change_24h < 0 else "😏"
        smiley_7d = "😊" if price_change_7d > 0 else "😞" if price_change_7d < 0 else "😏"
        
        message_text = get_text(
            language,
            'crypto_details',
            selected_crypto,
            current_price,
            currency.upper(),
            high_24h,
            low_24h,
            price_change_1h,
            smiley_1h,
            price_change_24h,
            smiley_24h,
            price_change_7d,
            smiley_7d,
            market_cap,
            volume_24h
        )
        try:
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=context.user_data['last_message_id'],
                text=message_text,
                parse_mode='Markdown',
                reply_markup=query.message.reply_markup
            )
        except Exception as e:
            logger.error(f"Помилка при редагуванні повідомлення: {e}")
            await query.answer(get_text(language, 'error_fetching_data'))
    except Exception as e:
        logger.error(f"Помилка при оновленні криптовалюти: {e}")
        await query.answer("Сталася помилка. Спробуйте ще раз.")


async def send_graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uk')  
    
    selected_crypto = context.user_data.get('selected_crypto')
    currency = context.user_data.get('selected_currency', 'usd')
    
    if not selected_crypto:
        await update.callback_query.answer(get_text(language, 'error_fetching_data'))
        return
    
    prices = get_crypto_history(selected_crypto, currency=currency)
    if not prices:
        await update.callback_query.answer(get_text(language, 'error_fetching_data'))
        return
    
    buf = plot_crypto_history(prices)
    await context.bot.send_photo(chat_id=update.callback_query.message.chat_id, photo=buf)
    buf.close()


async def convert_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uk')
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        get_text(language, 'convert_instructions'),
        parse_mode="MarkdownV2"
    )


async def handle_convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uk')
    try:
        args = context.args
        if len(args) != 3:
            await update.message.reply_text(get_text(language, 'invalid_command_format'), parse_mode="MarkdownV2")
            return

        amount = float(args[0])
        from_currency = args[1].lower()
        to_currency = args[2].lower()

        price = get_crypto_price(from_currency, to_currency)
        if not price:
            await update.message.reply_text(get_text(language, 'error_fetching_data'), parse_mode="MarkdownV2")
            return

        converted_amount = amount * price
        await update.message.reply_text(
            get_text(language, 'conversion_result', amount, from_currency.upper(), converted_amount, to_currency.upper()),
            parse_mode="MarkdownV2"
        )
    except ValueError:
        await update.message.reply_text(get_text(language, 'invalid_number'), parse_mode="MarkdownV2")
    except Exception as e:
        logger.error(f"Помилка при конвертації: {e}")
        await update.message.reply_text(get_text(language, 'error_fetching_data'), parse_mode="MarkdownV2")


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uk')
    keyboard = [
        [InlineKeyboardButton("Українська", callback_data="set_language_uk")],
        [InlineKeyboardButton("English", callback_data="set_language_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(get_text(language, 'choose_language'), reply_markup=reply_markup)


async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()  

        selected_language = query.data.split('_')[-1]
        context.user_data['language'] = selected_language
        
        language = context.user_data.get('language', 'uk') 
        
        await query.edit_message_text(get_text(language, 'language_selected', selected_language))

        new_update = Update(update.update_id, message=query.message)
        await start(new_update, context)
    except Exception as e:
        logger.error(f"Помилка при обробці вибору мови: {e}")
        await query.answer("Сталася помилка. Спробуйте ще раз.")


async def start_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()

        language = context.user_data.get('language', 'uk')
        keyboard = [
            [InlineKeyboardButton(get_text(language, 'monitoring_interval_5'), callback_data="monitoring_interval_5")],
            [InlineKeyboardButton(get_text(language, 'monitoring_interval_30'), callback_data="monitoring_interval_30")],
            [InlineKeyboardButton(get_text(language, 'monitoring_interval_120'), callback_data="monitoring_interval_120")],
            [InlineKeyboardButton(get_text(language, 'stop_monitoring'), callback_data="stop_monitoring")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(get_text(language, 'choose_monitoring_interval'), reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Помилка при запуску моніторингу: {e}")
        await query.answer("Сталася помилка. Спробуйте ще раз.")


async def handle_monitoring_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()

        interval = int(query.data.split('_')[-1]) 
        context.user_data['monitoring_interval'] = interval  

        language = context.user_data.get('language', 'uk')
        await query.edit_message_text(get_text(language, 'monitoring_interval_selected', interval))

        context.job_queue.run_repeating(monitor_price, interval=interval * 60, first=0, user_id=query.from_user.id)
    except Exception as e:
        logger.error(f"Помилка при обробці вибору інтервалу: {e}")
        await query.answer("Сталася помилка. Спробуйте ще раз.")


async def stop_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()

        language = context.user_data.get('language', 'uk')
        jobs = context.job_queue.get_jobs_by_name(str(query.from_user.id))
        for job in jobs:
            job.schedule_removal()

        await query.edit_message_text(get_text(language, 'monitoring_stopped'))
    except Exception as e:
        logger.error(f"Помилка при зупинці моніторингу: {e}")
        await query.answer("Сталася помилка. Спробуйте ще раз.")


async def monitor_price(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.user_id
    selected_crypto = context.user_data.get('selected_crypto')
    currency = context.user_data.get('selected_currency', 'usd')

    current_price = get_crypto_price(selected_crypto, currency)
    previous_price = context.user_data.get('previous_price')

    if previous_price is not None and current_price is not None:
        price_change = ((current_price - previous_price) / previous_price) * 100

        language = context.user_data.get('language', 'uk')
        interval = context.user_data.get('monitoring_interval', 5)  
        message = get_text(language, 'price_change_alert', selected_crypto, price_change, interval, previous_price, currency.upper(), current_price)

        prices = get_crypto_history(selected_crypto, days=1, currency=currency)
        if prices:
            buf = plot_crypto_history(prices)
            await context.bot.send_photo(chat_id=user_id, photo=buf, caption=message)
            buf.close()
        else:
            await context.bot.send_message(chat_id=user_id, text=message)

    context.user_data['previous_price'] = current_price


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_top_gainers(currency='usd', top_n=10):
    try:
        response = requests.get(
            f'{API_URL}coins/markets',
            params={'vs_currency': currency, 'order': 'market_cap_desc', 'per_page': 100, 'page': 1},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        sorted_data = sorted(data, key=lambda x: x['price_change_percentage_24h'], reverse=True)

        return sorted_data[:top_n]
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при запиті до API: {e}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_top_losers(currency='usd', top_n=10):
    try:
        response = requests.get(
            f'{API_URL}coins/markets',
            params={'vs_currency': currency, 'order': 'market_cap_desc', 'per_page': 100, 'page': 1},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        sorted_data = sorted(data, key=lambda x: x['price_change_percentage_24h'])

        return sorted_data[:top_n]
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при запиті до API: {e}")
        return None


async def top_gainers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uk')
    currency = context.user_data.get('selected_currency', 'usd')

    top_gainers_data = get_top_gainers(currency)

    if not top_gainers_data:
        await update.message.reply_text(get_text(language, 'error_fetching_data'), parse_mode="MarkdownV2")
        return

    gainers_message = ""
    for i, coin in enumerate(top_gainers_data[:5], 1):
        gainers_message += (
            f"{i}. *{coin['name']}* ({coin['symbol'].upper()})\n"
            f"   💵 Price: {coin['current_price']:,.2f} {currency.upper()}\n"
            f"   📈 Change: {coin['price_change_percentage_24h']:.2f}%\n\n"
        )

    await update.message.reply_text(get_text(language, 'top_gainers', gainers_message), parse_mode="Markdown")


async def top_losers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uk')
    currency = context.user_data.get('selected_currency', 'usd')

    top_losers_data = get_top_losers(currency)

    if not top_losers_data:
        await update.message.reply_text(get_text(language, 'error_fetching_data'), parse_mode="MarkdownV2")
        return

    losers_message = ""
    for i, coin in enumerate(top_losers_data[:5], 1):
        losers_message += (
            f"{i}. *{coin['name']}* ({coin['symbol'].upper()})\n"
            f"   💵 Price: {coin['current_price']:,.2f} {currency.upper()}\n"
            f"   📉 Change: {coin['price_change_percentage_24h']:.2f}%\n\n"
        )

    await update.message.reply_text(get_text(language, 'top_losers', losers_message), parse_mode="Markdown")


def main():
    application = Application.builder().token(TOKEN).build()

    application.job_queue.run_once(start_news_job, when=0)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_currency", set_currency))
    application.add_handler(CommandHandler("set_language", set_language))
    application.add_handler(CommandHandler("convert", handle_convert))
    application.add_handler(CommandHandler("top_gainers", top_gainers))  
    application.add_handler(CommandHandler("top_losers", top_losers))
    application.add_handler(CommandHandler("subscribe_news", subscribe_news))
    application.add_handler(CommandHandler("unsubscribe_news", unsubscribe_news))
    application.add_handler(MessageHandler(filters.Regex(r"^[1-9][0-9]*$"), select_crypto))
    application.add_handler(CallbackQueryHandler(handle_currency_selection, pattern='^set_currency_'))
    application.add_handler(CallbackQueryHandler(handle_language_selection, pattern='^set_language_'))
    application.add_handler(CallbackQueryHandler(update_crypto, pattern='update_crypto'))
    application.add_handler(CallbackQueryHandler(send_graph, pattern='send_graph'))
    application.add_handler(CallbackQueryHandler(convert_crypto, pattern='convert_crypto'))
    application.add_handler(CallbackQueryHandler(start_monitoring, pattern='start_monitoring'))
    application.add_handler(CallbackQueryHandler(handle_monitoring_interval, pattern='^monitoring_interval_'))
    application.add_handler(CallbackQueryHandler(stop_monitoring, pattern='stop_monitoring'))

    application.run_polling()

if __name__ == '__main__':

    main()
