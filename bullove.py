import os
import asyncio
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# === Patch untuk Python 3.13 (hilangnya imghdr) ===
try:
    import imghdr  # normal di Python < 3.13
except ImportError:
    import imghdr_py as imghdr  # fallback dari requirements

from telethon import TelegramClient, events
from telethon.tl.functions.channels import CreateChannelRequest
from telethon.errors import FloodWaitError

# === Load ENV ===
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

# Debug ENV
print("=== DEBUG Railway ENV ===")
print("API_ID   =", API_ID)
print("API_HASH =", API_HASH)
print("SESSION  =", SESSION)

if not API_ID or not API_HASH or not SESSION:
    print("❌ ENV tidak lengkap! Pastikan API_ID, API_HASH, SESSION sudah diisi di Railway.")
    exit(1)

API_ID = int(API_ID)

# Inisialisasi client pakai SESSION
bullove = TelegramClient(session=SESSION, api_id=API_ID, api_hash=API_HASH)

OWNER_ID = None

async def init_owner():
    global OWNER_ID
    me = await bullove.get_me()
    OWNER_ID = me.id
    print(f"✅ OWNER_ID otomatis: {OWNER_ID} ({me.first_name})")

# === Handler Command .buat g ===
@bullove.on(events.NewMessage(pattern=r"\.buat g(?: (\d+))?(?: (.+))"))
async def handler_buat(event):
    if event.sender_id != OWNER_ID:
        return

    jumlah = 1
    nama = None

    if event.pattern_match.group(1) and event.pattern_match.group(2):
        jumlah = int(event.pattern_match.group(1))
        nama = event.pattern_match.group(2)
    elif event.pattern_match.group(2):
        nama = event.pattern_match.group(2)

    if not nama:
        await event.reply("⚠️ Format salah!\nGunakan: `.buat g <jumlah> <nama>` atau `.buat g <nama>`")
        return

    await event.delete()
    msg = await event.respond("⏳ Membuat grup...")

    hasil = []
    for i in range(jumlah):
        try:
            grup = await bullove(CreateChannelRequest(
                title=f"{nama} {i+1}",
                about="Grup by @WARUNGBULLOVE",
                megagroup=True
            ))
            chat_id = grup.chats[0].id

            try:
                link = await bullove.export_chat_invite_link(chat_id)
            except Exception as e:
                link = f"(gagal ambil link: {e})"

            await tampilkan_progress(msg, jumlah, i)

            for _ in range(4):
                await bullove.send_message(chat_id, get_random_pesan())
                await asyncio.sleep(1)

            hasil.append(f"✅ [{nama} {i+1}]({link})")

        except FloodWaitError as e:
            sisa = e.seconds
            hari, sisa = divmod(sisa, 86400)
            jam, sisa = divmod(sisa, 3600)
            menit, detik = divmod(sisa, 60)

            waktu_bisa = datetime.now() + timedelta(seconds=e.seconds)
            waktu_bisa_fmt = waktu_bisa.strftime("%d-%m-%Y %H:%M:%S")

            hasil.append(
                f"⛔ Kena limit Telegram!\n"
                f"Tunggu {hari} hari {jam} jam {menit} menit {detik} detik.\n"
                f"Kamu bisa membuat grup lagi pada: **{waktu_bisa_fmt}**"
            )
            break

        except Exception as e:
            hasil.append(f"❌ Gagal buat {nama} {i+1} → {e}")

    await msg.edit("🎉 Hasil pembuatan grup:\n\n" + "\n".join(hasil), link_preview=False)

# === Handler Ping ===
@bullove.on(events.NewMessage(pattern=r"\.ping"))
async def handler_ping(event):
    if event.sender_id != OWNER_ID:
        return
    start = time.time()
    msg = await event.reply("🏓 Pong...")
    end = time.time()
    ms = int((end - start) * 1000)
    await msg.edit(f"🏓 Pong! `{ms}ms`")

# === Fungsi Tambahan ===
def get_random_pesan():
    pesan_list = [
        "Halo semua 👋",
        "Selamat datang di grup!",
        "Jangan lupa baca rules ya 📜",
        "Semoga betah 🤝"
    ]
    return random.choice(pesan_list)

async def tampilkan_progress(msg, total, current):
    progress = int((current+1) / total * 100)
    bar = "█" * ((current+1) * 5 // total) + "░" * (5 - ((current+1) * 5 // total))
    await msg.edit(f"⏳ Membuat grup {current+1}/{total}...\n[{bar}] {progress}%")

# === Run Bot ===
async def main():
    await bullove.start()
    await init_owner()
    await bullove.run_until_disconnected()

asyncio.run(main())
