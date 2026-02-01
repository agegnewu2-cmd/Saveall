import sqlite3
import telebot
import os
import time
import datetime
import kvsqlite
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import requests
from bs4 import BeautifulSoup
import io
import re
import json
from threading import Thread
import schedule
from datetime import datetime as dt

TOKEN = "8306373981:AAG3SJLs6_rXoTrGjwasIkHZh1QKwSIQM30"
ADMIN_IDS = [7214891796, 7211991799]  # New admin IDs
MAIN_CHANNEL = "@Elabcode"
SUPPORT_CHANNEL = "@Elabsupport"
SMM_CHANNEL = "@Agesmm"
LOG_CHANNEL = -1003452186867

BOT_NAME = "Save All Bot"
BOT_USERNAME = "save_all_downloader_bot"

bot = telebot.TeleBot(TOKEN, num_threads=50, skip_pending=True)
db = kvsqlite.sync.Client('users.sqlite', 'users')
user_states = {}
download_queues = {}

# Initialize database
if not db.exists("banned_users"): db.set("banned_users", [])
if not db.exists("force_subscribe_channels"): db.set("force_subscribe_channels", [])
if not db.exists("user_ids"): db.set("user_ids", [])
if not db.exists("groups"): db.set("groups", {})
if not db.exists("daily_stats"): db.set("daily_stats", {})
if not db.exists("download_logs"): db.set("download_logs", [])
if not db.exists("settings"): db.set("settings", {
    "maintenance": False,
    "max_file_size": 50,
    "quality_default": "hd",
    "watermark_removal": True
})

