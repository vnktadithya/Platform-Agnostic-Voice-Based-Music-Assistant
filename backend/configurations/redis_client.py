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
                # Raise the error to stop the app from starting in a broken state.
                raise e
        return cls._client

# This line ensures that anywhere we import 'redis_client', we get the same instance.
redis_client = RedisClient.get_client()