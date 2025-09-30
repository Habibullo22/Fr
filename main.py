import telebot
from telebot import types
import json
import os

BOT_TOKEN = "8198002913:AAH_yu2FEag3GMeHLYDy-s7x-1jzjHLxrrU"
ADMIN_ID = 5815294733
CARD_NUMBER = "9860 6067 5024 7151"

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "bot_data.json"

# ---------------- Data yuklash / saqlash ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                # ensure keys exist
                return d.get("users", {}), d.get("orders", {})
        except Exception as e:
            print("Data load error:", e)
            return {}, {}
    return {}, {}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": users, "orders": orders}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Data save error:", e)

# load on start
users, orders = load_data()
# users structure:
# users = { "<user_id>": {"balance": int, "almaz": [packages], "ref_by": "<user_id>|None", "referrals": [user_id,...]} }
# orders = { "<user_id>": [ { "order_id": int, "ff_id": str, "package": str, "status": str } ] }

# Ensure existing users have the needed fields
for uid, u in list(users.items()):
    if "balance" not in u: u["balance"] = 0
    if "almaz" not in u: u["almaz"] = []
    if "ref_by" not in u: u["ref_by"] = None
    if "referrals" not in u: u["referrals"] = []

# ---------------- Voucher paketlari ----------------
voucher_packages = {
    "💳 Haftalik Lite [90💎] – 9,000 so‘m": 9000,
    "💳 Haftalik [450💎] – 21,000 so‘m": 21000,
    "💳 Oylik [2600💎] – 135,000 so‘m": 135000,
    "💎 LvL Up [1270💎] – 67,000 so‘m": 67000
}

# ---------------- Helper funksiyalar ----------------
def ensure_user(user_id):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"balance": 0, "almaz": [], "ref_by": None, "referrals": []}
        save_data()
    return users[uid]

def next_order_id_for(user_id):
    uid = str(user_id)
    user_orders = orders.get(uid, [])
    return len(user_orders) + 1

def add_order(user_id, ff_id, package_name):
    uid = str(user_id)
    if uid not in orders:
        orders[uid] = []
    order_id = next_order_id_for(user_id)
    orders[uid].append({
        "order_id": order_id,
        "ff_id": ff_id,
        "package": package_name,
        "status": "Jarayonda"
    })
    save_data()
    return order_id

def find_order(user_id, order_id):
    uid = str(user_id)
    for o in orders.get(uid, []):
        if o.get("order_id") == order_id:
            return o
    return None

# ---------------- Main menu ----------------
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💎 Almaz sotib olish", "💎 Vavucher sotib olish")
    markup.add("💳 Hisob to‘ldirish", "💳 Balance")
    markup.add("🛒 Mening almazim", "👥 Referal")
    if user_id == ADMIN_ID:
        markup.add("⚙ Sozlamalar")
    return markup

# ---------------- Start ----------------
@bot.message_handler(commands=["start"])
def start(message):
    args = message.text.split()
    user_id = message.chat.id
    uid = str(user_id)
    ensure_user(user_id)

    # referal xabar: /start <ref_id>
    if len(args) > 1:
        ref = args[1]
        # only accept numeric ids
        try:
            ref_id = int(ref)
            ref_uid = str(ref_id)
            if ref_uid != uid and users[uid]["ref_by"] is None and ref_uid in users:
                # set referrer
                users[uid]["ref_by"] = ref_uid
                # add to referrals list if not already
                if uid not in users[ref_uid].get("referrals", []):
                    users[ref_uid].setdefault("referrals", []).append(uid)
                    # give bonus once
                    users[ref_uid]["balance"] = users[ref_uid].get("balance", 0) + 500
                    bot.send_message(ref_id, f"🎉 Yangi referal qo‘shildi! +500 so‘m balansingizga qo‘shildi.")
                save_data()
        except:
            pass

    ensure_user(user_id)
    bot.send_message(user_id,
                     "👋 Assalomu alekum! Free Fire almaz servisga hush kelibsiz.\nDo‘stlaringizni taklif qiling va bonus oling!",
                     reply_markup=main_menu(user_id))
    # send user's referral link
    try:
        bot.send_message(user_id, f"🔗 Sizning referal linkingiz:\nhttps://t.me/{bot.get_me().username}?start={user_id}")
    except Exception:
        pass