LANGUAGES = {
    'ar': {
        'bot_title': f"🤖 {BOT_NAME} - محمّل الوسائط",
        'welcome': f"""
🌟 **مرحباً بك في {BOT_NAME}!** 🌟

📥 **بوت التحميل الذكي من جميع المنصات:**
• 📹 يوتيوب (فيديو/صوت)
• 📸 إنستغرام (ريلز/قصص)
• 📘 فيسبوك/تويتر/تيك توك
• 📌 بينتريست والمزيد

⚡ **مميزاتنا:**
• جودة عالية تصل إلى 4K
• دعم 24/7
• سرعة فائقة في التحميل
• إزالة العلامات المائية
• دعم المجموعات
• واجهة سهلة الاستخدام

📢 **القناة الرسمية:** {MAIN_CHANNEL}
💬 **الدعم الفني:** {SUPPORT_CHANNEL}
        """,
        'banned': "🚫 تم حظرك من استخدام البوت.",
        'subscribe_first': f"""
📢 **يجب الاشتراك أولاً!**

للاستمرار، اشترك في قناتنا:
{MAIN_CHANNEL}

⚡ بعد الاشتراك، اضغط على:
✅ **لقد اشتركت**
        """,
        'searching': "🔍 **جارٍ تحليل الرابط...**",
        'downloading': "⬇️ **جارٍ التحميل...**",
        'processing': "⚙️ **جارٍ المعالجة...**",
        'error_general': "❌ حدث خطأ، حاول مرة أخرى.",
        'error_link': "❌ رابط غير صحيح أو غير مدعوم.",
        'success': "✅ **تم التحميل بنجاح!**",
        'how_to_use_button': "📖 طريقة الاستخدام",
        'change_lang_button': "🌐 تغيير اللغة",
        'my_stats': "📊 إحصائياتي",
        'add_group': "➕ أضف للجروب",
        'support': "💬 الدعم الفني",
        'donate': "💰 دعم البوت",
        'quality_menu': "🎬 اختر الجودة",
        'how_to_use_text': f"""
📚 **دليل استخدام {BOT_NAME}:**

📥 **طرق التحميل:**
1. أرسل الرابط مباشرة للبوت
2. استخدم الأمر: /d رابط
3. في الجروبات: /download رابط

🌐 **المنصات المدعومة:**
🎬 **YouTube** - فيديو/صوت بجودة عالية
📸 **Instagram** - ريلز/قصص/منشورات
📘 **Facebook** - فيديوهات/ريلز
🎵 **TikTok** - فيديوهات/صوتيات
🐦 **Twitter/X** - فيديوهات
📌 **Pinterest** - فيديوهات
👻 **Snapchat** - ستوريات
📱 **Reddit** - فيديوهات

⚡ **المميزات المتقدمة:**
• جودة 4K/1080p/720p
• تحميل الصوت منفصلاً
• إزالة العلامة المائية
• دعم المجموعات
• واجهة متعددة اللغات
• سجل التحميلات

🔧 **الأوامر المتاحة:**
/start - بدء البوت
/stats - إحصائياتك
/settings - الإعدادات
/admin - لوحة التحكم (للمشرفين)

💬 **الدعم:** {SUPPORT_CHANNEL}
📢 **القناة:** {MAIN_CHANNEL}
        """,
        'back_button': "🔙 رجوع",
        'choose_lang': "🌐 **اختر لغتك المفضلة:**",
        'lang_changed': "✅ تم تغيير اللغة بنجاح!",
        'my_stats_text': """
📊 **إحصائياتك الشخصية:**

• 📥 **التحميلات:** {downloads}
• ⭐ **الجودة المفضلة:** {quality}
• 📅 **تاريخ الانضمام:** {join_date}
• 🕒 **النشاط الأخير:** {last_active}
• 🌐 **اللغة:** {language}

📈 **المستوى:** {level}
        """,
        'stats_downloads': "التحميلات",
        'stats_quality': "الجودة",
        'stats_since': "تاريخ الانضمام",
        'admin_panel': """
👑 **لوحة التحكم الإدارية**

⚡ **البوت:** {bot_name}
👥 **المستخدمون:** {total_users}
📥 **التحميلات:** {total_downloads}
🚫 **المحظورون:** {banned_users}

🔧 **اختر الإجراء:**
        """,
        'group_welcome': f"""
🌟 **مرحباً! أنا {BOT_NAME}** 🌟

📥 يمكنني تحميل الوسائط من:
• يوتيوب، إنستغرام، فيسبوك
• تيك توك، تويتر، بينتريست

⚡ **كيفية الاستخدام:**
1. أرسل رابطاً مباشرةً
2. أو استخدم: /d رابط

📢 **القناة:** {MAIN_CHANNEL}
💬 **الدعم:** {SUPPORT_CHANNEL}
        """,
        'bot_added': f"""
✅ **تمت إضافة البوت بنجاح!**

⚡ **الأوامر المتاحة:**
/d رابط - للتحميل
/stats - للإحصائيات
/settings - للإعدادات

📢 **القناة:** {MAIN_CHANNEL}
💬 **الدعم:** {SUPPORT_CHANNEL}
        """,
        'audio_button': "🎵 تحميل الصوت",
        'video_button': "📹 تحميل الفيديو",
        'quality_hd': "🔵 عالية (HD)",
        'quality_sd': "🟢 متوسطة (SD)",
        'quality_audio': "🎵 صوت فقط",
        'download_complete': """
✅ **تم التحميل بنجاح!**

📁 **الملف:** {title}
🌐 **المنصة:** {platform}
⚡ **الجودة:** {quality}
📊 **الحجم:** {size}

💬 **الدعم:** {SUPPORT_CHANNEL}
        """,
        'no_audio': "❌ لا يوجد صوت متاح",
        'select_quality': "🎬 **اختر جودة التحميل:**",
        'select_format': "📁 **اختر نوع الملف:**",
    },
    'en': {
        'bot_title': f"🤖 {BOT_NAME} - Media Downloader",
        'welcome': f"""
🌟 **Welcome to {BOT_NAME}!** 🌟

📥 **Smart Downloader from All Platforms:**
• 📹 YouTube (video/audio)
• 📸 Instagram (reels/stories)
• 📘 Facebook/Twitter/TikTok
• 📌 Pinterest & more

⚡ **Our Features:**
• High quality up to 4K
• 24/7 Support
• Super fast downloads
• Watermark removal
• Group support
• User-friendly interface

📢 **Official Channel:** {MAIN_CHANNEL}
💬 **Technical Support:** {SUPPORT_CHANNEL}
        """,
        'banned': "🚫 You are banned from using this bot.",
        'subscribe_first': f"""
📢 **Subscription Required!**

To continue, subscribe to our channel:
{MAIN_CHANNEL}

⚡ After subscribing, click:
✅ **I've Subscribed**
        """,
        'searching': "🔍 **Analyzing link...**",
        'downloading': "⬇️ **Downloading...**",
        'processing': "⚙️ **Processing...**",
        'error_general': "❌ An error occurred, please try again.",
        'error_link': "❌ Invalid or unsupported link.",
        'success': "✅ **Downloaded Successfully!**",
        'how_to_use_button': "📖 How to Use",
        'change_lang_button': "🌐 Change Language",
        'my_stats': "📊 My Stats",
        'add_group': "➕ Add to Group",
        'support': "💬 Support",
        'donate': "💰 Donate",
        'quality_menu': "🎬 Quality Options",
        'how_to_use_text': f"""
📚 **{BOT_NAME} User Guide:**

📥 **Download Methods:**
1. Send link directly to bot
2. Use command: /d link
3. In groups: /download link

🌐 **Supported Platforms:**
🎬 **YouTube** - video/audio high quality
📸 **Instagram** - reels/stories/posts
📘 **Facebook** - videos/reels
🎵 **TikTok** - videos/audio
🐦 **Twitter/X** - videos
📌 **Pinterest** - videos
👻 **Snapchat** - stories
📱 **Reddit** - videos

⚡ **Advanced Features:**
• 4K/1080p/720p quality
• Separate audio download
• Watermark removal
• Group support
• Multi-language interface
• Download history

🔧 **Available Commands:**
/start - Start bot
/stats - Your statistics
/settings - Settings
/admin - Control panel (admins)

💬 **Support:** {SUPPORT_CHANNEL}
📢 **Channel:** {MAIN_CHANNEL}
        """,
        'back_button': "🔙 Back",
        'choose_lang': "🌐 **Choose Your Language:**",
        'lang_changed': "✅ Language changed successfully!",
        'my_stats_text': """
📊 **Your Personal Statistics:**

• 📥 **Downloads:** {downloads}
• ⭐ **Preferred Quality:** {quality}
• 📅 **Join Date:** {join_date}
• 🕒 **Last Active:** {last_active}
• 🌐 **Language:** {language}

📈 **Level:** {level}
        """,
        'stats_downloads': "Downloads",
        'stats_quality': "Quality",
        'stats_since': "Join Date",
        'admin_panel': """
👑 **Admin Control Panel**

⚡ **Bot:** {bot_name}
👥 **Users:** {total_users}
📥 **Downloads:** {total_downloads}
🚫 **Banned:** {banned_users}

🔧 **Select Action:**
        """,
        'group_welcome': f"""
🌟 **Hi! I'm {BOT_NAME}** 🌟

📥 I can download media from:
• YouTube, Instagram, Facebook
• TikTok, Twitter, Pinterest

⚡ **How to Use:**
1. Send link directly
2. Or use: /d link

📢 **Channel:** {MAIN_CHANNEL}
💬 **Support:** {SUPPORT_CHANNEL}
        """,
        'bot_added': f"""
✅ **Bot Added Successfully!**

⚡ **Available Commands:**
/d link - To download
/stats - For statistics
/settings - For settings

📢 **Channel:** {MAIN_CHANNEL}
💬 **Support:** {SUPPORT_CHANNEL}
        """,
        'audio_button': "🎵 Download Audio",
        'video_button': "📹 Download Video",
        'quality_hd': "🔵 High (HD)",
        'quality_sd': "🟢 Medium (SD)",
        'quality_audio': "🎵 Audio Only",
        'download_complete': """
✅ **Download Complete!**

📁 **File:** {title}
🌐 **Platform:** {platform}
⚡ **Quality:** {quality}
📊 **Size:** {size}

💬 **Support:** {SUPPORT_CHANNEL}
        """,
        'no_audio': "❌ No audio available",
        'select_quality': "🎬 **Select Download Quality:**",
        'select_format': "📁 **Select File Type:**",
    },
    'am': {
        'bot_title': f"🤖 {BOT_NAME} - ሜዲያ ማውረጃ",
        'welcome': f"""
🌟 **እንኳን ወደ {BOT_NAME} በደህና መጡ!** 🌟

📥 **ከሁሉም የማህበራዊ ሚዲያ ማውረድ:**
• 📹 YouTube (ቪዲዮ/ድምፅ)
• 📸 Instagram (ሪልስ/ስቶሪ)
• 📘 Facebook/Twitter/TikTok
• 📌 Pinterest እና ሌሎች

⚡ **የእኛ ባህሪያት:**
• ከፍተኛ ጥራት እስከ 4K
• 24/7 ድጋፍ
• ፈጣን ማውረጃ
• የውሃ ምልክት ማስወገድ
• ቡድን ድጋፍ
• ለተጠቃሚ ምቹ በይነገጽ

📢 **ይፋዊ ሰርጥ:** {MAIN_CHANNEL}
💬 **ቴክኒካል ድጋፍ:** {SUPPORT_CHANNEL}
        """,
        'banned': "🚫 ይህን ቦት መጠቀም ተከልክለዋል።",
        'subscribe_first': f"""
📢 **የመመዝገቢያ ግዴታ!**

ለመቀጠል፣ ወደ ሰርጣችን ይቀላቀሉ፡
{MAIN_CHANNEL}

⚡ ከመመዝገብ በኋላ፣ ይጫኑ፡
✅ **ተመዝግቤአለሁ**
        """,
        'searching': "🔍 **ማገናኛ በመተንተን ላይ...**",
        'downloading': "⬇️ **በማውረድ ላይ...**",
        'processing': "⚙️ **በማስተናገድ ላይ...**",
        'error_general': "❌ ስህተት ተከስቷል፣ እባክዎ እንደገና ይሞክሩ።",
        'error_link': "❌ የተሳሳተ ወይም የማይደገፍ ማገናኛ።",
        'success': "✅ **በሚገባ ተመርቷል!**",
        'how_to_use_button': "📖 አጠቃቀም መመሪያ",
        'change_lang_button': "🌐 ቋንቋ ቀይር",
        'my_stats': "📊 ስታትስቶቼ",
        'add_group': "➕ ለቡድን ጨምር",
        'support': "💬 ድጋፍ",
        'donate': "💰 ድጋፍ አድርግ",
        'quality_menu': "🎬 ጥራት አማራጮች",
        'how_to_use_text': f"""
📚 **{BOT_NAME} የተጠቃሚ መመሪያ:**

📥 **የማውረድ ዘዴዎች:**
1. ማገናኛን በቀጥታ ለቦት ይላኩ
2. ትእዛዙን ይጠቀሙ፡ /d ማገናኛ
3. በቡድኖች ውስጥ፡ /download ማገናኛ

🌐 **የሚደገፉ የማህበራዊ ሚዲያዎች:**
🎬 **YouTube** - ቪዲዮ/ድምፅ ከፍተኛ ጥራት
📸 **Instagram** - ሪልስ/ስቶሪ/ልጥፎች
📘 **Facebook** - ቪዲዮዎች/ሪልስ
🎵 **TikTok** - ቪዲዮዎች/ድምፅ
🐦 **Twitter/X** - ቪዲዮዎች
📌 **Pinterest** - ቪዲዮዎች
👻 **Snapchat** - ስቶሪዎች
📱 **Reddit** - ቪዲዮዎች

⚡ **የላቀ ባህሪያት:**
• 4K/1080p/720p ጥራት
• የድምፅ ማውረድ
• የውሃ ምልክት ማስወገድ
• ቡድን ድጋፍ
• ብዙ ቋንቋ በይነገጽ
• የማውረድ ታሪክ

🔧 **ሊገኙ የሚችሉ ትእዛዞች:**
/start - ቦትን ጀምር
/stats - የእርስዎ ስታትስቲክስ
/settings - ቅንብሮች
/admin - የአስተዳደር ፓነል (አስተዳዳሪዎች)

💬 **ድጋፍ:** {SUPPORT_CHANNEL}
📢 **ሰርጥ:** {MAIN_CHANNEL}
        """,
        'back_button': "🔙 ተመለስ",
        'choose_lang': "🌐 **ቋንቋዎን ይምረጡ:**",
        'lang_changed': "✅ ቋንቋ በሚገባ ተቀይሯል!",
        'my_stats_text': """
📊 **የእርስዎ ግላዊ ስታትስቲክስ:**

• 📥 **ማውረዶች:** {downloads}
• ⭐ **የተመረጠ ጥራት:** {quality}
• 📅 **የመግቢያ ቀን:** {join_date}
• 🕒 **የመጨረሻ እንቅስቃሴ:** {last_active}
• 🌐 **ቋንቋ:** {language}

📈 **ደረጃ:** {level}
        """,
        'group_welcome': f"""
🌟 **ሰላም! እኔ {BOT_NAME} ነኝ** 🌟

📥 ከሚከተሉት ማህበራዊ ሚዲያዎች ማውረድ እችላለሁ፡
• YouTube, Instagram, Facebook
• TikTok, Twitter, Pinterest

⚡ **አጠቃቀም:**
1. ማገናኛን በቀጥታ ይላኩ
2. ወይም ይጠቀሙ፡ /d ማገናኛ

📢 **ሰርጥ:** {MAIN_CHANNEL}
💬 **ድጋፍ:** {SUPPORT_CHANNEL}
        """,
        'bot_added': f"""
✅ **ቦት በሚገባ ተጨምሯል!**

⚡ **ሊገኙ የሚችሉ ትእዛዞች:**
/d ማገናኛ - ለማውረድ
/stats - ለስታትስቲክስ
/settings - ለቅንብሮች

📢 **ሰርጥ:** {MAIN_CHANNEL}
💬 **ድጋፍ:** {SUPPORT_CHANNEL}
        """,
        'audio_button': "🎵 ድምፅ አውርድ",
        'video_button': "📹 ቪዲዮ አውርድ",
        'quality_hd': "🔵 ከፍተኛ (HD)",
        'quality_sd': "🟢 መካከለኛ (SD)",
        'quality_audio': "🎵 ድምፅ ብቻ",
        'download_complete': """
✅ **ማውረድ ተጠናቋል!**

📁 **ፋይል:** {title}
🌐 **የማህበራዊ ሚዲያ:** {platform}
⚡ **ጥራት:** {quality}
📊 **መጠን:** {size}

💬 **ድጋፍ:** {SUPPORT_CHANNEL}
        """,
        'no_audio': "❌ ድምፅ የለም",
        'select_quality': "🎬 **የማውረድ ጥራት ይምረጡ:**",
        'select_format': "📁 **የፋይል አይነት ይምረጡ:**",
    },
    'ru': {
        'bot_title': f"🤖 {BOT_NAME} - Загрузчик Медиа",
        'welcome': f"""
🌟 **Добро пожаловать в {BOT_NAME}!** 🌟

📥 **Умный загрузчик со всех платформ:**
• 📹 YouTube (видео/аудио)
• 📸 Instagram (рилы/сторис)
• 📘 Facebook/Twitter/TikTok
• 📌 Pinterest и другие

⚡ **Наши возможности:**
• Высокое качество до 4K
• Поддержка 24/7
• Супер быстрая загрузка
• Удаление водяных знаков
• Поддержка групп
• Удобный интерфейс

📢 **Официальный канал:** {MAIN_CHANNEL}
💬 **Техподдержка:** {SUPPORT_CHANNEL}
        """,
        'banned': "🚫 Вы забанены в этом боте.",
        'subscribe_first': f"""
📢 **Требуется подписка!**

Чтобы продолжить, подпишитесь на наш канал:
{MAIN_CHANNEL}

⚡ После подписки нажмите:
✅ **Я подписался**
        """,
        'searching': "🔍 **Анализирую ссылку...**",
        'downloading': "⬇️ **Скачиваю...**",
        'processing': "⚙️ **Обрабатываю...**",
        'error_general': "❌ Произошла ошибка, попробуйте снова.",
        'error_link': "❌ Неверная или неподдерживаемая ссылка.",
        'success': "✅ **Успешно скачано!**",
        'how_to_use_button': "📖 Как использовать",
        'change_lang_button': "🌐 Сменить язык",
        'my_stats': "📊 Моя статистика",
        'add_group': "➕ Добавить в группу",
        'support': "💬 Поддержка",
        'donate': "💰 Поддержать бота",
        'quality_menu': "🎬 Качество загрузки",
        'how_to_use_text': f"""
📚 **Руководство пользователя {BOT_NAME}:**

📥 **Способы загрузки:**
1. Отправьте ссылку напрямую боту
2. Используйте команду: /d ссылка
3. В группах: /download ссылка

🌐 **Поддерживаемые платформы:**
🎬 **YouTube** - видео/аудио высокого качества
📸 **Instagram** - рилы/сторисы/посты
📘 **Facebook** - видео/рилы
🎵 **TikTok** - видео/аудио
🐦 **Twitter/X** - видео
📌 **Pinterest** - видео
👻 **Snapchat** - сторисы
📱 **Reddit** - видео

⚡ **Расширенные возможности:**
• Качество 4K/1080p/720p
• Отдельная загрузка аудио
• Удаление водяных знаков
• Поддержка групп
• Многоязычный интерфейс
• История загрузок

🔧 **Доступные команды:**
/start - Запустить бота
/stats - Ваша статистика
/settings - Настройки
/admin - Панель управления (админы)

💬 **Поддержка:** {SUPPORT_CHANNEL}
📢 **Канал:** {MAIN_CHANNEL}
        """,
        'back_button': "🔙 Назад",
        'choose_lang': "🌐 **Выберите язык:**",
        'lang_changed': "✅ Язык успешно изменен!",
        'my_stats_text': """
📊 **Ваша личная статистика:**

• 📥 **Загрузок:** {downloads}
• ⭐ **Предпочтительное качество:** {quality}
• 📅 **Дата регистрации:** {join_date}
• 🕒 **Последняя активность:** {last_active}
• 🌐 **Язык:** {language}

📈 **Уровень:** {level}
        """,
        'group_welcome': f"""
🌟 **Привет! Я {BOT_NAME}** 🌟

📥 Я могу скачивать медиа с:
• YouTube, Instagram, Facebook
• TikTok, Twitter, Pinterest

⚡ **Как использовать:**
1. Отправьте ссылку напрямую
2. Или используйте: /d ссылка

📢 **Канал:** {MAIN_CHANNEL}
💬 **Поддержка:** {SUPPORT_CHANNEL}
        """,
        'bot_added': f"""
✅ **Бот успешно добавлен!**

⚡ **Доступные команды:**
/d ссылка - Для загрузки
/stats - Для статистики
/settings - Для настроек

📢 **Канал:** {MAIN_CHANNEL}
💬 **Поддержка:** {SUPPORT_CHANNEL}
        """,
        'audio_button': "🎵 Скачать аудио",
        'video_button': "📹 Скачать видео",
        'quality_hd': "🔵 Высокое (HD)",
        'quality_sd': "🟢 Среднее (SD)",
        'quality_audio': "🎵 Только аудио",
        'download_complete': """
✅ **Загрузка завершена!**

📁 **Файл:** {title}
🌐 **Платформа:** {platform}
⚡ **Качество:** {quality}
📊 **Размер:** {size}

💬 **Поддержка:** {SUPPORT_CHANNEL}
        """,
        'no_audio': "❌ Аудио не доступно",
        'select_quality': "🎬 **Выберите качество загрузки:**",
        'select_format': "📁 **Выберите тип файла:**",
    }
}

