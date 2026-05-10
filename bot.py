import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler
)

# =====================
# KONFIGURASI - EDIT BAGIAN INI
# =====================
BOT_TOKEN = "ISI_TOKEN_BOT_KAMU"       # Token dari BotFather
ADMIN_USERNAME = "clintgg"              # Username Telegram kamu (tanpa @)
ADMIN_CHAT_ID = None                    # Akan diisi otomatis saat kamu /start

PRODUCTS = {
    "akun_2hari": {
        "name": "Akun 2 Hari",
        "price": 2500,
        "file": "akun.txt"
    }
}

QRIS_IMAGE = "qris.jpg"   # Nama file gambar QRIS kamu

# =====================
# STATE CONVERSATION
# =====================
PILIH_PRODUK, PILIH_KUANTITI, TUNGGU_BUKTI = range(3)

# Simpan data pesanan sementara
pesanan_aktif = {}

logging.basicConfig(level=logging.INFO)

BANNER = (
    "╔══════════════════════╗\n"
    "║   🎵 ZHANG TIKTOKER  ║\n"
    "║   Toko Akun Digital  ║\n"
    "╚══════════════════════╝\n\n"
    "👋 Selamat datang!\n"
    "Kami menyediakan akun digital\n"
    "berkualitas dengan harga terjangkau.\n\n"
    "⚡ Proses cepat & aman\n"
    "💳 Bayar via QRIS / GoPay / OVO\n\n"
    "Pilih menu di bawah untuk mulai:"
)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🛒 Pesan Sekarang")],
        [KeyboardButton("❓ Bantuan")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_CHAT_ID

    # Simpan chat_id admin otomatis
    if update.effective_user.username == ADMIN_USERNAME:
        ADMIN_CHAT_ID = update.effective_chat.id
        await update.message.reply_text(
            f"Halo Admin! Chat ID kamu sudah tersimpan: {ADMIN_CHAT_ID}\n"
            "Bot siap menerima pesanan. ✅"
        )
        return ConversationHandler.END

    await update.message.reply_text(BANNER, reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

# =====================
# TOMBOL PESAN SEKARANG
# =====================
async def pesan_sekarang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for key, produk in PRODUCTS.items():
        keyboard.append([InlineKeyboardButton(
            f"{produk['name']} - Rp {produk['price']:,}",
            callback_data=f"pilih_{key}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🛍️ *Pilih produk yang kamu inginkan:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return PILIH_PRODUK

# =====================
# TOMBOL BANTUAN
# =====================
async def bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ *Bantuan*\n\n"
        "Cara pesan:\n"
        "1️⃣ Tap *Pesan Sekarang*\n"
        "2️⃣ Pilih produk & kuantiti\n"
        "3️⃣ Bayar via QRIS\n"
        "4️⃣ Kirim bukti bayar\n"
        "5️⃣ Produk langsung dikirim!\n\n"
        "Ada pertanyaan lain? Hubungi admin: @clintgg",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# =====================
# PILIH PRODUK
# =====================
async def pilih_produk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data.replace("pilih_", "")
    produk = PRODUCTS.get(key)

    if not produk:
        await query.edit_message_text("Produk tidak ditemukan.")
        return ConversationHandler.END

    context.user_data["produk_key"] = key
    context.user_data["produk"] = produk

    keyboard = [
        [InlineKeyboardButton("1", callback_data="qty_1"),
         InlineKeyboardButton("2", callback_data="qty_2"),
         InlineKeyboardButton("3", callback_data="qty_3")],
        [InlineKeyboardButton("4", callback_data="qty_4"),
         InlineKeyboardButton("5", callback_data="qty_5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Kamu memilih: *{produk['name']}*\nHarga satuan: Rp {produk['price']:,}\n\nPilih kuantiti:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return PILIH_KUANTITI

# =====================
# PILIH KUANTITI
# =====================
async def pilih_kuantiti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    qty = int(query.data.replace("qty_", ""))
    produk = context.user_data["produk"]
    total = produk["price"] * qty

    context.user_data["qty"] = qty
    context.user_data["total"] = total

    user = update.effective_user
    pesanan_aktif[user.id] = {
        "user_id": user.id,
        "username": user.username or user.first_name,
        "produk": produk["name"],
        "qty": qty,
        "total": total,
        "file": produk["file"]
    }

    # Kirim gambar QRIS
    try:
        with open(QRIS_IMAGE, "rb") as qris:
            await query.message.reply_photo(
                photo=qris,
                caption=(
                    f"🛍️ *Pesanan Kamu:*\n"
                    f"Produk: {produk['name']}\n"
                    f"Kuantiti: {qty}\n"
                    f"Total: Rp {total:,}\n\n"
                    f"💳 Silakan bayar via QRIS di atas.\n\n"
                    f"Setelah bayar, kirim *screenshot bukti pembayaran* ke sini ya!"
                ),
                parse_mode="Markdown"
            )
    except FileNotFoundError:
        await query.message.reply_text(
            f"🛍️ *Pesanan Kamu:*\n"
            f"Produk: {produk['name']}\n"
            f"Kuantiti: {qty}\n"
            f"Total: Rp {total:,}\n\n"
            f"💳 Bayar via QRIS ke admin.\n\n"
            f"Setelah bayar, kirim *screenshot bukti pembayaran* ke sini ya!",
            parse_mode="Markdown"
        )

    return TUNGGU_BUKTI

# =====================
# TERIMA BUKTI BAYAR
# =====================
async def terima_bukti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pesanan = pesanan_aktif.get(user.id)

    if not pesanan:
        await update.message.reply_text("Silakan mulai pesanan dulu dengan menekan tombol 🛒 Pesan Sekarang")
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ Bukti pembayaran diterima!\nSedang kami verifikasi ya, tunggu sebentar..."
    )

    # Notif ke admin
    if ADMIN_CHAT_ID:
        caption = (
            f"📦 *PESANAN BARU!*\n"
            f"👤 Username: @{pesanan['username']}\n"
            f"🛍️ Produk: {pesanan['produk']}\n"
            f"🔢 Kuantiti: {pesanan['qty']}\n"
            f"💰 Total: Rp {pesanan['total']:,}\n\n"
            f"Untuk konfirmasi, ketik:\n"
            f"`/konfirmasi {user.id}`"
        )
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=update.message.photo[-1].file_id,
                caption=caption,
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=caption,
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "⚠️ Admin belum terdaftar. Minta admin untuk /start dulu."
        )

    return ConversationHandler.END

# =====================
# ADMIN: KONFIRMASI PESANAN
# =====================
async def konfirmasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("Kamu bukan admin.")
        return

    if not context.args:
        await update.message.reply_text("Format: /konfirmasi [user_id]")
        return

    user_id = int(context.args[0])
    pesanan = pesanan_aktif.get(user_id)

    if not pesanan:
        await update.message.reply_text("Pesanan tidak ditemukan.")
        return

    # Kirim file produk ke pembeli
    try:
        with open(pesanan["file"], "rb") as f:
            await context.bot.send_document(
                chat_id=user_id,
                document=f,
                caption=(
                    f"✅ *Pembayaran dikonfirmasi!*\n"
                    f"Terima kasih sudah membeli *{pesanan['produk']}*!\n\n"
                    f"Ini file produk kamu 👆\n"
                    f"Jika ada pertanyaan, hubungi admin."
                ),
                parse_mode="Markdown"
            )
        await update.message.reply_text(f"✅ Produk berhasil dikirim ke @{pesanan['username']}!")
        del pesanan_aktif[user_id]
    except FileNotFoundError:
        await update.message.reply_text(
            f"❌ File '{pesanan['file']}' tidak ditemukan. Pastikan file ada di folder yang sama."
        )

# =====================
# CANCEL
# =====================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pesanan dibatalkan. Tap 🛒 Pesan Sekarang untuk mulai lagi.")
    return ConversationHandler.END

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🛒 Pesan Sekarang$"), pesan_sekarang),
        ],
        states={
            PILIH_PRODUK: [CallbackQueryHandler(pilih_produk, pattern="^pilih_")],
            PILIH_KUANTITI: [CallbackQueryHandler(pilih_kuantiti, pattern="^qty_")],
            TUNGGU_BUKTI: [MessageHandler(filters.PHOTO | filters.Document.ALL, terima_bukti)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^❓ Bantuan$"), bantuan))
    app.add_handler(CommandHandler("konfirmasi", konfirmasi))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
