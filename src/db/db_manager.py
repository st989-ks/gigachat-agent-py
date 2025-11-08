import sqlite3
import logging
from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import List, Optional

from src.model.messages import Message, MessageType

logger = logging.getLogger(__name__)


class DbManager:
    TABLE_MESSAGES = "messages"

    def __init__(self, db_dir: Optional[Path] = None) -> None:
        if db_dir is None:
            from src.core.configs import settings
            db_dir = settings.DB_DIR

        self.db_dir: Path = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path: Path = self.db_dir / "app.db"

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
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
                    message_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            connection.commit()
            logger.info(f"База данных инициализирована: {self.db_path}")
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
        finally:
            connection.close()

    async def add_message(self, message: Message) -> Optional[Message]:
        connection = self._get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                f'''
                INSERT INTO {self.TABLE_MESSAGES} 
                (session_id, message_type, agent_id, name, timestamp, message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                    message.session_id,
                    message.message_type.value,
                    message.agent_id,
                    message.name,
                    message.timestamp,
                    message.message
                ))
            connection.commit()
            message_id = cursor.lastrowid

            message_with_id = message.model_copy(update={"id": message_id})

            logger.info(f"Сообщение добавлено: ID={message_with_id.id}, session={message_with_id.session_id}")
            return message_with_id
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения: {e}")
            raise
        finally:
            connection.close()

    async def get_messages(
            self,
            session_id: Optional[str] = None,
            agent_id: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[Message]:
        connection: Connection = self._get_connection()
        cursor: Cursor = connection.cursor()

        try:
            query: str = f'SELECT * FROM {self.TABLE_MESSAGES} WHERE 1=1'
            params: list = []

            if session_id:
                query += ' AND session_id = ?'
                params.append(session_id)

            if agent_id:
                query += ' AND agent_id = ?'
                params.append(agent_id)

            query += ' ORDER BY created_at DESC'

            if limit:
                query += ' LIMIT ?'
                params.append(limit)

            cursor.execute(query, params)
            rows: list = cursor.fetchall()

            messages = [
                Message(
                    id=row['id'],
                    session_id=row['session_id'],
                    message_type=MessageType(row['message_type']),
                    agent_id=row['agent_id'],
                    name=row['name'],
                    timestamp=row['timestamp'],
                    message=row['message']
                )
                for row in rows
            ]

            logger.info(f"Получено сообщений: {len(messages)}")
            return messages
        except Exception as e:
            logger.error(f"Ошибка получения сообщений: {e}")
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


_db_manager: Optional[DbManager] = None


def get_db_manager() -> DbManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DbManager()
    return _db_manager