def get_lang(user_id):
    """Get user language preference"""
    return db.get(f"user_lang_{user_id}") or 'en'

def get_text(user_id, key, **kwargs):
    """Get localized text with formatting"""
    lang = get_lang(user_id)
    text = LANGUAGES.get(lang, LANGUAGES['en']).get(key, '')
    
    # Format with kwargs
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    
    return text

def check_subscription(user_id, channels):
    """Check if user is subscribed to required channels"""
    if not channels: return True, None, None
    
    for channel_id in channels:
        try:
            member = bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ['creator', 'administrator', 'member']:
                try:
                    chat = bot.get_chat(channel_id)
                    invite_link = chat.invite_link or f"https://t.me/{chat.username}"
                    return False, chat.title, invite_link
                except:
                    return False, channel_id, None
        except Exception as e:
            print(f"Error checking subscription: {e}")
            continue
    
    return True, None, None

def log_to_channel(message, media_type=None, file_id=None, parse_mode='HTML'):
    """Log activity to channel"""
    try:
        if media_type and file_id:
            if media_type == 'video':
                bot.send_video(LOG_CHANNEL, file_id, caption=message, parse_mode=parse_mode)
            elif media_type == 'audio':
                bot.send_audio(LOG_CHANNEL, file_id, caption=message, parse_mode=parse_mode)
            elif media_type == 'document':
                bot.send_document(LOG_CHANNEL, file_id, caption=message, parse_mode=parse_mode)
        else:
            bot.send_message(LOG_CHANNEL, message, parse_mode=parse_mode)
    except Exception as e:
        print(f"Log channel error: {e}")

