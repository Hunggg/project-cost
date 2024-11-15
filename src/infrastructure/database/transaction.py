from functools import wraps

from loguru import logger
from sqlalchemy.exc import IntegrityError, PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import CTX_SESSION, get_session
from src.infrastructure.errors import DatabaseError


def transaction(coro):
    """This decorator should be used with all coroutines
    that want's access the database for saving a new data.
    """

    @wraps(coro)
    async def inner(*args, **kwargs):
        session: AsyncSession = get_session()
        CTX_SESSION.set(session)

        try:
            result = await coro(*args, **kwargs)
            await session.commit()
            return result
        except DatabaseError as error:
            logger.error(f"Rolling back changes.\n{error}")
            await session.rollback()
            raise DatabaseError
        except (IntegrityError, PendingRollbackError) as error:
            logger.error(f"Rolling back changes.\n{error}")
            await session.rollback()
        finally:
            await session.close()

    return inner