# ---------------- Referal menyusi ----------------
@bot.message_handler(func=lambda m: m.text == "👥 Referal")
def referral_menu(message):
    user_id = message.chat.id
    uid = str(user_id)
    ensure_user(user_id)
    user = users[uid]
    ref_by = user.get("ref_by")
    referrals = user.get("referrals", [])
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(user_id,
        f"👥 Sizning referal linkingiz:\n{link}\n\n"
        f"📊 Referallar soni: {len(referrals)} ta\n"
        f"💰 Balansingiz: {user.get('balance',0)} so‘m\n"
        f"👤 Sizni kim taklif qilgan: {ref_by if ref_by else 'Hech kim'}"
    )

# ---------------- Voucher menyusi ----------------
@bot.message_handler(func=lambda m: m.text == "💎 Vavucher sotib olish")
def voucher_menu(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for pkg in voucher_packages.keys():
        markup.add(pkg)
    markup.add("⬅️ Ortga qaytish")
    bot.send_message(message.chat.id, "Qaysi voucher paketini sotib olasiz?", reply_markup=markup)

# ---------------- Voucher sotib olish ----------------
@bot.message_handler(func=lambda m: m.text in voucher_packages.keys())
def buy_voucher(message):
    user_id = message.chat.id
    uid = str(user_id)
    ensure_user(user_id)
    package_name = message.text
    price = voucher_packages[package_name]

    if users[uid]["balance"] < price:
        bot.send_message(user_id, f"❌ Balansingiz yetarli emas ({price} so‘m kerak).")
        return

    msg = bot.send_message(user_id, "🆔 Free Fire IDingizni kiriting:")
    bot.register_next_step_handler(msg, lambda m: process_voucher_order(m, package_name, price))

def process_voucher_order(message, package_name, price):
    user_id = message.chat.id
    uid = str(user_id)
    ff_id = message.text.strip()
    ensure_user(user_id)

    # Balansdan yechish
    users[uid]["balance"] = users[uid].get("balance",0) - price
    # Add order
    order_id = add_order(user_id, ff_id, package_name)

    # Adminga xabar (inline)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_voucher_{uid}_{order_id}"))
    markup.add(types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_voucher_{uid}_{order_id}"))

    bot.send_message(ADMIN_ID,
                     f"💳 Voucher buyurtma:\n🆔 UserID: {user_id}\nFree Fire ID: {ff_id}\nPaket: {package_name}\nNarx: {price} so‘m\nStatus: Jarayonda",
                     reply_markup=markup)
    bot.send_message(user_id, f"✅ Voucher buyurtma qabul qilindi!\n{package_name}\nStatus: Jarayonda")
    save_data()

# ---------------- Almaz menyusi ----------------
@bot.message_handler(func=lambda m: m.text == "💎 Almaz sotib olish")
def almaz_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        "💎 105 Almaz – 13,250 so‘m", "💎 326 Almaz – 40,000 so‘m",
        "💎 546 Almaz – 65,000 so‘m", "💎 1113 Almaz – 131,250 so‘m",
        "💎 2398 Almaz – 262,500 so‘m", "💎 6160 Almaz – 650,000 so‘m"
    )
    markup.add("⬅️ Ortga qaytish")
    bot.send_message(message.chat.id, "Qaysi paketni sotib olasiz?", reply_markup=markup)

# ---------------- Almaz sotib olish ----------------
@bot.message_handler(func=lambda m: "Almaz" in m.text and "💎" in m.text)
def buy_almaz(message):
    user_id = message.chat.id
    uid = str(user_id)
    ensure_user(user_id)

    price_text = message.text.split("–")[-1].replace("so‘m","").replace(",","").strip()
    try:
        price = int(price_text)
    except:
        bot.send_message(user_id, "❌ Paket narxini aniqlashda xatolik.")
        return

    if users[uid]["balance"] < price:
        bot.send_message(user_id, "❌ Balansingiz yetarli emas. Iltimos, avval hisob to‘ldiring.")
        return

    msg = bot.send_message(user_id, "🆔 Free Fire IDingizni kiriting:")
    bot.register_next_step_handler(msg, lambda m: process_almaz_order(m, message.text, price))

def process_almaz_order(message, package_name, price):
    user_id = message.chat.id
    uid = str(user_id)
    ff_id = message.text.strip()
    ensure_user(user_id)

    users[uid]["balance"] = users[uid].get("balance",0) - price
    order_id = add_order(user_id, ff_id, package_name)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_admin_{uid}_{order_id}"))
    markup.add(types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_admin_{uid}_{order_id}"))

    bot.send_message(ADMIN_ID,
                     f"🆔 UserID: {user_id}\nFree Fire ID: {ff_id}\nPaket: {package_name}\nNarx: {price} so‘m\nStatus: Jarayonda",
                     reply_markup=markup)
    bot.send_message(user_id, f"✅ Buyurtma qabul qilindi!\n{package_name}\nStatus: Jarayonda")
    save_data()

# ---------------- Mening almazim va balans ----------------
@bot.message_handler(func=lambda m: m.text == "🛒 Mening almazim")
def my_orders(message):
    user_id = message.chat.id
    uid = str(user_id)
    user_orders = orders.get(uid, [])
    if not user_orders:
        bot.send_message(user_id, "Sizda buyurtmalar yo‘q.")
        return
    text = "📋 Sizning buyurtmalaringiz:\n\n"
    for o in user_orders:
        text += f"🆔 Order ID: {o['order_id']}\nPaket: {o['package']}\nFree Fire ID: {o.get('ff_id','')}\nStatus: {o['status']}\n\n"
    bot.send_message(user_id, text)

@bot.message_handler(func=lambda m: m.text == "💳 Balance")
def show_balance(message):
    user_id = message.chat.id
    uid = str(user_id)
    ensure_user(user_id)
    bot.send_message(user_id, f"💰 Sizning balansingiz: {users[uid].get('balance',0)} so‘m")

# ---------------- Hisob to‘ldirish (deposit) ----------------
@bot.message_handler(func=lambda m: m.text == "💳 Hisob to‘ldirish")
def deposit(message):
    user_id = message.chat.id
    ensure_user(user_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("⬅️ Ortga qaytish")
    msg = bot.send_message(user_id, "💳 Summani kiriting (10,000 – 10,000,000 so‘m):", reply_markup=markup)
    bot.register_next_step_handler(msg, process_deposit)

def process_deposit(message):
    user_id = message.chat.id
    if message.text == "⬅️ Ortga qaytish":
        bot.send_message(user_id, "⬅️ Asosiy menyuga qaytdingiz.", reply_markup=main_menu(user_id))
        return
    try:
        amount = int(message.text)
        if amount < 10000 or amount > 10000000:
            bot.send_message(user_id, "❌ Noto‘g‘ri summa. Qayta urinib ko‘ring.")
            deposit(message)
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ To‘lov qildim", callback_data=f"paid_{user_id}_{amount}"))
        bot.send_message(user_id, f"💳 To‘lov uchun karta:\n{CARD_NUMBER}\n💰 Summa: {amount} so‘m", reply_markup=markup)
    except:
        bot.send_message(user_id, "❌ Iltimos, faqat raqam kiriting.")
        deposit(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def paid_callback(call):
    # callback data format: paid_<user_id>_<amount>
    parts = call.data.split("_")
    if len(parts) != 3:
        bot.answer_callback_query(call.id, "❌ Noto‘g‘ri ma'lumot.")
        return
    _, uid_str, amount_str = parts
    user_id = int(uid_str)
    amount = int(amount_str)
    bot.send_message(call.message.chat.id, "✅ To‘lovni tasdiqlash uchun chek rasm yuboring:")
    bot.register_next_step_handler(call.message, lambda m: send_check(m, user_id, amount))

def send_check(message, user_id, amount):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Faqat rasm yuboring (chek skrinshot).")
        return
    file_id = message.photo[-1].file_id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_deposit_{user_id}_{amount}"))
    markup.add(types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_deposit_{user_id}_{amount}"))
    bot.send_photo(ADMIN_ID, file_id, caption=f"💳 Yangi to‘lov:\n🆔 UserID: {user_id}\n💰 Summa: {amount} so‘m", reply_markup=markup)
    bot.send_message(message.chat.id, "✅ Chek yuborildi, admin tasdiqlashini kuting.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_deposit") or call.data.startswith("reject_deposit"))
def confirm_reject_deposit(call):
    parts = call.data.split("_")
    if len(parts) != 4:
        bot.answer_callback_query(call.id, "❌ Noto‘g‘ri ma'lumot.")
        return
    action = parts[0] + "_" + parts[1]  # confirm_deposit or reject_deposit
    user_id = int(parts[2])
    amount = int(parts[3])

    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Siz admin emassiz!")
        return

    uid = str(user_id)
    ensure_user(user_id)

    if action == "confirm_deposit":
        users[uid]["balance"] = users[uid].get("balance",0) + amount
        save_data()
        bot.send_message(user_id, f"✅ To‘lov tasdiqlandi! {amount} so‘m balansingizga qo‘shildi.")
        bot.send_message(ADMIN_ID, f"✅ UserID {user_id} balansiga {amount} so‘m qo‘shildi.")
        bot.answer_callback_query(call.id, "✅ Tasdiqladingiz.")
    else:
        bot.send_message(user_id, "❌ To‘lov rad etildi. Qayta urinib ko‘ring.")
        bot.send_message(ADMIN_ID, f"❌ UserID {user_id} to‘lovi rad etildi.")
        bot.answer_callback_query(call.id, "❌ Rad etdiniz.")

# ---------------- Admin menyusi ----------------
@bot.message_handler(func=lambda m: m.text == "⚙ Sozlamalar")
def settings_menu(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📰 Reklama yuborish", "📋 Buyurtmalar")
    markup.add("📊 Statistika", "👥 Foydalanuvchilar")
    markup.add("⬅️ Ortga qaytish")
    bot.send_message(message.chat.id, "⚙ Sozlamalar menyusi:", reply_markup=markup)

# ---------------- Reklama yuborish ----------------
@bot.message_handler(func=lambda m: m.text == "📰 Reklama yuborish" and m.chat.id == ADMIN_ID)
def send_news(message):
    msg = bot.send_message(message.chat.id, "📰 Reklama matnini yoki rasm + matn yuboring:")
    bot.register_next_step_handler(msg, process_news)

def process_news(message):
    for uid in list(users.keys()):
        try:
            if message.photo:
                bot.send_photo(int(uid), message.photo[-1].file_id, caption=message.caption)
            else:
                bot.send_message(int(uid), message.text)
        except:
            pass
    bot.send_message(ADMIN_ID, "✅ Reklama yuborildi!")

# ---------------- Buyurtmalarni ko‘rish (admin) ----------------
@bot.message_handler(func=lambda m: m.text == "📋 Buyurtmalar" and m.chat.id == ADMIN_ID)
def show_orders(message):
    if not orders:
        bot.send_message(ADMIN_ID, "📋 Hali buyurtmalar yo‘q.")
        return
    for user_id, user_orders in orders.items():
        for o in user_orders:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_admin_{user_id}_{o['order_id']}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_admin_{user_id}_{o['order_id']}")
            )
            bot.send_message(
                ADMIN_ID,
                f"👤 UserID: {user_id}\n🆔 Order ID: {o['order_id']}\nFree Fire ID: {o.get('ff_id','')}\nPaket: {o['package']}\nStatus: {o['status']}",
                reply_markup=markup
            )

# ---------------- Statistika (admin) ----------------
@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.chat.id == ADMIN_ID)
def statistics(message):
    total_users = len(users)
    total_balance = sum(u.get("balance",0) for u in users.values())
    total_orders = sum(len(v) for v in orders.values())
    bot.send_message(ADMIN_ID,
        f"📊 Statistika:\n\nFoydalanuvchilar: {total_users}\nUmumiy balans: {total_balance} so‘m\nJami buyurtmalar: {total_orders}")

# ---------------- Foydalanuvchilar ro'yxati (admin) ----------------
@bot.message_handler(func=lambda m: m.text == "👥 Foydalanuvchilar" and m.chat.id == ADMIN_ID)
def users_list(message):
    lines = []
    for uid, u in users.items():
        lines.append(f"ID: {uid} | Balans: {u.get('balance',0)} | Referallar: {len(u.get('referrals',[]))}")
    # bo'lsa uzun bo'lsa faylga yozamiz
    text = "\n".join(lines)
    if len(text) < 4000:
        bot.send_message(ADMIN_ID, "👥 Foydalanuvchilar:\n\n" + text)
    else:
        # agar juda uzun bo'lsa, fayl sifatida yuborish
        fname = "users_list.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(text)
        with open(fname, "rb") as f:
            bot.send_document(ADMIN_ID, f)
        os.remove(fname)

# ---------------- Admin tasdiqlash / rad etish (almaz) ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_admin") or call.data.startswith("reject_admin"))
def admin_confirm_reject(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Siz admin emassiz!")
        return

    parts = call.data.split("_")
    if len(parts) < 4:
        bot.answer_callback_query(call.id, "❌ Noto'g'ri ma'lumot.")
        return

    action = parts[0]  # confirm_admin or reject_admin
    user_id = parts[2]
    order_id = int(parts[3])

    order = find_order(user_id, order_id)
    if not order:
        bot.answer_callback_query(call.id, "❌ Buyurtma topilmadi.")
        return

    if order["status"] in ["Bajarildi", "Rad etildi"]:
        bot.answer_callback_query(call.id, "❌ Bu buyurtma allaqachon ishlangan!")
        return

    # narxni paketdan olish (agar paket voucher yoki almaz formatida bo'lsa)
    price_text = order["package"].split("–")[-1].replace("so‘m","").replace(",","").strip()
    try:
        price = int(price_text)
    except:
        # agar voucher nomida bo'lsa dictionarydan tekshirish
        price = voucher_packages.get(order["package"], 0)

    uid = str(user_id)
    ensure_user(user_id)

    if action == "confirm":
        order["status"] = "Bajarildi"
        # foydalanuvchining almazlariga qo'shamiz (soddalashtirilgan)
        users[uid].setdefault("almaz", []).append(order["package"])
        save_data()
        bot.send_message(int(uid), f"✅ Buyurtmangiz bajarildi! {order['package']} sizning almazingizga tushdi.")
        bot.answer_callback_query(call.id, "✅ Tasdiqladingiz.")
    else:
        order["status"] = "Rad etildi"
        users[uid]["balance"] = users[uid].get("balance",0) + price
        save_data()
        bot.send_message(int(uid), f"❌ Buyurtmangiz rad etildi. {price} so‘m balansingizga qaytarildi.")
        bot.answer_callback_query(call.id, "❌ Rad etdiniz.")

# ---------------- Admin tasdiqlash / rad etish (voucher) ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_voucher") or call.data.startswith("reject_voucher"))
def admin_confirm_reject_voucher(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Siz admin emassiz!")
        return

    parts = call.data.split("_")
    if len(parts) < 3:
        bot.answer_callback_query(call.id, "❌ Noto'g'ri ma'lumot.")
        return

    # format: confirm_voucher_<uid>_<order_id>
    action = parts[0]
    user_id = parts[2]
    order_id = int(parts[3]) if len(parts) > 3 else None

    order = find_order(user_id, order_id)
    if not order:
        bot.answer_callback_query(call.id, "❌ Buyurtma topilmadi.")
        return

    if order["status"] in ["Bajarildi", "Rad etildi"]:
        bot.answer_callback_query(call.id, "❌ Bu buyurtma allaqachon ishlangan!")
        return

    # try to get price
    price_val = voucher_packages.get(order["package"], 0)
    uid = str(user_id)
    ensure_user(user_id)

    if action == "confirm_voucher":
        order["status"] = "Bajarildi"
        save_data()
        bot.send_message(int(uid), f"✅ Buyurtmangiz bajarildi! {order['package']} sizga yetkazildi.")
        bot.answer_callback_query(call.id, "✅ Tasdiqladingiz.")
    else:
        order["status"] = "Rad etildi"
        users[uid]["balance"] = users[uid].get("balance",0) + price_val
        save_data()
        bot.send_message(int(uid), f"❌ Buyurtmangiz rad etildi. {price_val} so‘m balansingizga qaytarildi.")
        bot.answer_callback_query(call.id, "❌ Rad etdiniz.")

# ---------------- Ortga qaytish ----------------
@bot.message_handler(func=lambda m: m.text == "⬅️ Ortga qaytish")
def back_to_menu(message):
    bot.send_message(message.chat.id, "⬅️ Asosiy menyuga qaytdingiz.", reply_markup=main_menu(message.chat.id))

# ---------------- Bot start ----------------
print("🤖 Bot ishga tushdi...")
bot.polling(none_stop=True)