def save_download_log(user_id, username, link, platform, success=True, file_size=0):
    """Save download log"""
    logs = db.get("download_logs") or []
    log_entry = {
        'user_id': user_id,
        'username': username,
        'link': link[:100],
        'platform': platform,
        'success': success,
        'file_size': file_size,
        'timestamp': time.time(),
        'date': dt.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    logs.append(log_entry)
    if len(logs) > 1000:
        logs = logs[-1000:]
    db.set("download_logs", logs)

def build_main_keyboard(user_id):
    """Build main menu keyboard"""
    l = get_lang(user_id)
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, 'how_to_use_button'), callback_data="show_help"),
        InlineKeyboardButton(get_text(user_id, 'change_lang_button'), callback_data="change_lang")
    )
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, 'my_stats'), callback_data="my_stats"),
        InlineKeyboardButton(get_text(user_id, 'quality_menu'), callback_data="quality_menu")
    )
    keyboard.add(
        InlineKeyboardButton(get_text(user_id, 'add_group'), url=f"https://t.me/{bot.get_me().username}?startgroup=true"),
        InlineKeyboardButton(get_text(user_id, 'support'), url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")
    )
    
    if user_id in ADMIN_IDS:
        keyboard.add(InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel"))
    
    return keyboard

def build_admin_keyboard():
    """Build advanced admin panel with 10+ features"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # First row
    keyboard.add(
        InlineKeyboardButton("📊 Full Statistics", callback_data="admin_stats_full"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )
    
    # Second row
    keyboard.add(
        InlineKeyboardButton("👥 Users List", callback_data="admin_users_list"),
        InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban")
    )
    
    # Third row
    keyboard.add(
        InlineKeyboardButton("✅ Unban User", callback_data="admin_unban"),
        InlineKeyboardButton("👥 Groups List", callback_data="admin_groups")
    )
    
    # Fourth row
    keyboard.add(
        InlineKeyboardButton("📋 Logs", callback_data="admin_logs"),
        InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")
    )
    
    # Fifth row
    keyboard.add(
        InlineKeyboardButton("📈 Daily Stats", callback_data="admin_daily_stats"),
        InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance")
    )
    
    # Sixth row
    keyboard.add(
        InlineKeyboardButton("📤 Export Data", callback_data="admin_export"),
        InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart")
    )
    
    # Seventh row
    keyboard.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start"))
    
    return keyboard

@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    user_id = message.from_user.id
    
    # Check if banned
    if user_id in (db.get("banned_users") or []):
        bot.send_message(user_id, get_text(user_id, 'banned'))
        return
    
    # Check subscription
    is_subscribed, channel_title, channel_link = check_subscription(user_id, [MAIN_CHANNEL])
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton(f"📢 Join {channel_title or MAIN_CHANNEL}", url=channel_link))
        keyboard.add(InlineKeyboardButton("✅ I've Joined", callback_data="check_join"))
        bot.send_message(user_id, get_text(user_id, 'subscribe_first'), reply_markup=keyboard, parse_mode='Markdown')
        return
    
    # Update user data
    all_users = db.get("user_ids") or []
    if user_id not in all_users:
        all_users.append(user_id)
        db.set("user_ids", all_users)
        
        user_data = {
            'id': user_id,
            'username': message.from_user.username or '',
            'first_name': message.from_user.first_name or '',
            'join_date': time.time(),
            'last_active': time.time(),
            'downloads': 0,
            'preferred_quality': 'hd',
            'language': get_lang(user_id)
        }
        db.set(f"user_info_{user_id}", user_data)
        
        # Log new user
        log_msg = f"""
👤 **New User Registered**
🆔 ID: {user_id}
👤 Name: {message.from_user.first_name}
📛 Username: @{message.from_user.username or 'N/A'}
🌐 Language: {get_lang(user_id)}
📅 Date: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        log_to_channel(log_msg)
    
    else:
        user_data = db.get(f"user_info_{user_id}") or {}
        user_data['last_active'] = time.time()
        db.set(f"user_info_{user_id}", user_data)
    
    # Check if in group
    if message.chat.type in ['group', 'supergroup']:
        bot.send_message(message.chat.id, get_text(user_id, 'group_welcome'), parse_mode='Markdown')
        
        # Register group
        groups = db.get("groups") or {}
        groups[str(message.chat.id)] = {
            'title': message.chat.title,
            'member_count': bot.get_chat_members_count(message.chat.id),
            'added_date': time.time(),
            'admin_id': user_id
        }
        db.set("groups", groups)
        return
    
    # Send welcome message with title
    keyboard = build_main_keyboard(user_id)
    bot.send_message(
        message.chat.id, 
        get_text(user_id, 'welcome'), 
        reply_markup=keyboard, 
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['d', 'download'])
def download_command(message):
    user_id = message.from_user.id
    
    # Check subscription
    is_subscribed, _, _ = check_subscription(user_id, [MAIN_CHANNEL])
    if not is_subscribed:
        start_command(message)
        return
    
    # Get link from command
    if message.text and len(message.text.split()) > 1:
        link = message.text.split(maxsplit=1)[1]
        handle_link(message, link)
    else:
        bot.reply_to(message, "Please provide a link after /d command\nExample: /d https://youtube.com/watch?v=...")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = message.from_user.id
    user_data = db.get(f"user_info_{user_id}") or {}
    
    downloads = user_data.get('downloads', 0)
    quality = user_data.get('preferred_quality', 'hd').upper()
    join_date = dt.fromtimestamp(user_data.get('join_date', time.time())).strftime("%Y-%m-%d")
    last_active = dt.fromtimestamp(user_data.get('last_active', time.time())).strftime("%H:%M %Y-%m-%d")
    language = user_data.get('language', 'en').upper()
    
    # Determine level
    if downloads >= 100:
        level = "🌟 Pro"
    elif downloads >= 50:
        level = "⭐ Advanced"
    elif downloads >= 20:
        level = "✨ Intermediate"
    else:
        level = "🔰 Beginner"
    
    stats_text = get_text(user_id, 'my_stats_text').format(
        downloads=downloads,
        quality=quality,
        join_date=join_date,
        last_active=last_active,
        language=language,
        level=level
    )
    
    bot.reply_to(message, stats_text, parse_mode='Markdown')

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 Access denied!")
        return
    
    # Check SMM subscription for advanced features
    is_subscribed, channel_title, channel_link = check_subscription(user_id, [SMM_CHANNEL])
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(f"📢 Join {SMM_CHANNEL}", url=channel_link))
        keyboard.add(InlineKeyboardButton("✅ I've Joined", callback_data="admin_check_join"))
        bot.send_message(user_id, f"🔒 Advanced Admin Panel requires joining:\n{SMM_CHANNEL}\n\nJoin to access admin features.", reply_markup=keyboard)
        return
    
    # Calculate stats for admin panel
    all_users = db.get("user_ids") or []
    banned_users = db.get("banned_users") or []
    total_downloads = sum((db.get(f"user_info_{uid}") or {}).get('downloads', 0) for uid in all_users)
    
    admin_text = get_text(user_id, 'admin_panel').format(
        bot_name=BOT_NAME,
        total_users=len(all_users),
        total_downloads=total_downloads,
        banned_users=len(banned_users)
    )
    
    keyboard = build_admin_keyboard()
    bot.send_message(user_id, admin_text, reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(commands=['settings'])
def settings_command(message):
    user_id = message.from_user.id
    user_data = db.get(f"user_info_{user_id}") or {}
    
    settings_text = f"""
⚙️ **Your Settings**

🌐 **Language:** {user_data.get('language', 'en').upper()}
🎬 **Default Quality:** {user_data.get('preferred_quality', 'hd').upper()}
📥 **Total Downloads:** {user_data.get('downloads', 0)}

🔧 **Change settings from the menu.**
    """
    
    bot.reply_to(message, settings_text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    user_id = call.from_user.id
    data = call.data
    
    try:
        if data == "check_join":
            is_subscribed, _, channel_link = check_subscription(user_id, [MAIN_CHANNEL])
            if is_subscribed:
                start_command(call.message)
                bot.answer_callback_query(call.id, "✅ Subscription verified!")
            else:
                bot.answer_callback_query(call.id, f"❌ Please join {MAIN_CHANNEL}")
        
        elif data == "admin_check_join":
            if user_id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "🚫 Access denied!")
                return
            
            is_subscribed, _, _ = check_subscription(user_id, [SMM_CHANNEL])
            if is_subscribed:
                admin_command(call.message)
                bot.answer_callback_query(call.id, "✅ Access granted!")
            else:
                bot.answer_callback_query(call.id, f"❌ Please join {SMM_CHANNEL}")
        
        elif data == "show_help":
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(get_text(user_id, 'back_button'), callback_data="back_to_start"))
            bot.edit_message_text(
                get_text(user_id, 'how_to_use_text'),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        elif data == "change_lang":
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("العربية 🇮🇶", callback_data="set_lang_ar"),
                InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
                InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="set_lang_am"),
                InlineKeyboardButton("Русский 🇷🇺", callback_data="set_lang_ru")
            )
            keyboard.add(InlineKeyboardButton(get_text(user_id, 'back_button'), callback_data="back_to_start"))
            bot.edit_message_text(
                get_text(user_id, 'choose_lang'),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
        
        elif data.startswith("set_lang_"):
            new_lang = data.split('_')[-1]
            db.set(f"user_lang_{user_id}", new_lang)
            
            # Update user data
            user_data = db.get(f"user_info_{user_id}") or {}
            user_data['language'] = new_lang
            db.set(f"user_info_{user_id}", user_data)
            
            bot.answer_callback_query(call.id, get_text(user_id, 'lang_changed'))
            start_command(call.message)
        
        elif data == "my_stats":
            stats_command(call.message)
            bot.answer_callback_query(call.id)
        
        elif data == "quality_menu":
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton(get_text(user_id, 'quality_hd'), callback_data="set_quality_hd"),
                InlineKeyboardButton(get_text(user_id, 'quality_sd'), callback_data="set_quality_sd"),
                InlineKeyboardButton(get_text(user_id, 'quality_audio'), callback_data="set_quality_audio")
            )
            keyboard.add(InlineKeyboardButton(get_text(user_id, 'back_button'), callback_data="back_to_start"))
            bot.edit_message_text(
                get_text(user_id, 'select_quality'),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
        
        elif data.startswith("set_quality_"):
            quality = data.split('_')[-1]
            user_data = db.get(f"user_info_{user_id}") or {}
            user_data['preferred_quality'] = quality
            db.set(f"user_info_{user_id}", user_data)
            
            quality_names = {'hd': 'High', 'sd': 'Medium', 'audio': 'Audio Only'}
            bot.answer_callback_query(call.id, f"✅ Quality set to {quality_names.get(quality, quality)}")
            start_command(call.message)
        
        elif data == "admin_panel":
            if user_id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "🚫 Access denied!")
                return
            
            admin_command(call.message)
        
        elif data == "back_to_start":
            start_command(call.message)
        
        elif data.startswith("admin_"):
            handle_admin_callbacks(call)
    
    except KeyError as e:
        print(f"KeyError in callback: {e}")
        bot.answer_callback_query(call.id, "❌ An error occurred. Please try /start again.")
    except Exception as e:
        print(f"Error in callback: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred")

