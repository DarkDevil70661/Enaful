from motor.motor_asyncio import AsyncIOMotorClient as _mongo_client_
from pymongo import MongoClient
from pyrogram import Client

import config

from ..logging import LOGGER

TEMP_MONGODB = ""


if config.MONGO_DB_URI is None:
    LOGGER(__name__).warning("No MONGO DB URL found. LOL")
    temp_client = Client(
        "Anon",
        bot_token=config.BOT_TOKEN,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
    )
    temp_client.start()
    info = temp_client.get_me()
    username = info.username
    temp_client.stop()
    # ⚡ maxPoolSize bumped: 500 running clones + main bot all share this one
    # Mongo client, so the default pool (100) can queue under load. 200 gives
    # real headroom — raise further if your Atlas tier's connection limit
    # allows it, lower it if you're on the M0 free tier.
    _mongo_async_ = _mongo_client_(TEMP_MONGODB, maxPoolSize=200, minPoolSize=10)
    _mongo_sync_ = MongoClient(TEMP_MONGODB, maxPoolSize=200, minPoolSize=10)
    mongodb = _mongo_async_[username]
    pymongodb = _mongo_sync_[username]
else:
    _mongo_async_ = _mongo_client_(config.MONGO_DB_URI, maxPoolSize=200, minPoolSize=10)
    _mongo_sync_ = MongoClient(config.MONGO_DB_URI, maxPoolSize=200, minPoolSize=10)
    mongodb = _mongo_async_.Anon
    pymongodb = _mongo_sync_.Anon
