import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from sheet_helper import sheet_manager


load_dotenv()

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token và Admin ID
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start"""
    user = update.effective_user
    
    # Lấy config từ sheet
    company = sheet_manager.get_config('company_name') or "Công ty chúng tôi"
    welcome = sheet_manager.get_config('welcome_message') or f"Chào mừng {user.first_name}!"
    
    # Tạo keyboard
    keyboard = [
        [
            InlineKeyboardButton("📊 Bảng giá", callback_data='rates'),
            InlineKeyboardButton("🛳 Space", callback_data='space')
        ],
        [
            InlineKeyboardButton("🗺 Các tuyến", callback_data='routes'),
            InlineKeyboardButton("📞 Liên hệ", callback_data='contact')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Gửi tin nhắn
    await update.message.reply_text(
        f"🚢 *{company}*\n\n"
        f"{welcome}\n\n"
        f"Tôi có thể giúp gì cho bạn?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Ghi log
    sheet_manager.log_action(user.id, "START", "", "SUCCESS")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý khi nhấn nút"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    data = query.data
    
    if data == 'rates':
        await show_rates_menu(query)
    elif data == 'space':
        await show_space_menu(query)
    elif data == 'routes':
        await show_routes(query)
    elif data == 'contact':
        await show_contact(query)
    elif data.startswith('rate_'):
        await show_rate_detail(query, data[5:])
    elif data.startswith('space_'):
        await show_space_detail(query, data[6:])
    
    # Ghi log
    sheet_manager.log_action(user.id, "BUTTON", data, "SUCCESS")

async def show_rates_menu(query):
    """Hiển thị menu chọn tuyến để xem giá"""
    # Lấy danh sách routes từ sheet (tạm thời hard code)
    routes = [
        ("VN-US WC", "rate_vnuswc"),
        ("VN-US EC", "rate_vnusec"),
        ("VN-EU", "rate_vneu"),
        ("VN-JP", "rate_vnjp"),
        ("VN-KR", "rate_vnkr")
    ]
    
    keyboard = []
    for route_name, callback in routes:
        keyboard.append([InlineKeyboardButton(route_name, callback_data=callback)])
    keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data='back')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📊 *Chọn tuyến bạn muốn xem giá:*\n\n"
        "👉 Click vào tuyến để xem chi tiết",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_space_menu(query):
    """Hiển thị menu chọn POD để xem space"""
    # Lấy danh sách POD từ sheet (tạm thời hard code)
    pods = [
        ("🇺🇸 Los Angeles (LAX)", "space_lax"),
        ("🇺🇸 New York (NYC)", "space_nyc"),
        ("🇪🇺 Rotterdam (RTM)", "space_rtm"),
        ("🇯🇵 Tokyo (TYO)", "space_tyo"),
        ("🇰🇷 Busan (BUS)", "space_bus")
    ]
    
    keyboard = []
    for pod_name, callback in pods:
        keyboard.append([InlineKeyboardButton(pod_name, callback_data=callback)])
    keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data='back')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🛳 *Chọn cảng đích để xem space còn trống:*\n\n"
        "👉 Click vào cảng để xem chi tiết",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_rate_detail(query, route):
    """Hiển thị chi tiết giá cho tuyến đã chọn"""
    # Map route code sang tên
    route_map = {
        'vnuswc': ('VN-US WC', 'HCM', 'LAX'),
        'vnusec': ('VN-US EC', 'HCM', 'NYC'),
        'vneu': ('VN-EU', 'HCM', 'RTM'),
        'vnjp': ('VN-JP', 'HCM', 'TYO'),
        'vnkr': ('VN-KR', 'HCM', 'BUS')
    }
    
    if route not in route_map:
        await query.edit_message_text("❌ Không tìm thấy thông tin tuyến này!")
        return
    
    route_name, pol, pod = route_map[route]
    
    # Lấy dữ liệu từ sheet
    rates = sheet_manager.get_rates(pol=pol, pod=pod)
    
    if not rates:
        # Nếu không có rate, hiển thị contact
        contact_tg = sheet_manager.get_config('contact_telegram') or "t.me/..."
        contact_zalo = sheet_manager.get_config('contact_zalo') or "09xxx"
        
        keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data='rates')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ *Hiện chưa có giá cho tuyến {route_name}*\n\n"
            f"Vui lòng liên hệ trực tiếp để được báo giá:\n"
            f"📱 Telegram: {contact_tg}\n"
            f"📲 Zalo: {contact_zalo}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Format kết quả
    msg = f"📊 *Bảng giá {route_name}*\n"
    msg += f"POL: {pol} → POD: {pod}\n"
    msg += "─" * 30 + "\n\n"
    
    for rate in rates[:5]:  # Chỉ show 5 rate mới nhất
        msg += f"*{rate.get('Carrier', 'N/A')}*\n"
        msg += f"20GP: ${rate.get('20GP', 'N/A')} | 40GP: ${rate.get('40GP', 'N/A')}\n"
        msg += f"40HC: ${rate.get('40HC', 'N/A')}\n"
        msg += f"Valid: {rate.get('Valid_To', 'N/A')}\n"
        msg += f"📝 {rate.get('Notes', '')}\n"
        msg += "─" * 20 + "\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data='rates')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def show_space_detail(query, pod_code):
    """Hiển thị chi tiết space cho POD đã chọn"""
    # Map pod code sang tên đầy đủ
    pod_map = {
        'lax': 'Los Angeles (LAX)',
        'nyc': 'New York (NYC)',
        'rtm': 'Rotterdam (RTM)',
        'tyo': 'Tokyo (TYO)',
        'bus': 'Busan (BUS)'
    }
    
    pod_name = pod_map.get(pod_code, pod_code.upper())
    
    # Lấy dữ liệu từ sheet
    spaces = sheet_manager.get_space(pod=pod_name)
    
    if not spaces:
        contact_tg = sheet_manager.get_config('contact_telegram') or "t.me/..."
        
        keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data='space')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ *Hiện chưa có thông tin space cho {pod_name}*\n\n"
            f"Liên hệ để được cập nhật nhanh nhất:\n"
            f"📱 Telegram: {contact_tg}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Format kết quả
    msg = f"🛳 *Space còn trống - {pod_name}*\n"
    msg += "─" * 30 + "\n\n"
    
    for space in spaces[:5]:
        msg += f"⚓ *{space.get('Vessel', 'N/A')}*\n"
        msg += f"ETD: {space.get('ETD', 'N/A')} | ETA: {space.get('ETA', 'N/A')}\n"
        msg += f"20': {space.get('Space_20', '0')} | 40': {space.get('Space_40', '0')}\n"
        msg += f"Status: {space.get('Status', 'N/A')}\n"
        msg += "─" * 20 + "\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data='space')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def show_routes(query):
    """Hiển thị các tuyến đang có"""
    routes = [
        "🇺🇸 **Mỹ**",
        "  • HCM → LAX (West Coast)",
        "  • HCM → NYC (East Coast)",
        "  • HCM → SAV (Savannah)",
        "",
        "🇪🇺 **Châu Âu**",
        "  • HCM → RTM (Rotterdam)",
        "  • HCM → HAM (Hamburg)",
        "  • HCM → FEL (Felixstowe)",
        "",
        "🇯🇵 **Nhật Bản**",
        "  • HCM → TYO (Tokyo)",
        "  • HCM → OSA (Osaka)",
        "",
        "🇰🇷 **Hàn Quốc**",
        "  • HCM → BUS (Busan)",
        "  • HCM → INC (Incheon)"
    ]
    
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🗺 *Các tuyến đang khai thác*\n\n" + "\n".join(routes),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_contact(query):
    """Hiển thị thông tin liên hệ"""
    contact_tg = sheet_manager.get_config('contact_telegram') or "t.me/..."
    contact_zalo = sheet_manager.get_config('contact_zalo') or "09xxx"
    company = sheet_manager.get_config('company_name') or "Công ty chúng tôi"
    
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📞 *Liên hệ tư vấn*\n\n"
        f"🏢 {company}\n\n"
        f"📱 *Telegram:* {contact_tg}\n"
        f"📲 *Zalo:* {contact_zalo}\n\n"
        f"⏰ *Thời gian làm việc:*\n"
        f"Thứ 2 - Thứ 6: 8:00 - 17:30\n"
        f"Thứ 7: 8:00 - 12:00",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn văn bản từ user"""
    text = update.message.text.lower()
    user = update.effective_user
    
    # Xử lý các từ khóa đơn giản
    if any(word in text for word in ['giá', 'rate', 'bảng giá']):
        await show_rates_menu(update.message)
    elif any(word in text for word in ['space', 'còn chỗ', 'tàu']):
        await show_space_menu(update.message)
    elif any(word in text for word in ['liên hệ', 'contact', 'tư vấn']):
        await show_contact(update.message)
    elif any(word in text for word in ['tuyến', 'route', 'đi']):
        await show_routes(update.message)
    else:
        # Không hiểu, gợi ý dùng menu
        keyboard = [[InlineKeyboardButton("📋 Xem menu", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ *Xin lỗi, tôi chưa hiểu yêu cầu của bạn.*\n\n"
            "Vui lòng sử dụng menu bên dưới để chọn thông tin cần xem:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # Ghi log
    sheet_manager.log_action(user.id, "MESSAGE", text, "PROCESSED")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quay lại menu chính"""
    query = update.callback_query
    await query.answer()
    await start(query, context)

def main():
    """Main function chạy bot"""
    # Tạo application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Lọc riêng nút back
    application.add_handler(CallbackQueryHandler(back_to_main, pattern='^back$'))
    
    # Chạy bot
    print("🚀 Bot đang chạy...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()