def handle_admin_callbacks(call):
    user_id = call.from_user.id
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "🚫 Access denied!")
        return
    
    data = call.data
    message = call.message
    
    try:
        if data == "admin_stats_full":
            # Full statistics
            all_users = db.get("user_ids") or []
            banned_users = db.get("banned_users") or []
            groups = db.get("groups") or {}
            logs = db.get("download_logs") or []
            
            # Calculate totals
            total_downloads = sum((db.get(f"user_info_{uid}") or {}).get('downloads', 0) for uid in all_users)
            today = dt.now().strftime("%Y-%m-%d")
            today_downloads = sum(1 for log in logs if log.get('date', '').startswith(today))
            
            # Platform stats
            platform_stats = {}
            for log in logs[-1000:]:
                platform = log.get('platform', 'Unknown')
                platform_stats[platform] = platform_stats.get(platform, 0) + 1
            
            stats_text = f"""
📊 **Complete Bot Statistics**

👤 **Users:**
• Total Users: {len(all_users):,}
• Active Today: {sum(1 for uid in all_users if time.time() - (db.get(f'user_info_{uid}') or {}).get('last_active', 0) < 86400):,}
• Banned Users: {len(banned_users):,}

📥 **Downloads:**
• Total Downloads: {total_downloads:,}
• Downloads Today: {today_downloads:,}
• Success Rate: {(sum(1 for log in logs if log.get('success')) / max(len(logs), 1) * 100):.1f}%

👥 **Groups:**
• Total Groups: {len(groups):,}
• Active Groups: {len([g for g in groups.values() if time.time() - g.get('added_date', 0) < 604800]):,}

🌐 **Platform Usage (Last 1000):**
"""
            
            for platform, count in sorted(platform_stats.items(), key=lambda x: x[1], reverse=True):
                stats_text += f"• {platform}: {count:,}\n"
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats_full"))
            keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
            
            bot.edit_message_text(stats_text, message.chat.id, message.message_id, 
                                 reply_markup=keyboard, parse_mode='Markdown')
        
        elif data == "admin_broadcast":
            user_states[user_id] = {'state': 'broadcast', 'message_id': message.message_id}
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔙 Cancel", callback_data="admin_panel"))
            bot.edit_message_text("📢 **Send Broadcast Message**\n\nSend the message you want to broadcast to all users:", 
                                 message.chat.id, message.message_id, reply_markup=keyboard, parse_mode='Markdown')
        
        elif data == "admin_users_list":
            all_users = db.get("user_ids") or []
            users_text = f"👥 **Total Users: {len(all_users):,}**\n\n"
            users_text += "**Recent Users (Last 20):**\n"
            
            for uid in all_users[-20:]:
                user_data = db.get(f"user_info_{uid}") or {}
                username = user_data.get('username', 'N/A')
                downloads = user_data.get('downloads', 0)
                users_text += f"• @{username} - {downloads} downloads\n"
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("📥 Export Users", callback_data="admin_export_users"))
            keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
            
            bot.edit_message_text(users_text, message.chat.id, message.message_id, 
                                 reply_markup=keyboard, parse_mode='Markdown')
        
        elif data == "admin_ban":
            user_states[user_id] = {'state': 'ban', 'message_id': message.message_id}
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔙 Cancel", callback_data="admin_panel"))
            bot.edit_message_text("🚫 **Ban User**\n\nSend the user ID to ban:", 
                                 message.chat.id, message.message_id, reply_markup=keyboard, parse_mode='Markdown')
        
        elif data == "admin_unban":
            banned_users = db.get("banned_users") or []
            if not banned_users:
                bot.edit_message_text("✅ No users are currently banned.", 
                                     message.chat.id, message.message_id)
                return
            
            keyboard = InlineKeyboardMarkup()
            for uid in banned_users[-10:]:
                keyboard.add(InlineKeyboardButton(f"User {uid}", callback_data=f"unban_{uid}"))
            keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
            
            bot.edit_message_text("✅ **Select user to unban:**", 
                                 message.chat.id, message.message_id, reply_markup=keyboard, parse_mode='Markdown')
        
        elif data.startswith("unban_"):
            try:
                uid_to_unban = int(data.split('_')[1])
                banned_users = db.get("banned_users") or []
                
                if uid_to_unban in banned_users:
                    banned_users.remove(uid_to_unban)
                    db.set("banned_users", banned_users)
                    bot.answer_callback_query(call.id, f"✅ User {uid_to_unban} unbanned!")
                else:
                    bot.answer_callback_query(call.id, "❌ User not found in banned list.")
                
                admin_command(message)
            except:
                bot.answer_callback_query(call.id, "❌ Error unbanning user.")
        
        elif data == "admin_groups":
            groups = db.get("groups") or {}
            groups_text = f"👥 **Total Groups: {len(groups):,}**\n\n"
            groups_text += "**Recent Groups (Last 10):**\n"
            
            for group_id, group_info in list(groups.items())[-10:]:
                title = group_info.get('title', 'Unknown')[:30]
                members = group_info.get('member_count', 0)
                days = int((time.time() - group_info.get('added_date', 0)) / 86400)
                groups_text += f"• {title} - {members:,} members ({days}d)\n"
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔄 Refresh", callback_data="admin_groups"))
            keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
            
            bot.edit_message_text(groups_text, message.chat.id, message.message_id, 
                                 reply_markup=keyboard, parse_mode='Markdown')
        
        elif data == "admin_logs":
            logs = db.get("download_logs") or []
            logs_text = f"📋 **Total Logs: {len(logs):,}**\n\n"
            logs_text += "**Recent Downloads (Last 10):**\n"
            
            for log in logs[-10:]:
                username = log.get('username', 'N/A')
                platform = log.get('platform', 'Unknown')
                success = "✅" if log.get('success') else "❌"
                time_str = log.get('date', 'N/A')
                logs_text += f"• @{username} - {platform} {success} - {time_str}\n"
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("📊 Full Statistics", callback_data="admin_stats_full"))
            keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
            
            bot.edit_message_text(logs_text, message.chat.id, message.message_id, 
                                 reply_markup=keyboard, parse_mode='Markdown')
        
        elif data == "admin_settings":
            settings = db.get("settings") or {}
            all_users = db.get("user_ids") or []
            
            settings_text = f"""
⚙️ **Bot Settings**

🔧 **Current Settings:**
• Maintenance Mode: {'✅ ON' if settings.get('maintenance') else '❌ OFF'}
• Max File Size: {settings.get('max_file_size', 50)}MB
• Default Quality: {settings.get('quality_default', 'hd').upper()}
• Watermark Removal: {'✅ ON' if settings.get('watermark_removal') else '❌ OFF'}

📊 **Bot Info:**
• Name: {BOT_NAME}
• Version: 3.0 Advanced
• Developer: @Elabcode
• Support: @Elabsupport
• Users: {len(all_users):,}
• Uptime: Running
            """
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("🔄 Toggle Maintenance", callback_data="toggle_maintenance"),
                InlineKeyboardButton("⚡ Change Quality", callback_data="change_global_quality")
            )
            keyboard.add(
                InlineKeyboardButton("📏 File Size Limit", callback_data="change_file_size"),
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            )
            
            bot.edit_message_text(settings_text, message.chat.id, message.message_id, 
                                 reply_markup=keyboard, parse_mode='Markdown')
        
        elif data == "admin_daily_stats":
            daily_stats = db.get("daily_stats") or {}
            today = dt.now().strftime("%Y-%m-%d")
            
            stats_text = "📈 **Daily Statistics**\n\n"
            for date, stats in list(daily_stats.items())[-7:]:  # Last 7 days
                downloads = stats.get('downloads', 0)
                users = stats.get('users', 0)
                stats_text += f"• {date}: {downloads:,} downloads, {users:,} users\n"
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔄 Refresh", callback_data="admin_daily_stats"))
            keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
            
            bot.edit_message_text(stats_text, message.chat.id, message.message_id, 
                                 reply_markup=keyboard, parse_mode='Markdown')
        
        elif data == "admin_maintenance":
            settings = db.get("settings") or {}
            current = settings.get('maintenance', False)
            settings['maintenance'] = not current
            db.set("settings", settings)
            
            status = "ON" if settings['maintenance'] else "OFF"
            bot.answer_callback_query(call.id, f"✅ Maintenance mode turned {status}")
            admin_command(message)
        
        elif data == "admin_export":
            all_users = db.get("user_ids") or []
            export_text = f"📊 **Bot Data Export**\n\n"
            export_text += f"Total Users: {len(all_users)}\n"
            export_text += f"Export Date: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("📤 Export Users CSV", callback_data="export_users_csv"))
            keyboard.add(InlineKeyboardButton("📊 Export Stats", callback_data="export_stats"))
            keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
            
            bot.edit_message_text(export_text, message.chat.id, message.message_id, 
                                 reply_markup=keyboard, parse_mode='Markdown')
        
        elif data == "admin_restart":
            bot.answer_callback_query(call.id, "🔄 Bot restarting...")
            import sys
            os.execl(sys.executable, sys.executable, *sys.argv)
        
        elif data == "admin_panel":
            admin_command(message)
        
        elif data == "export_users_csv":
            all_users = db.get("user_ids") or []
            csv_data = "ID,Username,Downloads,Join Date,Last Active\n"
            
            for uid in all_users:
                user_data = db.get(f"user_info_{uid}") or {}
                username = user_data.get('username', 'N/A')
                downloads = user_data.get('downloads', 0)
                join_date = dt.fromtimestamp(user_data.get('join_date', time.time())).strftime("%Y-%m-%d")
                last_active = dt.fromtimestamp(user_data.get('last_active', time.time())).strftime("%Y-%m-%d %H:%M:%S")
                csv_data += f"{uid},{username},{downloads},{join_date},{last_active}\n"
            
            # Send as file
            with open("users_export.csv", "w", encoding="utf-8") as f:
                f.write(csv_data)
            
            with open("users_export.csv", "rb") as f:
                bot.send_document(message.chat.id, f, caption="📤 Users Export CSV")
            
            os.remove("users_export.csv")
            bot.answer_callback_query(call.id, "✅ Export completed!")
    
    except Exception as e:
        print(f"Admin callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred")

