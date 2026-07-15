import os

# Define variáveis mínimas para que `settings = Settings()` não falhe ao importar
# módulos que dependem de `app.core.settings` durante a coleta dos testes.
os.environ.setdefault("JWT_SECRET", "test-secret-for-unit-tests")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRES_MIN", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRES_DAYS", "7")
