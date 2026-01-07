try:
    from app.core.config import settings
    print(f"Loaded config successfully. Model: {settings.OPENAI_MODEL}")
except Exception as e:
    print(f"Error loading config: {e}")