def handle_link(message, link):
    user_id = message.from_user.id
    
    # Check subscription
    is_subscribed, _, _ = check_subscription(user_id, [MAIN_CHANNEL])
    if not is_subscribed:
        start_command(message)
        return
    
    # Check maintenance mode
    settings = db.get("settings") or {}
    if settings.get('maintenance', False):
        bot.reply_to(message, "⚠️ Bot is under maintenance. Please try again later.")
        return
    
    # Update user activity
    user_data = db.get(f"user_info_{user_id}") or {}
    user_data['last_active'] = time.time()
    db.set(f"user_info_{user_id}", user_data)
    
    # Show processing message
    processing_msg = bot.reply_to(message, get_text(user_id, 'searching'))
    
    try:
        # Original downloading function
        session = requests.Session()
        session.headers.update({'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'})
        response = session.get("https://www.videofk.com/search", params={'url': link}, timeout=60)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('h2', class_='h2') or soup.find('div', class_='video-title')
        title = title_tag.text.strip() if title_tag else "media_download"
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        
        encrypted_links = [{"text": link.text.strip().lower(), "encrypted": link['href'].split('#url=')[1]} 
                          for link in soup.find_all('a', href=re.compile(r'#url='))]
        
        if not encrypted_links:
            raise ValueError(get_text(user_id, 'error_general'))
        
        bot.edit_message_text(get_text(user_id, 'downloading'), 
                             chat_id=processing_msg.chat.id, 
                             message_id=processing_msg.message_id)
        
        best_video, best_audio_url, no_watermark_video_url = {'url': None, 'size': 0}, None, None
        
        for link_info in encrypted_links:
            try:
                resp = requests.get('https://downloader.twdown.online/load_url', 
                                   params={'url': link_info['encrypted']}, 
                                   headers={'user-agent': 'Mozilla/5.0'}, 
                                   timeout=60)
                if not (resp.ok and resp.text.strip().startswith('http')): 
                    continue
                final_url = resp.text.strip()
                is_audio = any(keyword in link_info['text'] for keyword in ['mp3', 'm4a', 'aac', 'kbps'])
                if is_audio and not best_audio_url: 
                    best_audio_url = final_url
                elif not is_audio:
                    if 'without water' in link_info['text']: 
                        no_watermark_video_url = final_url
                        break
                    size = int(requests.head(final_url, allow_redirects=True, timeout=60).headers.get('Content-Length', 0))
                    if size > best_video['size']: 
                        best_video['url'], best_video['size'] = final_url, size
            except Exception: 
                continue
        
        # Determine platform
        platform = "Unknown"
        if "youtube.com" in link or "youtu.be" in link:
            platform = "YouTube"
        elif "instagram.com" in link:
            platform = "Instagram"
        elif "facebook.com" in link:
            platform = "Facebook"
        elif "tiktok.com" in link:
            platform = "TikTok"
        elif "twitter.com" in link or "x.com" in link:
            platform = "Twitter/X"
        elif "pinterest.com" in link:
            platform = "Pinterest"
        elif "snapchat.com" in link:
            platform = "Snapchat"
        elif "reddit.com" in link:
            platform = "Reddit"
        
        sent_count = 0
        final_video_to_send = no_watermark_video_url or best_video['url']
        
        # Get user preferred quality
        user_data = db.get(f"user_info_{user_id}") or {}
        preferred_quality = user_data.get('preferred_quality', 'hd')
        
        # Send video if available and user wants it
        if final_video_to_send and preferred_quality != 'audio':
            try:
                media_content = requests.get(final_video_to_send, headers={"User-Agent": "Mozilla/5.0"}, timeout=60).content
                file_size_mb = len(media_content) / (1024 * 1024)
                
                # Check file size limit
                max_size = settings.get('max_file_size', 50)
                if file_size_mb <= max_size:
                    stream = io.BytesIO(media_content)
                    msg = bot.send_video(
                        message.chat.id, 
                        stream, 
                        caption=f"📥 {safe_title}\n🌐 {platform}\n⚡ @{bot.get_me().username}",
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                    
                    # Log to channel
                    log_message = f"""
📥 **New Download**
👤 User: {message.from_user.first_name} (@{message.from_user.username or 'N/A'})
🆔 ID: {user_id}
🌐 Platform: {platform}
🔗 Link: {link[:50]}...
✅ Status: Success
📊 Size: {file_size_mb:.1f}MB
🕒 Time: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    log_to_channel(log_message, 'video', msg.video.file_id)
                    
                    # Create audio button if audio is available
                    if best_audio_url:
                        keyboard = InlineKeyboardMarkup()
                        keyboard.add(InlineKeyboardButton(get_text(user_id, 'audio_button'), 
                                                         callback_data=f"audio_{link}_{message.message_id}"))
                        bot.edit_message_caption(
                            caption=f"📥 {safe_title}\n🌐 {platform}\n⚡ @{bot.get_me().username}\n\n🎵 Audio available!",
                            chat_id=message.chat.id,
                            message_id=msg.message_id,
                            reply_markup=keyboard,
                            parse_mode='Markdown'
                        )
                else:
                    bot.send_message(message.chat.id, f"❌ File too large ({file_size_mb:.1f}MB > {max_size}MB limit)")
            except Exception as e:
                print(f"Failed to send video: {e}")
        
        # Send audio if available and (user wants it or video failed)
        if best_audio_url and (preferred_quality == 'audio' or sent_count == 0):
            try:
                media_content = requests.get(best_audio_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60).content
                file_size_mb = len(media_content) / (1024 * 1024)
                
                max_size = settings.get('max_file_size', 50)
                if file_size_mb <= max_size:
                    stream = io.BytesIO(media_content)
                    msg = bot.send_audio(
                        message.chat.id, 
                        stream, 
                        title=safe_title,
                        performer=f"Downloaded via @{bot.get_me().username}",
                        caption=f"🎵 {safe_title}\n🌐 {platform}\n⚡ @{bot.get_me().username}",
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                    
                    # Log audio
                    log_message = f"""
🎵 **Audio Download**
👤 User: {message.from_user.first_name} (@{message.from_user.username or 'N/A'})
🆔 ID: {user_id}
🌐 Platform: {platform}
🔗 Link: {link[:50]}...
✅ Status: Success
📊 Size: {file_size_mb:.1f}MB
🕒 Time: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    log_to_channel(log_message, 'audio', msg.audio.file_id)
                else:
                    bot.send_message(message.chat.id, f"❌ Audio file too large ({file_size_mb:.1f}MB > {max_size}MB limit)")
            except Exception as e:
                print(f"Failed to send audio: {e}")
        
        if sent_count > 0:
            bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
            
            # Update user stats
            user_data = db.get(f"user_info_{user_id}") or {}
            user_data['downloads'] = user_data.get('downloads', 0) + 1
            db.set(f"user_info_{user_id}", user_data)
            
            # Save download log
            file_size = (best_video.get('size', 0) / (1024 * 1024)) if best_video.get('size') else 0
            save_download_log(user_id, message.from_user.username, link, platform, success=True, file_size=file_size)
            
            # Send success message
            success_msg = get_text(user_id, 'download_complete').format(
                title=safe_title,
                platform=platform,
                quality=preferred_quality.upper(),
                size=f"{file_size:.1f}MB" if file_size > 0 else "Unknown"
            )
            
            # Add format selection buttons
            keyboard = InlineKeyboardMarkup(row_width=2)
            if final_video_to_send:
                keyboard.add(InlineKeyboardButton(get_text(user_id, 'video_button'), 
                                                 callback_data=f"video_{link}_{message.message_id}"))
            if best_audio_url:
                keyboard.add(InlineKeyboardButton(get_text(user_id, 'audio_button'), 
                                                 callback_data=f"audio_{link}_{message.message_id}"))
            
            if final_video_to_send or best_audio_url:
                bot.reply_to(message, success_msg, reply_markup=keyboard, parse_mode='Markdown')
        else:
            bot.edit_message_text(get_text(user_id, 'error_general'), 
                                 chat_id=processing_msg.chat.id, 
                                 message_id=processing_msg.message_id)
            save_download_log(user_id, message.from_user.username, link, platform, success=False)
    
    except Exception as e:
        print(f"Download error: {e}")
        bot.edit_message_text(get_text(user_id, 'error_link'), 
                             chat_id=processing_msg.chat.id, 
                             message_id=processing_msg.message_id)
        save_download_log(user_id, message.from_user.username, link, "Unknown", success=False)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('audio_', 'video_')))
