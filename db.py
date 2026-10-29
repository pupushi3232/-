import aiosqlite
DB_PATH = "shop.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, desc TEXT, price INTEGER NOT NULL, emoji TEXT DEFAULT '💜', photo TEXT);
        CREATE TABLE IF NOT EXISTS carts (user_id INTEGER, product_id INTEGER, qty INTEGER DEFAULT 1, PRIMARY KEY (user_id, product_id));
        CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, total INTEGER, contact TEXT, status TEXT DEFAULT 'new', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS order_items (order_id INTEGER, product_id INTEGER, qty INTEGER, price INTEGER);
        """)
        await db.commit()

async def seed_products():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM products")
        (c,) = await cur.fetchone()
        if c == 0:
            await db.executemany("INSERT INTO products (name,desc,price,emoji) VALUES (?,?,?,?)", [
                ("Неоновый набор","Свечи, смазка, аксессуары",2490,"💜"),
                ("Кибер-игрушка","Вибрация 10 режимов, USB",5900,"🔮"),
                ("Поп-арт бельё","Комплект, светится в темноте",3200,"🩷"),
                ("Набор для пар","Всё для двоих",7800,"💞"),
                ("Смазка Neon Glow","Светится под УФ",990,"✨"),
            ])
            await db.commit()

async def get_products():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id,name,desc,price,emoji,photo FROM products")
        return await cur.fetchall()

async def get_product(pid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id,name,desc,price,emoji,photo FROM products WHERE id=?", (pid,))
        return await cur.fetchone()

async def add_to_cart(uid, pid, qty=1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO carts (user_id,product_id,qty) VALUES (?,?,?) ON CONFLICT(user_id,product_id) DO UPDATE SET qty=qty+excluded.qty", (uid,pid,qty))
        await db.commit()

async def dec_cart(uid, pid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE carts SET qty=qty-1 WHERE user_id=? AND product_id=?", (uid,pid))
        await db.execute("DELETE FROM carts WHERE qty<=0")
        await db.commit()

async def get_cart(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT p.id,p.name,p.price,p.emoji,c.qty FROM carts c JOIN products p ON p.id=c.product_id WHERE c.user_id=?", (uid,))
        return await cur.fetchall()

async def clear_cart(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM carts WHERE user_id=?", (uid,))
        await db.commit()

async def create_order(uid, items, contact, total):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("INSERT INTO orders (user_id,total,contact) VALUES (?,?,?)", (uid,total,contact))
        oid = cur.lastrowid
        await db.executemany("INSERT INTO order_items (order_id,product_id,qty,price) VALUES (?,?,?,?)", [(oid,pid,qty,price) for pid,_,price,_,qty in items])
        await db.commit()
        return oid

async def revenue():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status='paid'")
        (s,) = await cur.fetchone()
        return s

async def mark_paid(oid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status='paid' WHERE id=?", (oid,))
        await db.commit()

async def add_product(name,desc,price,emoji,photo):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO products (name,desc,price,emoji,photo) VALUES (?,?,?,?,?)", (name,desc,price,emoji,photo))
        await db.commit()

async def del_product(pid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM products WHERE id=?", (pid,))
        await db.commit()

async def all_orders():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id,user_id,total,contact,status,created_at FROM orders ORDER BY id DESC LIMIT 20")
        return await cur.fetchall()