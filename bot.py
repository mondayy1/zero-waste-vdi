import discord
from config import DISCORD_TOKEN, PROXMOX_HOST
from proxmox import create_vm
from llm import parse_vdi_request

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} 봇 시작됨')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if not message.content.startswith('!vdi'):
        return

    user_request = message.content[5:].strip()
    await message.channel.send("요청 처리 중... 🔄")

    params = parse_vdi_request(user_request)

    if not params:
        await message.channel.send("요청을 이해하지 못했습니다. 다시 시도해주세요.")
        return

    cpu = params['cpu']
    ram = params['ram']
    purpose = params['purpose']

    await message.channel.send(
        f"VM 생성 시작...\n"
        f"- CPU: {cpu}코어\n"
        f"- RAM: {ram}MB\n"
        f"- 용도: {purpose}"
    )

    vmid, result = create_vm(cpu, ram, purpose)

    if not vmid:
        await message.channel.send(f"❌ VM 생성 실패: {result}")
        return

    await message.channel.send(
        f"✅ VM 생성 완료!\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🖥️ VM 이름: `{result}`\n"
        f"🔑 계정: `ubuntu` / 비밀번호: `vdi-password`\n"
        f"📌 접속 IP는 Proxmox 콘솔에서 확인하세요.\n"
        f"🔗 {PROXMOX_HOST}:8006\n"
        f"⏰ 24시간 미사용 시 자동 회수됩니다.\n"
        f"━━━━━━━━━━━━━━━━"
    )

bot.run(DISCORD_TOKEN)
