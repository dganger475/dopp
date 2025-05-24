class ProductionConfig:
    DEBUG = False
    TESTING = False
    # Use environment variable for secret key; do not hardcode in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'prod-insecure-key'
    CACHE_TYPE = 'simple'
    SENTRY_DSN = 'YOUR_SENTRY_DSN'
    # Add other production-specific configurations as needed
