import aiosqlite


class DataBase:

    def __init__(self):
        self.db_name = "test-database.db"

    async def create_table(self):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.cursor()

                query = """
                CREATE TABLE IF NOT EXISTS users(
                    member_id INTEGER PRIMARY KEY,
                    balance BIGINT NOT NULL DEFAULT 300,
                    reputation INTEGER NOT NULL DEFAULT 0,
                    xp INTEGER NOT NULL DEFAULT 0,
                    level INTEGER NOT NULL DEFAULT 1,
                    territory INTEGER NOT NULL DEFAULT 0,
                    population INTEGER NOT NULL DEFAULT 0,
                    army INTEGER NOT NULL DEFAULT 0,
                    education_level INTEGER NOT NULL DEFAULT 1,
                    healthcare_level INTEGER NOT NULL DEFAULT 1,
                    tourism_level INTEGER NOT NULL DEFAULT 1,
                    economy_level INTEGER NOT NULL DEFAULT 1,
                    capital TEXT DEFAULT 'Нету столицы',
                    sanctions_level INTEGER NOT NULL DEFAULT 0,
                    member_name TEXT,
                    member_display_name TEXT
                );
                CREATE TABLE IF NOT EXISTS shop(
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cost BIGINT NOT NULL,
                    type TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS inventory(
                    member_id INTEGER,
                    item_id INTEGER,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    member_name TEXT NOT NULL,
                    member_display_name TEXT NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES shop(item_id)
                );
                """
                await cursor.executescript(query)
                await db.commit()

                # Добавление предустановленных предметов
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('Солдат', 100, 'войска')")
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('Танк', 1000, 'техника')")
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('Школа', 5000, 'образование')")
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('ВУЗ', 10000, 'образование')")
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('Больница', 8000, 'здравоохранение')")
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('Аптека', 3000, 'здравоохранение')")
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('Отель', 7000, 'туризм')")
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('Музей', 6000, 'туризм')")
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('Фабрика', 15000, 'экономика')")
                await cursor.execute("INSERT INTO shop(name, cost, type) VALUES('Банк', 20000, 'экономика')")
                await db.commit()
        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")

    async def add_item_to_inventory(self, member_id: int, item_id: int, quantity: int, member_name: str = "", member_display_name: str = ""):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.cursor()

                # Получаем название предмета из таблицы shop
                await cursor.execute(
                    "SELECT name FROM shop WHERE item_id = ?",
                    [item_id]
                )
                item = await cursor.fetchone()
                if not item:
                    return  # Предмет не найден, выходим из функции

                item_name = item['name']

                # Проверяем, есть ли уже такой предмет в инвентаре
                await cursor.execute(
                    "SELECT quantity FROM inventory WHERE member_id = ? AND item_id = ?",
                    [member_id, item_id]
                )
                existing_item = await cursor.fetchone()

                if existing_item:
                    new_quantity = existing_item['quantity'] + quantity
                    await cursor.execute(
                        "UPDATE inventory SET quantity = ?, member_name = ?, member_display_name = ? WHERE member_id = ? AND item_id = ?",
                        [new_quantity, member_name, member_display_name, member_id, item_id]
                    )
                else:
                    await cursor.execute(
                        """
                        INSERT INTO inventory(member_id, item_id, item_name, quantity, member_name, member_display_name)
                        VALUES(?, ?, ?, ?, ?, ?)
                        """,
                        [member_id, item_id, item_name, quantity, member_name, member_display_name]
                    )

                # Обновление данных об армии в таблице users
                if item_id in [1, 2]:  # Предположим, что 1 - Солдат, 2 - Танк
                    await cursor.execute(
                        "UPDATE users SET army = army + ? WHERE member_id = ?",
                        [quantity, member_id]
                    )

                await db.commit()
        except Exception as e:
            print(f"Ошибка при добавлении предмета в инвентарь: {e}")

    async def get_inventory(self, member_id: int):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.cursor()
                await cursor.execute(
                    """
                    SELECT item_name, quantity
                    FROM inventory
                    WHERE member_id = ?
                    """,
                    [member_id]
                )
                return await cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении инвентаря: {e}")
            return []

    async def item_exists(self, name: str):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.cursor()
                await cursor.execute(
                    "SELECT 1 FROM shop WHERE name = ?",
                    [name]
                )
                return await cursor.fetchone() is not None
        except Exception as e:
            print(f"Ошибка при проверке существования предмета: {e}")
            return False

    async def insert_new_item(self, name: str, cost: int):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.cursor()

                await cursor.execute(
                    "INSERT INTO shop(name, cost) VALUES(?, ?)",
                    [name, cost]
                )
                await db.commit()
        except Exception as e:
            print(f"Ошибка при добавлении нового предмета: {e}")

    async def delete_item_from_shop(self, name: str):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.cursor()

                await cursor.execute(
                    "DELETE FROM shop WHERE name = ?",
                    [name]
                )
                await db.commit()
        except Exception as e:
            print(f"Ошибка при удалении предмета из магазина: {e}")

    async def get_item_by_name(self, name: str):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.cursor()

                await cursor.execute(
                    "SELECT * FROM shop WHERE name = ?",
                    [name]
                )
                result = await cursor.fetchone()
                return result
        except Exception as e:
            print(f"Ошибка при получении предмета по имени: {e}")
            return None

    async def get_shop_data(self, *, all_data: bool = False):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.cursor()

                if all_data:
                    await cursor.execute("SELECT * FROM shop")
                    result = await cursor.fetchall()
                else:
                    result = None

                return result
        except Exception as e:
            print(f"Ошибка при получении данных магазина: {e}")
            return []

    async def get_data(self, member_id=None, all_data=False, filters=""):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.cursor()
                
                if all_data:
                    query = f"SELECT * FROM users {filters}"
                    await cursor.execute(query)
                else:
                    query = "SELECT * FROM users WHERE member_id = ?"
                    await cursor.execute(query, (member_id,))
                
                data = await cursor.fetchall()
                return data
        except Exception as e:
            return []

    async def update_user(self, query: str, values: list):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.cursor()
                await cursor.execute(query, values)
                await db.commit()
        except Exception as e:
            print(f"Ошибка при обновлении данных пользователя: {e}")

    async def insert_new_member(self, member_id: int, member_name: str, member_display_name: str):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.cursor()

                await cursor.execute(
                    "SELECT * FROM users WHERE member_id = ?",
                    [member_id]
                )
                if await cursor.fetchone() is None:
                    await cursor.execute(
                        """
                        INSERT INTO users(member_id, member_name, member_display_name)
                        VALUES(?, ?, ?)
                        """,
                        [member_id, member_name, member_display_name]
                    )
                else:
                    await cursor.execute(
                        """
                        UPDATE users
                        SET member_name = ?, member_display_name = ?
                        WHERE member_id = ?
                        """,
                        [member_name, member_display_name, member_id]
                    )
                await db.commit()
        except Exception as e:
            print(f"Ошибка при добавлении нового участника: {e}")

    async def update_member_display_name(self, member_id: int, member_display_name: str):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.cursor()
                await cursor.execute(
                    """
                    UPDATE users
                    SET member_display_name = ?
                    WHERE member_id = ?
                    """,
                    [member_display_name, member_id]
                )
                await db.commit()
        except Exception as e:
            print(f"Ошибка при обновлении отображаемого имени пользователя: {e}")

    async def update_inventory_display_name(self, member_id: int, member_display_name: str):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.cursor()
                await cursor.execute(
                    """
                    UPDATE inventory
                    SET member_display_name = ?
                    WHERE member_id = ?
                    """,
                    [member_display_name, member_id]
                )
                await db.commit()
        except Exception as e:
            print(f"Ошибка при обновлении отображаемого имени в инвентаре: {e}")

    async def update_inventory_quantity(self, member_id: int, item_id: int, new_quantity: int):
        try:
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.cursor()
                if new_quantity > 0:
                    await cursor.execute(
                        "UPDATE inventory SET quantity = ? WHERE member_id = ? AND item_id = ?",
                        [new_quantity, member_id, item_id]
                    )
                else:
                    await cursor.execute(
                        "DELETE FROM inventory WHERE member_id = ? AND item_id = ?",
                        [member_id, item_id]
                    )

                # Обновление данных об армии в таблице users
                if item_id in [1, 2]:  # Предположим, что 1 - Солдат, 2 - Танк
                    await cursor.execute(
                        "UPDATE users SET army = army - ? WHERE member_id = ?",
                        [new_quantity, member_id]
                    )

                await db.commit()
        except Exception as e:
            print(f"Ошибка при обновлении количества предметов в инвентаре: {e}")
