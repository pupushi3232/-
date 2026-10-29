import asyncio, os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import db
from keyboards import main_menu, catalog_kb, product_kb, cart_kb, admin_kb, del_list_kb

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip()}
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class AddProduct(StatesGroup):
    name=State(); desc=State(); price=State(); emoji=State(); photo=State()
class Checkout(StatesGroup):
    contact=State()

def is_admin(uid): return uid in ADMIN_IDS

@dp.message(Command("start"))
async def start(m: Message):
    await m.answer("💜 <b>NEON SHOP</b> 💜\n\nСекс-гей-шоп в неоновом формате.", reply_markup=main_menu(is_admin(m.from_user.id)), parse_mode="HTML")

@dp.callback_query(F.data=="menu")
async def cb_menu(c: CallbackQuery):
    await c.message.edit_text("💜 <b>NEON SHOP</b> 💜\n\nГлавное меню:", reply_markup=main_menu(is_admin(c.from_user.id)), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data=="catalog")
async def cb_catalog(c: CallbackQuery):
    await c.message.edit_text("🛍 <b>Витрина</b>\nЖми на товар:", reply_markup=catalog_kb(await db.get_products()), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data.startswith("view:"))
async def cb_view(c: CallbackQuery):
    pid = int(c.data.split(":")[1])
    _, name, desc, price, emoji, photo = await db.get_product(pid)
    text = f"{emoji} <b>{name}</b>\n\n{desc}\n\n💰 <b>{price}₽</b>"
    if photo:
        await c.message.answer_photo(photo, caption=text, reply_markup=product_kb(pid), parse_mode="HTML")
    else:
        await c.message.edit_text(text, reply_markup=product_kb(pid), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data.startswith("add:"))
async def cb_add(c: CallbackQuery):
    pid = int(c.data.split(":")[1])
    await db.add_to_cart(c.from_user.id, pid)
    p = await db.get_product(pid)
    await c.answer(f"{p[4]} {p[1]} добавлен!")

def cart_text(items):
    if not items: return "🛒 Корзина пуста."
    lines = ["🛒 <b>Корзина:</b>\n"]; total = 0
    for pid,name,price,emoji,qty in items:
        s = price*qty; total += s
        lines.append(f"{emoji} {name} × {qty} = <b>{s}₽</b>")
    lines.append(f"\n💰 Итого: <b>{total}₽</b>")
    return "\n".join(lines)

@dp.callback_query(F.data=="cart")
async def cb_cart(c: CallbackQuery):
    items = await db.get_cart(c.from_user.id)
    await c.message.edit_text(cart_text(items), reply_markup=cart_kb(items), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data.startswith("del:"))
async def cb_del(c: CallbackQuery):
    pid = int(c.data.split(":")[1])
    await db.dec_cart(c.from_user.id, pid)
    items = await db.get_cart(c.from_user.id)
    await c.message.edit_text(cart_text(items), reply_markup=cart_kb(items), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data=="revenue")
