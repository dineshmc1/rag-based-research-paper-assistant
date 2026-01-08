"""
Helper script to update the backend .env file with OpenAI API key.
Run this script and enter your OpenAI API key when prompted.
"""

import os

env_path = "backend/.env"

print("=== OpenAI API Key Setup ===\n")
print("Please enter your OpenAI API key:")
print("(You can get this from https://platform.openai.com/api-keys)\n")

api_key = input("OPENAI_API_KEY: ").strip()

if not api_key:
    print("\n❌ Error: API key cannot be empty")
    exit(1)

# Read existing .env
try:
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
except FileNotFoundError:
    lines = []

# Update or add OPENAI_API_KEY
found = False
new_lines = []
for line in lines:
    if line.startswith("OPENAI_API_KEY="):
        new_lines.append(f"OPENAI_API_KEY={api_key}\n")
        found = True
    else:
        new_lines.append(line)

if not found:
    new_lines.append(f"OPENAI_API_KEY={api_key}\n")

# Write back
with open(env_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("\n✅ Success! Your .env file has been updated.")
print("Please restart the backend server:")
print("  uvicorn app.main:app --reload --port 8000")
