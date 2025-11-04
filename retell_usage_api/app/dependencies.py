from collections.abc import AsyncGenerator

from fastapi import Depends

from .config import Settings, get_settings
from .services.retell_client import RetellClient
from .services.usage_service import UsageService


async def get_usage_service(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[UsageService, None]:
    client = RetellClient(settings)
    service = UsageService(client)
    try:
        yield service
    finally:
        await client.close()
