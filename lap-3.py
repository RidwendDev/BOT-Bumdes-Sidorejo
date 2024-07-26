import csv
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, Filters

# File paths
PRODUCTS_FILE = 'products.csv'
TRANSACTIONS_FILE = 'transactions.csv'

# States for ConversationHandler
(PRODUCT, KODE, HARGA_JUAL, HARGA_BELI, 
 TRANS_PRODUCT, TRANS_KODE, TRANS_JUMLAH, TRANS_TANGGAL, TRANS_JENIS,
 DELETE_PRODUCT, DELETE_TRANSACTION) = range(11)

def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Tambah Produk", callback_data='add_product')],
        [InlineKeyboardButton("Tambah Transaksi", callback_data='add_transaction')],
        [InlineKeyboardButton("Lihat Produk", callback_data='view_products')],
        [InlineKeyboardButton("Lihat Transaksi", callback_data='view_transactions')],
        [InlineKeyboardButton("Hapus Produk", callback_data='delete_product')],
        [InlineKeyboardButton("Hapus Transaksi", callback_data='delete_transaction')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Selamat datang di Bot Inventaris BUMDes Desa Sidorejo. Silakan pilih opsi:', reply_markup=reply_markup)

def button(update: Update, context):
    query = update.callback_query
    query.answer()

    if query.data == 'add_product':
        query.edit_message_text(text="Silakan masukkan nama produk:")
        return PRODUCT
    elif query.data == 'add_transaction':
        query.edit_message_text(text="Silakan masukkan nama produk untuk transaksi:")
        return TRANS_PRODUCT
    elif query.data == 'view_products':
        view_products(update, context)
    elif query.data == 'view_transactions':
        view_transactions(update, context)
    elif query.data == 'delete_product':
        query.edit_message_text(text="Masukkan nomor baris produk yang ingin dihapus:")
        return DELETE_PRODUCT
    elif query.data == 'delete_transaction':
        query.edit_message_text(text="Masukkan nomor baris transaksi yang ingin dihapus:")
        return DELETE_TRANSACTION

def add_product(update: Update, context):
    context.user_data['produk'] = update.message.text
    update.message.reply_text("Masukkan kode produk:")
    return KODE

def add_product_kode(update: Update, context):
    context.user_data['kode_produk'] = update.message.text
    update.message.reply_text("Masukkan harga jual:")
    return HARGA_JUAL

def add_product_harga_jual(update: Update, context):
    context.user_data['harga_jual'] = update.message.text
    update.message.reply_text("Masukkan harga beli:")
    return HARGA_BELI

def add_product_harga_beli(update: Update, context):
    context.user_data['harga_beli'] = update.message.text
    
    # Simpan ke file CSV
    with open(PRODUCTS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([context.user_data['produk'], context.user_data['kode_produk'],
                         context.user_data['harga_jual'], context.user_data['harga_beli']])

    update.message.reply_text("Produk berhasil ditambahkan!")
    return ConversationHandler.END

def add_transaction(update: Update, context):
    context.user_data['produk'] = update.message.text
    update.message.reply_text("Masukkan kode produk:")
    return TRANS_KODE

def add_transaction_kode(update: Update, context):
    context.user_data['kode_produk'] = update.message.text
    # Cari harga jual produk
    with open(PRODUCTS_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[1] == context.user_data['kode_produk']:
                context.user_data['harga_jual'] = float(row[2])
                break
    if 'harga_jual' not in context.user_data:
        update.message.reply_text("Produk tidak ditemukan. Silakan coba lagi.")
        return TRANS_PRODUCT
    update.message.reply_text("Masukkan jumlah unit:")
    return TRANS_JUMLAH

def add_transaction_jumlah(update: Update, context):
    context.user_data['jumlah_unit'] = int(update.message.text)
    context.user_data['total'] = context.user_data['harga_jual'] * context.user_data['jumlah_unit']
    update.message.reply_text("Masukkan tanggal transaksi (format: YYYY-MM-DD):")
    return TRANS_TANGGAL

def add_transaction_tanggal(update: Update, context):
    context.user_data['tanggal'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Pemasukan", callback_data='pemasukan')],
        [InlineKeyboardButton("Pengeluaran", callback_data='pengeluaran')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Pilih jenis transaksi:", reply_markup=reply_markup)
    return TRANS_JENIS

def add_transaction_jenis(update: Update, context):
    query = update.callback_query
    query.answer()

    is_pemasukan = "1" if query.data == 'pemasukan' else "0"
    
    # Simpan ke file CSV
    with open(TRANSACTIONS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([context.user_data['produk'], context.user_data['kode_produk'],
                         context.user_data['jumlah_unit'], context.user_data['tanggal'],
                         context.user_data['harga_jual'], context.user_data['total'],
                         is_pemasukan])

    query.edit_message_text(text="Transaksi berhasil ditambahkan!")
    return ConversationHandler.END

def view_products(update: Update, context):
    try:
        with open(PRODUCTS_FILE, 'r') as f:
            reader = csv.reader(f)
            products = list(reader)
    except FileNotFoundError:
        update.effective_message.reply_text("Belum ada data produk.")
        return

    if not products:
        update.effective_message.reply_text("Belum ada data produk.")
        return

    table = "Daftar Produk:\n\n"
    table += f"{'No.':<5}{'Produk':<15}{'Kode':<10}{'Harga Jual':<15}{'Harga Beli':<15}\n"
    table += "-" * 60 + "\n"
    for i, product in enumerate(products, 1):
        table += f"{i:<5}{product[0]:<15}{product[1]:<10}{product[2]:<15}{product[3]:<15}\n"

    update.effective_message.reply_text(f"```\n{table}\n```", parse_mode='Markdown')

def view_transactions(update: Update, context):
    try:
        with open(TRANSACTIONS_FILE, 'r') as f:
            reader = csv.reader(f)
            transactions = list(reader)
    except FileNotFoundFile:
        update.effective_message.reply_text("Belum ada data transaksi.")
        return

    if not transactions:
        update.effective_message.reply_text("Belum ada data transaksi.")
        return

    table = "Daftar Transaksi:\n\n"
    table += f"{'No.':<5}{'Produk':<15}{'Kode':<10}{'Jumlah':<10}{'Tanggal':<15}{'Harga Jual':<15}{'Total':<15}{'Jenis':<15}\n"
    table += "-" * 100 + "\n"
    for i, transaction in enumerate(transactions, 1):
        if len(transaction) >= 7:
            jenis = "Pemasukan" if transaction[6] == "1" else "Pengeluaran"
        else:
            jenis = "Tidak diketahui"
        
        # Pastikan semua elemen yang diperlukan ada
        produk = transaction[0] if len(transaction) > 0 else ""
        kode = transaction[1] if len(transaction) > 1 else ""
        jumlah = transaction[2] if len(transaction) > 2 else ""
        tanggal = transaction[3] if len(transaction) > 3 else ""
        harga_jual = transaction[4] if len(transaction) > 4 else ""
        total = transaction[5] if len(transaction) > 5 else ""
        
        table += f"{i:<5}{produk:<15}{kode:<10}{jumlah:<10}{tanggal:<15}{harga_jual:<15}{total:<15}{jenis:<15}\n"

    update.effective_message.reply_text(f"```\n{table}\n```", parse_mode='Markdown')

def delete_product(update: Update, context):
    try:
        line_number = int(update.message.text) - 1
        with open(PRODUCTS_FILE, 'r') as f:
            products = list(csv.reader(f))
        
        if 0 <= line_number < len(products):
            deleted_product = products.pop(line_number)
            with open(PRODUCTS_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(products)
            update.message.reply_text(f"Produk {deleted_product[0]} berhasil dihapus.")
        else:
            update.message.reply_text("Nomor baris tidak valid.")
    except ValueError:
        update.message.reply_text("Masukkan nomor baris yang valid.")
    except FileNotFoundError:
        update.message.reply_text("File produk tidak ditemukan.")
    
    return ConversationHandler.END

def delete_transaction(update: Update, context):
    try:
        line_number = int(update.message.text) - 1
        with open(TRANSACTIONS_FILE, 'r') as f:
            transactions = list(csv.reader(f))
        
        if 0 <= line_number < len(transactions):
            deleted_transaction = transactions.pop(line_number)
            with open(TRANSACTIONS_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(transactions)
            update.message.reply_text(f"Transaksi pada tanggal {deleted_transaction[3]} berhasil dihapus.")
        else:
            update.message.reply_text("Nomor baris tidak valid.")
    except ValueError:
        update.message.reply_text("Masukkan nomor baris yang valid.")
    except FileNotFoundError:
        update.message.reply_text("File transaksi tidak ditemukan.")
    
    return ConversationHandler.END

def main():
    updater = Updater("7379581979:AAFgoWwXW6P2U-24xgKVfebyBzaQ5DPQXtA", use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button)],
        states={
            PRODUCT: [MessageHandler(Filters.text & ~Filters.command, add_product)],
            KODE: [MessageHandler(Filters.text & ~Filters.command, add_product_kode)],
            HARGA_JUAL: [MessageHandler(Filters.text & ~Filters.command, add_product_harga_jual)],
            HARGA_BELI: [MessageHandler(Filters.text & ~Filters.command, add_product_harga_beli)],
            TRANS_PRODUCT: [MessageHandler(Filters.text & ~Filters.command, add_transaction)],
            TRANS_KODE: [MessageHandler(Filters.text & ~Filters.command, add_transaction_kode)],
            TRANS_JUMLAH: [MessageHandler(Filters.text & ~Filters.command, add_transaction_jumlah)],
            TRANS_TANGGAL: [MessageHandler(Filters.text & ~Filters.command, add_transaction_tanggal)],
            TRANS_JENIS: [CallbackQueryHandler(add_transaction_jenis)],
            DELETE_PRODUCT: [MessageHandler(Filters.text & ~Filters.command, delete_product)],
            DELETE_TRANSACTION: [MessageHandler(Filters.text & ~Filters.command, delete_transaction)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()