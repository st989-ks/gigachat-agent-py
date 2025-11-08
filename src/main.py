import asyncio
import logging

import uvicorn




async def main() -> None:

    uvicorn.run("src.server.application:server", host="127.0.0.1", port=8010, reload=True, log_level="info")


if __name__ == "__main__":
    asyncio.run(main())
