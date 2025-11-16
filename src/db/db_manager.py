import sqlite3
import logging
from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import List, Optional

from src.model.chat import Chat
from src.core.constants import CHATS_DEFAULT
from src.model.messages import Message, MessageType

logger = logging.getLogger(__name__)


class DbManager:
    TABLE_MESSAGES = "messages"
    TABLE_CHATS = "chats"

    def __init__(self, db_dir: Optional[Path] = None) -> None:
        if db_dir is None:
            from src.core.configs import settings
            db_dir = settings.DB_DIR

        self.db_dir: Path = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path: Path = self.db_dir / "app.db"

        self._init_db()

    def _get_connection(self) -> Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        connection: Connection = self._get_connection()
        cursor: Cursor = connection.cursor()

        try:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.TABLE_MESSAGES} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    agent_id TEXT,
                    id_chat TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    request_time INTEGER NOT NULL,
                    price INTEGER NOT NULL,
                    meta TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.TABLE_CHATS} (
                    id_chat TEXT PRIMARY KEY,
                    name TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute(f'''SELECT COUNT(*) FROM {self.TABLE_CHATS}''')
            existing_count = cursor.fetchone()[0]

            if existing_count == 0:
                for chat in CHATS_DEFAULT:
                    cursor.execute(
                        "INSERT INTO chats (id_chat, name) VALUES (?, ?)",
                        (chat.id, chat.name)
                    )
                connection.commit()
                logger.info(f"Default chats created: {CHATS_DEFAULT}")

            connection.commit()
            logger.info(f"Basis initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"DB initialization error: {e}")
        finally:
            connection.close()

    async def add_message(self, message: Message) -> Optional[Message]:
        connection = self._get_connection()
        cursor = connection.cursor()

        try:
            # Проверка наличия обязательных полей
            if not all([message.id_chat, message.session_id]):
                raise ValueError("Обязательные поля отсутствуют: id_chat или session_id")
            
            cursor.execute(
                f'''
                INSERT INTO {self.TABLE_MESSAGES} 
                (id_chat, session_id, message_type, agent_id, name, timestamp, message, prompt_tokens,completion_tokens,request_time,price,meta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                    message.id_chat,
                    message.session_id,
                    message.message_type.value,
                    message.agent_id,
                    message.name,
                    message.timestamp,
                    message.message,
                    message.prompt_tokens,
                    message.completion_tokens,
                    message.request_time,
                    message.price,
                    message.meta,
                ))
            connection.commit()
            message_id = cursor.lastrowid

            message_with_id = message.model_copy(update={"id": message_id})

            logger.info(f"Message added: ID={message_with_id.id}, chat={message_with_id.id_chat}")
            return message_with_id
        except Exception as e:
            logger.error(f"DB insert error: {e}")
            raise
        finally:
            connection.close()

    async def get_messages(
            self,
            id_chat: Optional[str] = None,
            session_id: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[Message]:
        connection: Connection = self._get_connection()
        cursor: Cursor = connection.cursor()

        try:
            query: str = f'SELECT * FROM {self.TABLE_MESSAGES}'
            params: list = []

            conditions = []
            if id_chat:
                conditions.append("id_chat = ?")
                params.append(id_chat)

            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)

            if len(conditions) > 0:
                query += " WHERE " + " AND ".join(conditions)

            query += ' ORDER BY created_at ASC'

            if limit:
                query += ' LIMIT ?'
                params.append(limit)

            cursor.execute(query, params)
            rows: list = cursor.fetchall()

            messages = [
                Message(
                    id=row['id'],
                    id_chat=row['id_chat'],
                    session_id=row['session_id'],
                    message_type=MessageType(row['message_type']),
                    agent_id=row['agent_id'],
                    name=row['name'],
                    timestamp=row['timestamp'],
                    message=row['message'],
                    prompt_tokens=row['prompt_tokens'],
                    completion_tokens=row['completion_tokens'],
                    request_time=row['request_time'],
                    price=row['price'],
                    meta=row['meta'],
                )
                for row in rows
            ]

            logger.info(f"{len(messages)} messages retrieved.")
            return messages
        except Exception as e:
            logger.error(f"DB retrieval error: {e}")
            raise
        finally:
            connection.close()

    async def clear_messages(self, id_chat: str) -> None:
        connection = self._get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(f"DELETE FROM {self.TABLE_MESSAGES} WHERE id_chat = ?", (id_chat,))
            connection.commit()
            logger.info(f"Messaging history cleared for chat: {id_chat}")
        except Exception as e:
            logger.error(f"Clear DB error: {e}")
            raise
        finally:
            connection.close()

    async def clear_all_table_messages(self) -> None:
        connection: Connection = self._get_connection()
        cursor: Cursor = connection.cursor()

        try:
            cursor.execute(f'DELETE FROM {self.TABLE_MESSAGES}')
            connection.commit()
            logger.warning(f"Таблица {self.TABLE_MESSAGES} полностью очищена")
        except Exception as e:
            logger.error(f"Ошибка очистки БД: {e}")
            raise
        finally:
            connection.close()

    async def add_chat(self, chat: Chat) -> Optional[str]:
        connection = self._get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "INSERT INTO chats (id_chat, name) VALUES (?, ?)",
                (chat.id, chat.name)
            )
            connection.commit()
            return chat.id
        except Exception as e:
            logger.error(f"Error adding chat: {e}")
            raise
        finally:
            connection.close()

    async def recreate_table_messages(self) -> None:
        connection: Connection = self._get_connection()
        cursor: Cursor = connection.cursor()

        try:
            cursor.execute(f'DROP TABLE IF EXISTS {self.TABLE_MESSAGES}')
            connection.commit()
            logger.warning("Таблица удалена")

            self._init_db()
            logger.info("Таблица пересоздана")
        except Exception as e:
            logger.error(f"Ошибка пересоздания таблицы: {e}")
            raise
        finally:
            connection.close()

    async def get_chats(self) -> List[Chat]:
        connection = self._get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(f"SELECT id_chat, name, created_at FROM {self.TABLE_CHATS}")
            rows = cursor.fetchall()
            return [Chat(id=row["id_chat"], name=row["name"], created_at=row["created_at"]) for row in rows]
        except Exception as e:
            logger.error(f"Error getting chats: {e}")
            raise
        finally:
            connection.close()

    async def update_name_chat(self, id_chat: str, chat_name: Optional[str]) -> bool:
        connection = self._get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                f"UPDATE {self.TABLE_CHATS} SET name = ? WHERE id_chat = ?",
                (chat_name, id_chat)
            )
            connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating chat: {e}")
            return False
        finally:
            connection.close()

    async def remove_all_messages_chat(self, id_chat: str) -> bool:
        connection = self._get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("DELETE FROM chats WHERE id_chat = ?", (id_chat,))
            connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting messages chat: {e}")
            return False
        finally:
            connection.close()


_db_manager: Optional[DbManager] = None

def get_db_manager() -> DbManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DbManager()
    return _db_manager
