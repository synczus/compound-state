#!/usr/bin/env python3
"""Write the Telegram bot token to kestrel .env"""
token = "8607902717:AAFYICfwQeGScvuMtXMy1Mv9hDaDYverA_I"

with open("/home/synczus/kestrel/.env", "w") as f:
    f.write("# Kestrel environment\n")
    f.write(f"TELEGRAM_BOT_TOKEN=***")
    f.write("TELEGRAM_CHAT_ID=-5087043705\n")

print("Written successfully")
