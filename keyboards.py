from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu(is_admin=False):
    kb = [[InlineKeyboardButton(text="🛍 Витрина", callback_data="catalog")],
          [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
           InlineKeyboardButton(text="💰 Выручка", callback_data="revenue")]]
    if is_admin: kb.append([InlineKeyboardButton(text="⚙️ Админка", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def catalog_kb(products):
    rows = [[InlineKeyboardButton(text=f"{p[4]} {p[1]} — {p[3]}₽", callback_data=f"view:{p[0]}")] for p in products]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def product_kb(pid):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ В корзину", callback_data=f"add:{pid}")],
                                                 [InlineKeyboardButton(text="⬅️ К витрине", callback_data="catalog")]])

def cart_kb(items):
    rows = [[InlineKeyboardButton(text=f"❌ {i[3]} {i[1]} x{i[4]}", callback_data=f"del:{i[0]}")] for i in items]
    rows.append([InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_del_list")],
        [InlineKeyboardButton(text="📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")]])

def del_list_kb(products):
    rows = [[InlineKeyboardButton(text=f"🗑 {p[4]} {p[1]}", callback_data=f"admin_del:{p[0]}")] for p in products]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)