def handle_format_selection(call):
    user_id = call.from_user.id
    data = call.data
    
    try:
        if data.startswith('audio_'):
            parts = data.split('_')
            if len(parts) >= 3:
                link = '_'.join(parts[1:-1])  # Reconstruct link
                message_id = parts[-1]
                
                # Create a new message to trigger audio download
                fake_message = types.Message(
                    message_id=int(message_id),
                    from_user=call.from_user,
                    date=int(time.time()),
                    chat=call.message.chat,
                    content_type='text',
                    options={},
                    json_string=''
                )
                fake_message.text = link
                
                # Send processing message
                processing_msg = bot.send_message(call.message.chat.id, get_text(user_id, 'processing'))
                
                # Trigger audio download
                handle_link(fake_message, link)
                
                # Delete processing message
                try:
                    bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
                except:
                    pass
                
                bot.answer_callback_query(call.id, "🎵 Downloading audio...")
        
        elif data.startswith('video_'):
            parts = data.split('_')
            if len(parts) >= 3:
                link = '_'.join(parts[1:-1])  # Reconstruct link
                message_id = parts[-1]
                
                # Create a new message to trigger video download
                fake_message = types.Message(
                    message_id=int(message_id),
                    from_user=call.from_user,
                    date=int(time.time()),
                    chat=call.message.chat,
                    content_type='text',
                    options={},
                    json_string=''
                )
                fake_message.text = link
                
                # Send processing message
                processing_msg = bot.send_message(call.message.chat.id, get_text(user_id, 'processing'))
                
                # Trigger video download
                handle_link(fake_message, link)
                
                # Delete processing message
                try:
                    bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
                except:
                    pass
                
                bot.answer_callback_query(call.id, "📹 Downloading video...")
    
    except Exception as e:
        print(f"Format selection error: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    
    # Check if user is in a state
    if user_id in user_states:
        handle_user_state(message)
        return
    
    # Check if it's a URL
    if message.text and (message.text.startswith('http://') or message.text.startswith('https://')):
        handle_link(message, message.text)
        return
    
    # Default response
    bot.reply_to(message, "Please send a valid link or use /help for instructions.")

def handle_user_state(message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return
    
    state_info = user_states[user_id]
    state = state_info.get('state')
    
    try:
        if state == 'broadcast' and user_id in ADMIN_IDS:
            # Broadcast message
            all_users = db.get("user_ids") or []
            sent = 0
            failed = 0
            
            progress_msg = bot.reply_to(message, "📢 Broadcasting started...")
            
            for uid in all_users:
                try:
                    bot.copy_message(uid, message.chat.id, message.message_id)
                    sent += 1
                    if sent % 100 == 0:  # Update progress every 100 users
                        try:
                            bot.edit_message_text(
                                f"📢 Broadcasting...\nProgress: {sent}/{len(all_users)} ({sent/len(all_users)*100:.1f}%)",
                                progress_msg.chat.id,
                                progress_msg.message_id
                            )
                        except:
                            pass
                    time.sleep(0.05)  # Prevent flooding
                except Exception as e:
                    failed += 1
            
            # Send completion report
            success_rate = (sent / len(all_users) * 100) if all_users else 0
            report = f"""
✅ **Broadcast Complete!**

📊 **Statistics:**
• 📤 Sent: {sent:,}
• ❌ Failed: {failed:,}
• 📈 Success Rate: {success_rate:.1f}%
• 👥 Total Users: {len(all_users):,}

🕒 **Time:** {dt.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            bot.reply_to(message, report, parse_mode='Markdown')
            bot.delete_message(progress_msg.chat.id, progress_msg.message_id)
            
            # Log broadcast
            log_message = f"""
📢 **Broadcast Sent**
👤 Admin: {message.from_user.first_name} (@{message.from_user.username or 'N/A'})
📊 Stats: {sent} sent, {failed} failed
📅 Time: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            log_to_channel(log_message)
            
            del user_states[user_id]
            admin_command(message)
        
        elif state == 'ban' and user_id in ADMIN_IDS:
            try:
                uid_to_ban = int(message.text)
                banned_users = db.get("banned_users") or []
                
                if uid_to_ban not in banned_users:
                    banned_users.append(uid_to_ban)
                    db.set("banned_users", banned_users)
                    
                    # Get user info for logging
                    user_info = db.get(f"user_info_{uid_to_ban}") or {}
                    username = user_info.get('username', 'N/A')
                    
                    bot.reply_to(message, f"✅ User {uid_to_ban} (@{username}) has been banned.")
                    
                    # Log ban
                    log_message = f"""
🚫 **User Banned**
👤 Admin: {message.from_user.first_name} (@{message.from_user.username})
🚫 Banned User: {uid_to_ban} (@{username})
📅 Time: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    log_to_channel(log_message)
                else:
                    bot.reply_to(message, f"❌ User {uid_to_ban} is already banned.")
                
                del user_states[user_id]
                admin_command(message)
            except ValueError:
                bot.reply_to(message, "❌ Invalid user ID. Please send a numeric ID.")
    
    except Exception as e:
        print(f"User state error: {e}")
        bot.reply_to(message, "❌ An error occurred.")

def update_daily_stats():
    """Update daily statistics"""
    today = dt.now().strftime("%Y-%m-%d")
    daily_stats = db.get("daily_stats") or {}
    
    if today not in daily_stats:
        daily_stats[today] = {'downloads': 0, 'users': 0}
    
    # Count active users today
    all_users = db.get("user_ids") or []
    active_today = 0
    now = time.time()
    
    for uid in all_users:
        user_data = db.get(f"user_info_{uid}") or {}
        last_active = user_data.get('last_active', 0)
        if now - last_active < 86400:  # Last 24 hours
            active_today += 1
    
    # Count downloads today
    logs = db.get("download_logs") or []
    downloads_today = sum(1 for log in logs if log.get('date', '').startswith(today) and log.get('success'))
    
    daily_stats[today]['users'] = active_today
    daily_stats[today]['downloads'] = downloads_today
    db.set("daily_stats", daily_stats)

# Scheduled task for daily stats
def scheduled_tasks():
    schedule.every().day.at("00:00").do(update_daily_stats)
    schedule.every(30).minutes.do(update_daily_stats)  # Also update every 30 minutes
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    print(f"""
🤖 {BOT_NAME} Started Successfully!
👑 Admin IDs: {ADMIN_IDS}
📢 Main Channel: {MAIN_CHANNEL}
💬 Support: {SUPPORT_CHANNEL}
📝 Log Channel: {LOG_CHANNEL}
⚡ Bot is running...
    """)
    
    # Start scheduled tasks in background
    Thread(target=scheduled_tasks, daemon=True).start()
    
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
    
    
    
    