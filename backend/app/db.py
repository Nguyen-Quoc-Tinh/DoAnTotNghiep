import logging
import os
from functools import lru_cache

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database


LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    return MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)


def get_database() -> Database:
    database_name = os.getenv("MONGO_DB_NAME", "breast_cancer_diagnosis")
    return get_client()[database_name]


def ping_database() -> None:
    get_database().command("ping")


def ensure_indexes() -> None:
    database = get_database()
    database["users"].create_index([("username", ASCENDING)], unique=True)
    database["histories"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    database["histories"].create_index([("created_at", DESCENDING)])
    database["histories"].create_index([("record_code", ASCENDING)], unique=True, sparse=True)
    LOGGER.info("MongoDB indexes ensured")