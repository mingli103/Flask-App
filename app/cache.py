from flask_caching import Cache
import redis

cache = Cache()

def init_cache(app):
    """Initialize Redis cache"""
    with app.app_context():
        app.logger.info(f"Initializing Redis cache with URL: {app.config['REDIS_URL']}")
        cache.init_app(app)
        # Verify Redis connection
        try:
            app.logger.info("Testing Redis connection...")
            cache.set('test_key', 'test_value', timeout=10)
            test_value = cache.get('test_key')
            if test_value == 'test_value':
                app.logger.info("Redis cache initialized successfully")
            else:
                app.logger.error(f"Redis cache test failed. Got value: {test_value}")
        except Exception as e:
            app.logger.error(f"Failed to initialize Redis cache: {str(e)}")
            # Try to get more details about Redis connection
            try:
                app.logger.info(f"Trying direct Redis connection to: {app.config['REDIS_URL']}")
                redis_client = redis.from_url(app.config['REDIS_URL'])
                redis_client.ping()
                app.logger.info("Redis connection test successful")
            except Exception as redis_error:
                app.logger.error(f"Redis connection error: {str(redis_error)}")
