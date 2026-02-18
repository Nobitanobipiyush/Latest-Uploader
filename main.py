import requests
import subprocess
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyromod import listen
from pyrogram.types import Message
from subprocess import getstatusoutput
from aiohttp import ClientSession
import helper
import time
import asyncio
import sys
import re
import os


# -------------------------
# Bot Setup
# -------------------------
bot = Client(
    "bot",
    bot_token=os.environ.get("BOT_TOKEN", "add"),
    api_id=int(os.environ.get("API_ID", "0")),
    api_hash=os.environ.get("API_HASH", "add"),
)

owner_id = [6530997270]
auth_users = [6530997270]

photo1 = "https://envs.sh/PQ_.jpg"
getstatusoutput(f"wget {photo1} -O 'photo.jpg'")
photo = "photo.jpg"


# -------------------------
# /start (for everyone)
# -------------------------
@bot.on_message(filters.command(["start"]))
async def start_cmd(bot: Client, m: Message):
    await m.reply_text(
        f"**Hello** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n"
        f">> I am TXT file Downloader Bot.\n"
        f">> Send me /txt and follow steps.\n\n"
        f"If you want to stop me just send /stop"
    )


# -------------------------
# /restart
# -------------------------
@bot.on_message(filters.command("restart"))
async def restart_handler(_, m: Message):
    await m.reply_text("🚀 Restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)


# -------------------------
# /txt
# -------------------------
@bot.on_message(filters.command(["txt"]))
async def txt_cmd(bot: Client, m: Message):

    editable = await m.reply_text("**Please send TXT file for download**")
    input_msg: Message = await bot.listen(editable.chat.id)

    y = await input_msg.download()
    file_name, ext = os.path.splitext(os.path.basename(y))
    x = y

    path = f"./downloads/{m.chat.id}"
    os.makedirs(path, exist_ok=True)

    # -------------------------
    # Read TXT links
    # -------------------------
    try:
        with open(x, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = content.split("\n")

        links = []
        for i in content:
            if i.strip():
                links.append(i.split("://", 1))

        os.remove(x)

    except Exception:
        await m.reply_text("❌ Invalid file input.")
        try:
            os.remove(x)
        except Exception:
            pass
        return

    await editable.edit(
        f"Total links found are **{len(links)}**\n\n"
        f"Send from where you want to download (initial is **1**)"
    )

    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    await editable.edit("**Send me your Batch Name or send `df` for filename default.**")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)

    b_name = file_name if raw_text0 == "df" else raw_text0

    await editable.edit("**Enter resolution** `1080` , `720` , `480` , `360` , `240` , `144`")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)

    if raw_text2 == "144":
        res = "256x144"
    elif raw_text2 == "240":
        res = "426x240"
    elif raw_text2 == "360":
        res = "640x360"
    elif raw_text2 == "480":
        res = "854x480"
    elif raw_text2 == "720":
        res = "1280x720"
    elif raw_text2 == "1080":
        res = "1920x1080"
    else:
        raw_text2 = "720"
        res = "1280x720"

    await editable.edit("**Now enter caption (or send `df` for default)**")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)

    MR = "Group Admin" if raw_text3 == "df" else raw_text3

    await editable.edit("**Now send Thumb url for Custom Thumbnail (or send `no`)**")
    input6: Message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = raw_text6
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    count = 1 if len(links) == 1 else int(raw_text)

    # -------------------------
    # MAIN LOOP
    # -------------------------
    try:
        for i in range(count - 1, len(links)):

            V = (
                links[i][1]
                .replace("file/d/", "uc?export=download&id=")
                .replace("www.youtube-nocookie.com/embed", "youtu.be")
                .replace("?modestbranding=1", "")
                .replace("/view?usp=sharing", "")
            )

            if V.startswith("http://") or V.startswith("https://"):
                url = V
            else:
                url = "https://" + V

            # ----------------------------
            # Special cases
            # ----------------------------
            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            # Appx encrypted key
            appxkey = None
            if "encrypted.m" in url and "*" in url:
                appxkey = url.split("*")[1]
                url = url.split("*")[0]

            # ----------------------------
            # Safe Name
            # ----------------------------
            name1 = (
                links[i][0]
                .replace("\t", "")
                .replace(":", "")
                .replace("/", "")
                .replace("+", "")
                .replace("#", "")
                .replace("|", "")
                .replace("@", "")
                .replace("*", "")
                .strip()
            )

            if not name1:
                name1 = f"File_{i+1}"

            name = f"{name1[:60]}"

            # ----------------------------
            # Captions
            # ----------------------------
            cc = (
                f"🎬 **Title:** `{name1}.mkv`\n"
                f"🖥️ **Resolution:** [{res}]\n\n"
                f"📘 **Course:** `{b_name}`\n\n"
                f"🚀 **Extracted By:** `{MR}`"
            )

            cc1 = (
                f"📄 **Title:** `{name1}.pdf`\n\n"
                f"📘 **Course:** `{b_name}`\n\n"
                f"🚀 **Extracted By:** `{MR}`"
            )

            cc2 = (
                f"🖼️ **Title:** `{name1}.jpg`\n\n"
                f"📘 **Course:** `{b_name}`\n\n"
                f"🚀 **Extracted By:** `{MR}`"
            )

            # ----------------------------
            # DOWNLOAD LOGIC
            # ----------------------------
            try:

                # ✅ PDF FIX (requests based)
                if ".pdf" in url.lower():
                    try:
                        prog = await m.reply_text(f"📄 Downloading PDF: **{name1}**")
                        pdf_file = await helper.pdf_download(url, f"{name}.pdf")
                        await prog.delete(True)

                        await bot.send_document(
                            chat_id=m.chat.id,
                            document=pdf_file,
                            caption=cc1
                        )

                        if os.path.exists(pdf_file):
                            os.remove(pdf_file)

                        count += 1
                        continue

                    except Exception as e:
                        await m.reply_text(f"❌ PDF download failed: {e}\n\nLink: {url}")
                        count += 1
                        continue

                # ✅ M3U8 SUPPORT
                if "master.m3u8" in url.lower() or url.lower().endswith(".m3u8"):
                    try:
                        prog = await m.reply_text(f"⬇️ Downloading M3U8: **{name1}**")

                        cmd = f'yt-dlp -f "bv[height<={raw_text2}]+ba/b" "{url}" -o "{name}.mp4"'
                        res_file = await helper.download_video(url, cmd, name)
                        filename = res_file

                        await prog.delete(True)
                        await helper.send_vid(bot, m, cc, filename, thumb, name, prog)

                        count += 1
                        await asyncio.sleep(1)
                        continue

                    except Exception as e:
                        await m.reply_text(f"❌ M3U8 download failed: {e}\n\nLink: {url}")
                        count += 1
                        continue

                # Images
                if any(img in url.lower() for img in [".jpeg", ".png", ".jpg"]):
                    subprocess.run(["wget", url, "-O", f"{name}.jpg"], check=True)
                    await bot.send_photo(chat_id=m.chat.id, caption=cc2, photo=f"{name}.jpg")

                    if os.path.exists(f"{name}.jpg"):
                        os.remove(f"{name}.jpg")

                    count += 1
                    continue

                # Encrypted appx video
                if "encrypted.m" in url:
                    prog = await m.reply_text(f"🔐 Downloading encrypted video: **{name1}**")

                    ytf = f'b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba'
                    cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

                    res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)
                    filename = res_file

                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)

                    count += 1
                    await asyncio.sleep(1)
                    continue

                # Normal video
                prog = await m.reply_text(f"⬇️ Downloading: **{name1}**")

                ytf = f'b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba'
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

                res_file = await helper.download_video(url, cmd, name)
                filename = res_file

                await prog.delete(True)
                await helper.send_vid(bot, m, cc, filename, thumb, name, prog)

                count += 1
                await asyncio.sleep(1)

            except FloodWait as e:
                await asyncio.sleep(e.x)
                continue

            except Exception as e:
                await m.reply_text(
                    f"**downloading failed**\n\n"
                    f"{str(e)}\n\n"
                    f"**Name** - {name}\n"
                    f"**Link** - {url}"
                )
                count += 1
                continue

    except Exception as e:
        await m.reply_text(str(e))

    await m.reply_text("🔥 All downloads completed successfully!")


bot.run()
