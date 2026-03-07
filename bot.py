# -*- coding: utf-8 -*-
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from sheet_helper import sheet_manager

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

COMPANY_NAME = "Logistics Supporter"
CONTACT_TELEGRAM = "t.me/+84967070468"
CONTACT_ZALO = "0967070468"
WORKING_HOURS = "Thứ 2 - Thứ 6: 8:00 - 17:30 | Thứ 7: 8:00 - 12:00"

ROUTES = {
    "vnuswc": {
        "name": "VN → US West Coast",
        "pol": "HCM",
        "pods": ["LAX", "LGB", "SEA"],
        "flag": "🇺🇸"
    },
    "vnusec": {
        "name": "VN → US East Coast",
        "pol": "HCM",
        "pods": ["NYC", "SAV", "MIA"],
        "flag": "🇺🇸"
    },
    "vneu": {
        "name": "VN → EU",
        "pol": "HCM",
        "pods": ["RTM", "HAM", "FEL"],
        "flag": "🇪🇺"
    },
    "vnjp": {
        "name": "VN → Japan",
        "pol": "HCM",
        "pods": ["TYO", "OSA", "NGO"],
        "flag": "🇯🇵"
    },
    "vnkr": {
        "name": "VN → Korea",
        "pol": "HCM",
        "pods": ["BUS", "INC"],
        "flag": "🇰🇷"
    },
    "vnau": {
        "name": "VN → Australia",
        "pol": "HCM",
        "pods": ["SYD", "MEL", "BNE"],
        "flag": "🇦🇺"
    },
    "vnin": {
        "name": "VN → India",
        "pol": "HCM",
        "pods": ["JNPT", "NMPT", "MAA"],
        "flag": "🇮🇳"
    }
}


# ── MAIN MENU ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("📊 Bảng giá cước", callback_data='rates'),
            InlineKeyboardButton("🛳 Space & Lịch tàu", callback_data='space')
        ],
        [
            InlineKeyboardButton("🗺 Các tuyến", callback_data='routes'),
            InlineKeyboardButton("📞 Liên hệ tư vấn", callback_data='contact')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🚢 *{COMPANY_NAME}*\n\n"
        f"Xin chào {user.first_name}! 👋\n"
        f"Tôi có thể giúp bạn tra cứu:\n\n"
        f"📊 Giá cước Ocean Freight\n"
        f"🛳 Space & Lịch tàu\n"
        f"🗺 Các tuyến đang khai thác\n\n"
        f"Vui lòng chọn thông tin cần xem:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ── ROUTES ─────────────────────────────────────────────────────────────────────

async def show_routes(query):
    text = f"🗺 *Các tuyến đang khai thác*\n\n"
    for key, r in ROUTES.items():
        pods = ", ".join(r['pods'])
        text += f"{r['flag']} *{r['name']}*\n"
        text += f"   POL: {r['pol']} → POD: {pods}\n\n"

    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data='back')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


# ── RATES ──────────────────────────────────────────────────────────────────────

