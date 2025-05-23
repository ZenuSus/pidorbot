# говнокод написан зенусом (https://zenusus.github.io/). 
# не используйте его без указания автора кода в месте, который при желании легко может увидеть каждый
# если вы берете кусок кода, указывайте его авторство в информации проекта, которая будет доступна всем.
# если ты просто смотришь код, то предупреждаю - он настолько плохой, что я сам не знаю как он работает.

import telebot
import random
import time
import logging
from threading import Lock
import sqlite3
from telebot import types
import os
import requests
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Токен нах
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'token')
ADMIN_ID = 5544581571  # айдишник админа бота (он кароч может управлять банами, базой итд)
MAX_VOICE_DURATION = 60  # длина гски, сделал как переменную чтоб быстренько поменять если че

# апи thecatapi.com (можешь ваще нет заполнять, оно и так работает, хотя если сменить значение не на токен код отвалится)
CAT_API_KEY = 'YOUR_CATAPI_KEY'

bot = telebot.TeleBot(TOKEN)

# чет с бдшкой чтоб работало
db_lock = Lock()

# Подключение к базе данных SQLite
def get_db_connection():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Инициализация базы данных
def init_db():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                score INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                last_used_get INTEGER DEFAULT 0,
                last_used_booster INTEGER DEFAULT 0
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                chat_type TEXT
            )
            ''')
            conn.commit()
        logging.info("База данных инициализирована.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")

# поиск по юзу для некоторых комманд
def get_user_by_username(username):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                return cursor.fetchone()
    except Exception as e:
        logging.error(f"Ошибка при поиск нах: {e}")
        return None

# создание юзера итп
def get_or_create_user(user_id, first_name, username):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                user = cursor.fetchone()
                if not user:
                    cursor.execute('INSERT INTO users (user_id, first_name, username) VALUES (?, ?, ?)', (user_id, first_name, username))
                    conn.commit()
                return user
    except Exception as e:
        logging.error(f"Ошибка нах при создании юзера нах {e}")
        return None

# не работает нихуя
def update_user_coins(user_id, coins):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins, user_id))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка: {e}")

def update_user_score(user_id, points):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET score = score + ? WHERE user_id = ?', (points, user_id))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка: {e}")

# время получения хуев
def update_last_used_get(user_id):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET last_used_get = ? WHERE user_id = ?', (int(time.time()), user_id))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка времени в гет: {e}")

# тоже не работает нихуя, убирать лень
def update_last_used_booster(user_id):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET last_used_booster = ? WHERE user_id = ?', (int(time.time()), user_id))
                conn.commit()
    except Exception as e:
        logging.error(f"бляяя ошибкаааа: {e}")

# получение данных
def get_user_data(user_id):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT first_name, username, score, coins, last_used_get, last_used_booster FROM users WHERE user_id = ?', (user_id,))
                return cursor.fetchone()
    except Exception as e:
        logging.error(f"Ошибка при получении данных: {e}")
        return None

# хуи
def get_user_score(user_id):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT score FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return result['score'] if result else 0
    except Exception as e:
        logging.error(f"Ошибка при получении хуев нах: {e}")
        return 0

# лидерборд
def get_leaderboard():
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT first_name, username, score FROM users ORDER BY score DESC LIMIT 10')
                return cursor.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при получении лидерборда: {e}")
        return []


# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    firstname = message.from_user.first_name
    bot.reply_to(message, f"👋 <b>Привет, {firstname}. Я пидорбот. </b> \n\n ❔ Используй команду /help, чтобы узнать что я могу. \n\n 🤑 Канал разраба: @zenusoff \n Мой канал: @pidorbot_ch \n\n Сейчас проходит сбор на сервер, <a href='https://t.me/pidorbot_ch/74'>подробнее</a>", disable_web_page_preview=True, parse_mode='HTML')

# /help
@bot.message_handler(commands=['help'])
def send_(message):
    bot.reply_to(message, "❔ <b> Помощь: </b> <a href='https://t.me/skibidi_pidor_bot/docs'>нажми</a> \nХочешь узнать библиотеки в коде? Напиши /libs", parse_mode='HTML')

    # /libs
@bot.message_handler(commands=['libs'])
def send_welcome(message):
    bot.reply_to(message, "✍️ <b> Использованные библиотеки: </b> \n\n <blockquote> telebot - для работы бота\n random - рандом в командах \n time - расчет времени \n logging - логи \n sqlite - базы данных \n os - создание файлов </blockquote>", parse_mode='HTML')

# /me
@bot.message_handler(commands=['me'])
def show_me(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    # создаем юзера или выбираем из бд если есть
    get_or_create_user(user_id, first_name, username)

    # формировка соо
    user_data = get_user_data(user_id)
    if user_data:
        first_name, username, score, coins, _, _ = user_data
        me_message = f"👤 <b> Профиль: </b> \n\n"
        me_message += f"Имя: {first_name}\n"
        if username:
            me_message += f"Юзернейм: @{username}\n"
        me_message += f"Хуи в жопе: {score}\n"
        me_message += f"Монеты: {coins}"
    else:
        me_message = "❌ Произошла ошибка при получении данных."

    bot.reply_to(message, me_message, parse_mode='HTML')

# /getpenis
@bot.message_handler(commands=['getpenis'])
def get_points(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    # опять с бд херь ало
    get_or_create_user(user_id, first_name, username)

    user_data = get_user_data(user_id)
    if user_data:
        last_used_get = user_data['last_used_get']
        current_time = int(time.time())

        # проверка времени /get
        if current_time - last_used_get >= 2 * 5400:
            # получение хуев
            points = random.randint(3, 5)
            update_user_score(user_id, points)
            update_last_used_get(user_id)

            user_data = get_user_data(user_id)
            if user_data:
                score = user_data[2]
                chat_id = message.chat.id
                firstname = message.from_user.first_name
                bot.reply_to(message, f"🎉 Отлично, {firstname}, ты получил {points} хуёв! Теперь у тебя {score} хуёв.")
            else:
                bot.reply_to(message, "❌ Произошла ошибка при обновлении данных.")
        else:
            # опять время и отправка пиздец говнокод
            remaining_time = 2 * 5400 - (current_time - last_used_get)
            hours = remaining_time // 5400
            minutes = (remaining_time % 5400) // 60
            chat_id = message.chat.id
            firstname = message.from_user.first_name
            bot.reply_to(message, f"❌ Мне жаль, {firstname}, но ты сможешь получить еще хуев только через {hours} часов и {minutes} минут.")
    else:
        bot.reply_to(message, "❌ Произошла ошибка при получении данных.")

# /liderboard
@bot.message_handler(commands=['liderboard'])
def show_leaderboard(message):
    try:
        leaderboard = get_leaderboard()
        if leaderboard:
            leaderboard_message = "🏆 <b>Лидерборд:</b>\n\n"
            for i, (first_name, username, score) in enumerate(leaderboard, start=1):
                leaderboard_message += f'{i}. <a href="t.me/{username}">{first_name}</a> — {score} хуёв\n' 
        else:
            leaderboard_message = "❌ Лидерборд пуст."

        # Отправляем сообщение
        bot.reply_to(message, leaderboard_message, disable_web_page_preview=True, parse_mode='HTML')
    except Exception as e:
        logging.error(f"Ошибка в команде /liderboard: {e}")
        bot.reply_to(message, f"❌ Произошла ошибка при получении лидерборда: {e}")

# /cat
@bot.message_handler(commands=['cat'])
def send_cat(message):
    try:
        # получение фотки кота (пздц долго работает ебаный апи)
        if CAT_API_KEY:
            response = requests.get(f'https://api.thecatapi.com/v1/images/search?api_key={CAT_API_KEY}')
        else:
            response = requests.get('https://api.thecatapi.com/v1/images/search')
        
        if response.status_code == 200:
            cat_data = response.json()
            cat_url = cat_data[0]['url']
            
            
            bot.reply_to(message, "Ищу кота... \n ⚠️ Внимание! Данная команда может работать медленно из-за проблем с API, а также сервером.")
            time.sleep(1)
            chat_id = message.chat.id
            firstname = message.from_user.first_name
            bot.send_photo(message.chat.id, cat_url, caption=f"Держи котика, {firstname}. Как тебе? 😺")
        else:
            bot.reply_to(message, "Не получилось отправить котика 😿")
    
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, f"❌ Произошла ошибка: {e}")

        # /eblan
@bot.message_handler(commands=['eblan'])
def send_random_number(message):
    # определяем ебланство через оч сложные алгоритмы прям пздц
    random_number = random.randint(1, 100)
    bot.reply_to(message, f"🧐 Думаю, что ты еблан на {random_number}%")

#  /play_game
@bot.message_handler(commands=['play_game'])
def play_game(message):
    try:
        # сумма палучат
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Ошибка инициализации суммы. Используй команду так: /play_game [сумма ставки]")
            return

        bet_amount = int(args[1])
        if bet_amount <= 0:
            bot.reply_to(message, "Ставка должна быть больше 0.")
            return

        user_id = message.from_user.id
        user_score = get_user_score(user_id)

        # проверка на нищего нахуй
        if user_score < bet_amount:
            bot.reply_to(message, "❌ У тебя недостаточно хуёв для столь большой ставки. Подзаработай, и возращайся позже.")
            return

        # иллюзия выбора
        markup = types.InlineKeyboardMarkup()
        dart_button = types.InlineKeyboardButton("🎯 Дартс", callback_data=f"dart_{bet_amount}")
        casino_button = types.InlineKeyboardButton("🎰 Казино", callback_data=f"casino_{bet_amount}")
        markup.add(dart_button, casino_button)

        bot.reply_to(message, "🕹️ Выбери игру:", reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        user_id = call.from_user.id
        data = call.data.split('_')
        game_type = data[0]
        bet_amount = int(data[1])

        user_score = get_user_score(user_id)

        if game_type == "dart":
            # дартс
            if random.random() < 0.1:  # аж 10% шанс на победу ну короч можешь поменять
                win_amount = int(bet_amount * 1.2)
                update_user_score(user_id, win_amount)
                bot.answer_callback_query(call.id, f"🎉 Ты запустил стрелу, и выиграл {win_amount} хуёв. Поздравляю!")
            else:
                update_user_score(user_id, -bet_amount)
                bot.answer_callback_query(call.id, "😭 Стрела не попала. Ты проиграл. Мы забрали твою ставку себе.")

        elif game_type == "casino":
            # казино 1 икс бет
            if random.random() < 0.1:  # 5% шанс на победу (ну а хули нет)
                win_amount = int(bet_amount * 1.2)
                update_user_score(user_id, win_amount)
                bot.answer_callback_query(call.id, f"🎉 Ты крутанул казик, и тыиграл {win_amount} хуёв. Поздравляю!")
            else:
                update_user_score(user_id, -bet_amount)
                bot.answer_callback_query(call.id, "😭 Казик не в настроении. Ты проиграл. Мы забрали твою ставку себе.")

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Произошла ошибка: {e}")

        # инлайн нах
@bot.inline_handler(func=lambda query: True)
def handle_inline_query(inline_query):
    try:
        r = types.InlineQueryResultArticle(
            id='1',
            title='Отправить рекламко',
            input_message_content=types.InputTextMessageContent(
                message_text='@skibidi_pidor_bot получай хуи в жопу уже сегодня.'
            ),
            thumbnail_url='https://zenusus.github.io/images/riba.jpg',
            description='ышвагшвфцгзааыщупныщыпогыуапвк',
            )
        
        bot.answer_inline_query(inline_query.id, [r])
    except Exception as e:
        print(e)

# забыл что это делает уже
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == 'send_message':
        bot.send_message(chat_id=call.message.chat.id, text='@skibidi_pidor_bot лучший ботек (япидор)')

@bot.message_handler(commands=['send_penis'])
def send_penis_points(message):
    try:
        args = message.text.split()
        
        # проверка долбоею ли юзер и не указал хуйню
        if len(args) < 3:
            bot.reply_to(message, "❌ Используй команду так: /send_penis @username [сумма]")
            return

        # получение нахуй
        recipient_username = args[1].replace('@', '')
        try:
            amount = int(args[2])
        except ValueError:
            bot.reply_to(message, "❌ Сумма должна быть числом.")
            return

        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше нуля.")
            return

        sender_id = message.from_user.id
        sender_data = get_user_data(sender_id)
        if not sender_data:
            bot.reply_to(message, "❌ Произошла ошибка при получении данных.")
            return

        if sender_data['score'] < amount:
            bot.reply_to(message, "❌ У тебя недостаточно хуев для перевода.")
            return

        recipient_data = get_user_by_username(recipient_username)
        if not recipient_data:
            bot.reply_to(message, f"❌ Пользователь @{recipient_username} не найден.")
            return

        # подтвержение еблан ли юзер
        markup = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton("Подтвердить перевод", callback_data=f"confirm_send_penis_{amount}_{recipient_data['user_id']}")
        markup.add(confirm_button)

        bot.reply_to(message, f"🔄 Перевести {amount} хуев пользователю @{recipient_username}. Подтверди перевод:", reply_markup=markup)
    except Exception as e:
        logging.error(f"Ошибка в команде /send_penis: {e}")
        bot.reply_to(message, f"❌ Произошла ошибка: {e}\nИди нахуй.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_send_penis_'))
def handle_confirm_send_penis(call):
    try:
        data = call.data.split('_')
        amount = int(data[2])
        recipient_id = int(data[3])

        sender_id = call.from_user.id
        sender_data = get_user_data(sender_id)
        if not sender_data:
            bot.answer_callback_query(call.id, "❌ Произошла ошибка при получении данных.")
            return

        if sender_data['score'] < amount:
            bot.answer_callback_query(call.id, "❌ У тебя недостаточно очков для перевода.")
            return

        recipient_data = get_user_data(recipient_id)
        if not recipient_data:
            bot.answer_callback_query(call.id, "❌ Произошла ошибка при получении данных получателя.")
            return

        # зачисление
        update_user_score(sender_id, -amount) 
        update_user_score(recipient_id, amount)

        bot.answer_callback_query(call.id, f"✅ Перевод {amount} очков выполнен!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        # уведовление еблану
        bot.send_message(recipient_id, f"🎉 Вам перевели {amount} очков от @{sender_data['username']}.")
    except Exception as e:
        logging.error(f"Ошибка при обработке перевода: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка при переводе.")


# А эта баны))
def add_to_blacklist(user_id, username, first_name, last_name, reason):
    conn = sqlite3.connect('banned_users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO banned_users (user_id, username, first_name, last_name, reason)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, reason))
    
    conn.commit()
    conn.close()

# проверка на еблана
def is_user_banned(user_id):
    conn = sqlite3.connect('banned_users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    return user

# удаление еблана
def remove_from_blacklist(user_id):
    conn = sqlite3.connect('banned_users.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_member(message):
    for member in message.new_chat_members:
        banned_user = is_user_banned(member.id)
        if banned_user:
            try:
                # попытка бана еблана
                bot.ban_chat_member(
                    chat_id=message.chat.id,
                    user_id=member.id
                )
                
                # ебааать отправка
                reason = banned_user[4] or "Причина не указана"
                ban_message = (
                    f"🚨 Пользователь {member.first_name} (@{member.username}) "
                    f"был забанен, т.к находится в базе бота.\n"
                    f"Причина бана: {reason}\n"
                    f"ID юзера: {member.id}"
                )
                
                # Отправляем сообщение и удаляем его через 30 секунд
                msg = bot.send_message(message.chat.id, ban_message)
                
            except Exception as e:
                error_msg = (
                    f"⚠️ Пользователь был обнаружен в базе пидарасиков. Мне не удалось забанить {member.first_name}.\n"
                    f"Ошибка: {str(e)} \n\n Скорее всего, бот не админ с правами бана :("
                )
                bot.send_message(message.chat.id, error_msg)
                # Отправляем уведомление админу
                bot.send_message(ADMIN_ID, error_msg + f"\nЧат: {message.chat.title}")

@bot.message_handler(commands=['addban'])
def add_ban(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Поешь говна гандон")
        return
    
    try:
        args = message.text.split(' ', 2)
        if len(args) < 3:
            bot.reply_to(message, "Используй: /addban user_id причина")
            return
            
        user_id = int(args[1])
        reason = args[2]
        
        try:
            # палучаем инфоо
            user_info = bot.get_chat(user_id)
        except telebot.apihelper.ApiTelegramException as e:
            if "chat not found" in str(e):
                # сасал
                add_to_blacklist(
                    user_id=user_id,
                    username="unknown",
                    first_name="Unknown",
                    last_name="",
                    reason=reason
                )
                bot.reply_to(message, f"Юзер с ID {user_id} добавлен в eblan-базу. Информация недоступна (он блокнул бота его нету в бд, итд).")
                return
            else:
                raise
        
        # сасал да
        add_to_blacklist(
            user_id=user_id,
            username=user_info.username or "unknown",
            first_name=user_info.first_name or "Unknown",
            last_name=user_info.last_name or "",
            reason=reason
        )
        
        bot.reply_to(message, f"Юзер {user_info.first_name} добавлен в eblan-базу.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

@bot.message_handler(commands=['checkban'])
def check_ban(message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = int(message.text.split()[1])
        except:
            bot.reply_to(message, "Ответь на сообщение, либо укажи ID")
            return
    
    user = is_user_banned(user_id)
    if user:
        bot.reply_to(message, f"✅ Юзер {user_id} в базе. \nПричина: {user[4]}")
    else:
        bot.reply_to(message, f"❌ Юзер {user_id} не находится в eblan-базе. \n Для предложения юзера, обратитесь в чат бота")


@bot.message_handler(commands=['removeban'])
def remove_ban(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "говноед иди нахуй")
        return
    
    try:
        # Формат команды: /removeban user_id
        args = message.text.split(' ', 1)
        if len(args) < 2:
            bot.reply_to(message, "Юзай: /removeban user_id, еблан")
            return
            
        user_id = int(args[1])
        remove_from_blacklist(user_id)
        bot.reply_to(message, f"Юзер {user_id} удален из БД ебланов.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['listbanned'])
def list_banned(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "вай сынша лавы")
        return
    
    conn = sqlite3.connect('banned_users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM banned_users')
    banned_users = cursor.fetchall()
    
    conn.close()
    
    if not banned_users:
        bot.reply_to(message, "В базе пусто.")
        return
    
    response = "Все пользователи в базе ебланов:\n\n"
    for user in banned_users:
        response += f"ID: {user[0]}, Имя: {user[2]} {user[3]}, @{user[1]}, Причина: {user[4]}\n"
    
    bot.reply_to(message, response)


# расшифровка гс
def convert_ogg_to_wav(ogg_audio):
    """Конвертирует аудио в формат WAV для обработки"""
    audio = AudioSegment.from_ogg(BytesIO(ogg_audio))
    wav_audio = BytesIO()
    audio.export(wav_audio, format='wav')
    wav_audio.seek(0)
    return wav_audio

def transcribe_locally(audio_file_path):
    """Расшифровывает аудио локально с помощью SpeechRecognition"""
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(audio_file_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language='ru-RU')
            return text
        except sr.UnknownValueError:
            return "Не удалось распознать речь"
        except sr.RequestError as e:
            return f"Ошибка сервиса распознавания: {e}"

@bot.message_handler(commands=['voice'])
def handle_voice_command(message):
    """Обрабатывает команду /voice в ответ на голосовое сообщение"""
    if not message.reply_to_message or not message.reply_to_message.voice:
        bot.reply_to(message, "ℹ️ Команду /voice необходимо использовать в ответ на голосовое")
        return
    
    # проверка длины гс
    if message.reply_to_message.voice.duration > MAX_VOICE_DURATION:
        bot.reply_to(message, f"⚠️ Сообщение слишком длинное, максимальная длительность: {MAX_VOICE_DURATION} секунд.")
        return
    
    try:
        processing_msg = bot.reply_to(message.reply_to_message, "⏳ Расшифровка...")
        
        file_info = bot.get_file(message.reply_to_message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp_ogg:
            tmp_ogg.write(downloaded_file)
            tmp_ogg_path = tmp_ogg.name
        
        wav_audio = convert_ogg_to_wav(downloaded_file)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
            tmp_wav.write(wav_audio.getvalue())
            tmp_wav_path = tmp_wav.name
        
        # сама расшифровка
        text = transcribe_locally(tmp_wav_path)
        
        # удаление гс из файлов
        try:
            os.unlink(tmp_ogg_path)
            os.unlink(tmp_wav_path)
        except Exception as e:
            print(f"Ошибка при удалении временных файлов: {e}")
        
        bot.edit_message_text(
            chat_id=processing_msg.chat.id,
            message_id=processing_msg.message_id,
            text=f"🔊 Расшифровка: {text}"
        )
        
    except Exception as e:
        if 'tmp_ogg_path' in locals() and os.path.exists(tmp_ogg_path):
            os.unlink(tmp_ogg_path)
        if 'tmp_wav_path' in locals() and os.path.exists(tmp_wav_path):
            os.unlink(tmp_wav_path)
        
        bot.reply_to(message, f"⚠️ Произошла ошибка при обработке: {str(e)}")


# ы
init_db()

# Запуск нах
if __name__ == "__main__":
    logging.info("Запуск бота...")
    print("Бот запущен, и готов к работе.") 
    try:
        bot.polling(none_stop=True, timeout=60)
        updater.idle()
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        print(f"Ошибка при запуске бота: {e}") 