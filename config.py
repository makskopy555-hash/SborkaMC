import os

# === Обязательные переменные окружения (задаются в Railway) ===

# Токен бота от @BotFather
BOT_TOKEN = os.environ["8624909808:AAFpgTkXdGBTYhkKbbn-DQfZgj2hFZippcE"]

# Публичный канал VexWorld, на который нужно подписаться.
# Можно указать юзернейм (@VexWorld1) или числовой id канала.
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@VexWorld1")

# ID приватного канала со сборками (куда бот выдаёт доступ по подписке).
# Это ЧИСЛО вида -1001234567890, а не ссылка-приглашение.
# Как получить — см. README.md, раздел "Как узнать SHOP_CHANNEL_ID".
SHOP_CHANNEL_ID = int(os.environ["SHOP_CHANNEL_ID"])

# === Необязательные настройки (есть значения по умолчанию) ===

# Сколько Stars стоит подписка
PRICE_STARS = int(os.environ.get("PRICE_STARS", "50"))

# На сколько дней выдаётся доступ за одну оплату
SUB_DAYS = int(os.environ.get("SUB_DAYS", "30"))

# Юзернейм/ссылка для связи с тех. поддержкой (чисто для текста, можно не менять)
SUPPORT_CONTACT = os.environ.get("SUPPORT_CONTACT", "@your_support_username")

# Путь к файлу базы данных SQLite
DB_PATH = os.environ.get("DB_PATH", "vexworld.db")