async def show_rates_menu(query):
    keyboard = []
    row = []
    for key, r in ROUTES.items():
        row.append(InlineKeyboardButton(f"{r['flag']} {r['name']}", callback_data=f'rate_{key}'))
        if len(row) == 1:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data='back')])

    await query.edit_message_text(
        "📊 *Bảng giá cước*\n\nChọn tuyến bạn muốn xem:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_rate_detail(query, route_key):
    if route_key not in ROUTES:
        await query.edit_message_text("❌ Tuyến không hợp lệ.")
        return

    r = ROUTES[route_key]
    rates = sheet_manager.get_rates(route=r['name'])

    keyboard = [
        [InlineKeyboardButton("🔙 Quay lại", callback_data='rates')]
    ]

    if not rates:
        await query.edit_message_text(
            f"⚠️ *Hiện chưa có giá cho tuyến {r['name']}*\n\n"
            f"Vui lòng liên hệ trực tiếp để được báo giá:\n"
            f"📱 Telegram: {CONTACT_TELEGRAM}\n"
            f"📲 Zalo: {CONTACT_ZALO}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    msg = f"📊 *Bảng giá {r['name']}*\n"
    msg += f"POL: {r['pol']}\n"
    msg += "─" * 25 + "\n\n"

    for rate in rates[:5]:
        msg += f"🚢 *{rate.get('Carrier', 'N/A')}*\n"
        msg += f"  20GP: ${rate.get('20GP', 'N/A')}\n"
        msg += f"  40GP: ${rate.get('40GP', 'N/A')}\n"
        msg += f"  40HC: ${rate.get('40HC', 'N/A')}\n"
        msg += f"  Valid to: {rate.get('Valid_To', 'N/A')}\n"
        if rate.get('Notes'):
            msg += f"  📝 {rate.get('Notes')}\n"
        msg += "\n"

    msg += f"📞 Đặt chỗ: {CONTACT_TELEGRAM}"

    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


# ── SPACE ──────────────────────────────────────────────────────────────────────

async def show_space_menu(query):
    keyboard = []
    for key, r in ROUTES.items():
        keyboard.append([InlineKeyboardButton(f"{r['flag']} {r['name']}", callback_data=f'space_{key}')])
    keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data='back')])

    await query.edit_message_text(
        "🛳 *Space & Lịch tàu*\n\nChọn tuyến bạn muốn xem:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_space_detail(query, route_key):
    if route_key not in ROUTES:
        await query.edit_message_text("❌ Tuyến không hợp lệ.")
        return

    r = ROUTES[route_key]
    spaces = sheet_manager.get_space(route=r['name'])

    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data='space')]]

    if not spaces:
        await query.edit_message_text(
            f"⚠️ *Hiện chưa có thông tin space cho {r['name']}*\n\n"
            f"Liên hệ để được cập nhật nhanh nhất:\n"
            f"📱 Telegram: {CONTACT_TELEGRAM}\n"
            f"📲 Zalo: {CONTACT_ZALO}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    msg = f"🛳 *Space còn trống - {r['name']}*\n"
    msg += "─" * 25 + "\n\n"

    for s in spaces[:5]:
        status_icon = "✅" if s.get('Status', '').upper() == 'OPEN' else "🔴"
        msg += f"{status_icon} *{s.get('Vessel', 'N/A')}*\n"
        msg += f"  ETD: {s.get('ETD', 'N/A')} | ETA: {s.get('ETA', 'N/A')}\n"
        msg += f"  20': {s.get('Space_20', '0')} slot | 40': {s.get('Space_40', '0')} slot\n"
        msg += f"  Carrier: {s.get('Carrier', 'N/A')}\n\n"

    msg += f"📞 Đặt chỗ ngay: {CONTACT_TELEGRAM}"

    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


# ── CONTACT ────────────────────────────────────────────────────────────────────

async def show_contact(query):
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data='back')]]
    await query.edit_message_text(
        f"📞 *Liên hệ tư vấn*\n\n"
        f"🏢 *{COMPANY_NAME}*\n\n"
        f"📱 *Telegram:* {CONTACT_TELEGRAM}\n"
        f"📲 *Zalo:* {CONTACT_ZALO}\n\n"
        f"⏰ *Giờ làm việc:*\n"
        f"{WORKING_HOURS}\n\n"
        f"💬 Chúng tôi sẽ phản hồi trong vòng 30 phút!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# ── CALLBACK ROUTER ────────────────────────────────────────────────────────────

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'rates':
        await show_rates_menu(query)
    elif data == 'space':
        await show_space_menu(query)
    elif data == 'routes':
        await show_routes(query)
    elif data == 'contact':
        await show_contact(query)
    elif data == 'back':
        await back_to_main(update, context)
    elif data.startswith('rate_'):
        await show_rate_detail(query, data[5:])
    elif data.startswith('space_'):
        await show_space_detail(query, data[6:])


# ── ADMIN: UPLOAD EXCEL ────────────────────────────────────────────────────────

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng tính năng này.")
        return

    doc = update.message.document
    if not doc.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("⚠️ Vui lòng gửi file Excel (.xlsx hoặc .xls)")
        return

    await update.message.reply_text("⏳ Đang xử lý file Excel...")

    try:
        file = await context.bot.get_file(doc.file_id)
        file_path = f"/tmp/{doc.file_name}"
        await file.download_to_drive(file_path)

        result = sheet_manager.import_excel(file_path)

        keyboard = [[InlineKeyboardButton("✅ Xác nhận cập nhật", callback_data='confirm_import'),
                     InlineKeyboardButton("❌ Huỷ", callback_data='cancel_import')]]

        await update.message.reply_text(
            f"📋 *Preview dữ liệu từ Excel:*\n\n"
            f"📊 RATES: {result.get('rates_count', 0)} dòng\n"
            f"🛳 SPACE: {result.get('space_count', 0)} dòng\n\n"
            f"Xác nhận cập nhật lên Google Sheet?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi xử lý file: {str(e)}")


# ── MESSAGE HANDLER ────────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📋 Xem menu", callback_data='back')]]
    await update.message.reply_text(
        "❓ Vui lòng sử dụng menu để tra cứu thông tin.\n\n"
        "Hoặc liên hệ trực tiếp:\n"
        f"📱 {CONTACT_TELEGRAM}\n"
        f"📲 {CONTACT_ZALO}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ── BACK TO MAIN ───────────────────────────────────────────────────────────────

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    keyboard = [
        [
            InlineKeyboardButton("📊 Bảng giá cước", callback_data='rates'),
            InlineKeyboardButton("🛳 Space & Lịch tàu", callback_data='space')
        ],
        [
            InlineKeyboardButton("🗺 Các tuyến", callback_data='routes'),
            InlineKeyboardButton("📞 Liên hệ tư vấn", callback_data='contact')
        ]
    ]

    await query.edit_message_text(
        f"🚢 *{COMPANY_NAME}*\n\n"
        f"Chọn thông tin cần xem:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Logistics Supporter Bot đang chạy...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
