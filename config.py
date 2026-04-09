import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PROXMOX_HOST = os.getenv("PROXMOX_HOST")
PROXMOX_USER = os.getenv("PROXMOX_USER")
PROXMOX_PASSWORD = os.getenv("PROXMOX_PASSWORD")
PROXMOX_NODE = os.getenv("PROXMOX_NODE", "pve")
TEMPLATE_ID = int(os.getenv("TEMPLATE_ID", "100"))
