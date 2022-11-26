import os


def get_postgres_uri():
    host = os.environ.get("DB_HOST", "localhost")
    port = 5432 if host == "localhost" else None
    user, db_name = "parkbosung", "architecture"
    return f"postgresql://{host}:{port}/{db_name}"


def get_api_url():
    host = "127.0.0.1"
    port = 8000
    return f"http://{host}:{port}"


def get_redis_host_and_port():
    host = "127.0.0.1"
    port = 63791 if host == "localhost" else 6379
    return dict(host=host, port=port)

