from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes
import os
from sheet_helper import sheet_manager
import tempfile

ADMIN_ID = int(os.getenv('ADMIN_ID'))

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /admin - Chỉ admin mới dùng được"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
        return
    
    keyboard = [
        [InlineKeyboardButton("📤 Upload Excel (RATES)", callback_data='admin_upload_rates')],
        [InlineKeyboardButton("📤 Upload Excel (SPACE)", callback_data='admin_upload_space')],
        [InlineKeyboardButton("📊 Xem thống kê", callback_data='admin_stats')],
        [InlineKeyboardButton("⚙️ Cấu hình", callback_data='admin_config')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👑 *Admin Panel*\n\n"
        "Chọn chức năng:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý callback từ admin menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Bạn không có quyền!")
        return
    
    data = query.data
    
    if data == 'admin_upload_rates':
        context.user_data['upload_type'] = 'RATES'
        await query.edit_message_text(
            "📤 Gửi file Excel (RATES) cho tôi.\n\n"
            "Yêu cầu:\n"
            "• File .xlsx hoặc .xls\n"
            "• Cột: Route, POL, POD, 20GP, 40GP, 40HC, Carrier, Valid_To, Notes"
        )
    
    elif data == 'admin_upload_space':
        context.user_data['upload_type'] = 'SPACE'
        await query.edit_message_text(
            "📤 Gửi file Excel (SPACE) cho tôi.\n\n"
            "Yêu cầu:\n"
            "• File .xlsx hoặc .xls\n"
            "• Cột: Vessel, Voyage, ETD, ETA, POD, Space_20, Space_40, Status, Carrier"
        )
    
    elif data == 'admin_stats':
        # TODO: Thêm thống kê
        await query.edit_message_text("📊 Tính năng đang phát triển...")
    
    elif data == 'admin_config':
        # TODO: Thêm cấu hình
        await query.edit_message_text("⚙️ Tính năng đang phát triển...")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý file upload"""
    user_id = update.effective_user.id
    
    # Chỉ admin mới upload được
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Bạn không có quyền upload file!")
        return
    
    # Kiểm tra đã chọn loại upload chưa
    if 'upload_type' not in context.user_data:
        await update.message.reply_text("❌ Vui lòng chọn loại dữ liệu trước: /admin")
        return
    
    # Download file
    file = await update.message.document.get_file()
    
    # Tạo file tạm
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        await file.download_to_drive(tmp_file.name)
        
        # Update lên Google Sheet
        success, message = sheet_manager.update_from_excel(
            tmp_file.name, 
            context.user_data['upload_type']
        )
        
        # Xóa file tạm
        os.unlink(tmp_file.name)
        
        if success:
            await update.message.reply_text(f"✅ {message}")
        else:
            await update.message.reply_text(f"❌ Lỗi: {message}")
    
    # Xóa trạng thái upload
    del context.user_data['upload_type']

# Hàm để thêm admin handlers vào bot chính
def add_admin_handlers(application):
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern='^admin_'))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))