import redis
import os
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    _client = None

    @classmethod
    def get_client(cls):
        """
        Gets a single, shared Redis client instance.
        Includes connection checking on first creation.
        """
        if cls._client is None:
            try:
                cls._client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", 6379)),
                    db=0,
                    decode_responses=True # Ensures keys and values are strings
                )
                cls._client.ping()
                logger.info("Successfully connected to Redis.")
            except redis.exceptions.ConnectionError as e:
                logger.error(f"Could not connect to Redis: {e}. Please ensure your Redis server is running.")
                raise e
        return cls._client

redis_client = RedisClient.get_client()