import os

content = b"OPENAI_API_KEY=your_key_here_locally"

file_path = '.env'

try:
    if os.path.exists(file_path):
        os.remove(file_path)
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    print(f"Wrote {len(content)} bytes to {file_path}")
    
    
    with open(file_path, 'rb') as f:
        header = f.read(5)
        print(f"Header bytes: {header}")
        
    
    from app.core.config import settings
    print(f"Config loaded. Model: {settings.OPENAI_MODEL}")

except Exception as e:
    print(f"Error: {e}")