async def cb_revenue(c: CallbackQuery):
    t = await db.revenue(); g = 100000
    pct = min(100, int(t/g*100)); bar = "█"*(pct//10) + "░"*(10-pct//10)
    await c.message.edit_text(f"💰 <b>Выручка</b>\n\nСобрано: <b>{t}₽</b> из <b>{g}₽</b>\n<code>{bar}</code> {pct}%",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")]]), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data=="checkout")
async def cb_checkout(c: CallbackQuery, state: FSMContext):
    items = await db.get_cart(c.from_user.id)
    if not items:
        await c.answer("Корзина пуста!", show_alert=True); return
    await state.set_state(Checkout.contact)
    await c.message.edit_text("📞 Отправь контакт:"); await c.answer()

@dp.message(Checkout.contact)
async def process_contact(m: Message, state: FSMContext):
    items = await db.get_cart(m.from_user.id)
    total = sum(price*qty for _,_,price,_,qty in items)
    stars = max(1, total//2)
    await state.clear()
    await m.answer_invoice(title="Заказ NEON SHOP", description=f"Товаров: {len(items)}", payload=f"order:{m.from_user.id}",
                           provider_token="", currency="XTR", prices=[LabeledPrice(label="Заказ", amount=stars)])

@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def on_paid(m: Message):
    items = await db.get_cart(m.from_user.id)
    total = sum(price*qty for _,_,price,_,qty in items)
    oid = await db.create_order(m.from_user.id, items, m.from_user.username or "—", total)
    await db.mark_paid(oid); await db.clear_cart(m.from_user.id)
    await m.answer(f"✅ <b>Оплачено!</b>\nЗаказ №{oid} на {total}₽", reply_markup=main_menu(is_admin(m.from_user.id)), parse_mode="HTML")

@dp.callback_query(F.data=="admin")
async def cb_admin(c: CallbackQuery):
    if not is_admin(c.from_user.id): return await c.answer("Нет доступа", show_alert=True)
    await c.message.edit_text("⚙️ <b>Админка</b>", reply_markup=admin_kb(), parse_mode="HTML"); await c.answer()

@dp.callback_query(F.data=="admin_add")
async def cb_admin_add(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id): return await c.answer("Нет доступа", show_alert=True)
    await state.set_state(AddProduct.name); await c.message.edit_text("Название:"); await c.answer()

@dp.message(AddProduct.name)
async def ap_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text); await state.set_state(AddProduct.desc); await m.answer("Описание:")

@dp.message(AddProduct.desc)
async def ap_desc(m: Message, state: FSMContext):
    await state.update_data(desc=m.text); await state.set_state(AddProduct.price); await m.answer("Цена:")

@dp.message(AddProduct.price)
async def ap_price(m: Message, state: FSMContext):
    if not m.text.isdigit(): return await m.answer("Число:")
    await state.update_data(price=int(m.text)); await state.set_state(AddProduct.emoji); await m.answer("Эмодзи:")

@dp.message(AddProduct.emoji)
async def ap_emoji(m: Message, state: FSMContext):
    await state.update_data(emoji=m.text); await state.set_state(AddProduct.photo); await m.answer("Фото или '-':")

@dp.message(AddProduct.photo, F.photo | F.text)
async def ap_photo(m: Message, state: FSMContext):
    photo = m.photo[-1].file_id if m.photo else None
    d = await state.get_data()
    await db.add_product(d["name"], d["desc"], d["price"], d["emoji"], photo)
    await state.clear()
    await m.answer("✅ Товар добавлен!", reply_markup=main_menu(is_admin(m.from_user.id)))

@dp.callback_query(F.data=="admin_del_list")
async def cb_del_list(c: CallbackQuery):
    if not is_admin(c.from_user.id): return await c.answer("Нет доступа", show_alert=True)
    await c.message.edit_text("Удалить:", reply_markup=del_list_kb(await db.get_products())); await c.answer()

@dp.callback_query(F.data.startswith("admin_del:"))
async def cb_del_prod(c: CallbackQuery):
    if not is_admin(c.from_user.id): return await c.answer("Нет доступа", show_alert=True)
    await db.del_product(int(c.data.split(":")[1]))
    await c.message.edit_text("Удалено. Осталось:", reply_markup=del_list_kb(await db.get_products())); await c.answer()

@dp.callback_query(F.data=="admin_orders")
async def cb_orders(c: CallbackQuery):
    if not is_admin(c.from_user.id): return await c.answer("Нет доступа", show_alert=True)
    orders = await db.all_orders()
    text = "📦 <b>Заказы:</b>\n\n" + ("\n".join(f"№{o[0]} | {o[2]}₽ | {o[4]}" for o in orders) if orders else "Пусто")
    await c.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin")]]), parse_mode="HTML")
    await c.answer()

async def main():
    await db.init_db(); await db.seed_products()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
