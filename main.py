from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
import requests
import m3u8
import json
import subprocess
from pyrogram import Client, filters
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
from pyromod import listen
from pyrogram.types import Message
from p_bar import progress_bar
from subprocess import getstatusoutput
from aiohttp import ClientSession
import helper
from logger import logging
import time
import asyncio
from pyrogram.types import User, Message
import sys
import re
import os
import urllib
import urllib.parse
import tgcrypto
import cloudscraper

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

token_cp = "your cp token"


# ✅ FIXED: /start now works for everyone
@bot.on_message(filters.command(["start"]))
async def start_cmd(bot: Client, m: Message):
    await m.reply_text(
        f"**Hello** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n"
        f">> I am TXT file Downloader Bot.\n"
        f">> Send me /txt and follow steps.\n\n"
        f"If you want to stop me just send /stop"
    )


@bot.on_message(filters.command("restart"))
async def restart_handler(_, m):
    await m.reply_text("STOPPED", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.on_message(filters.command(["txt"]))
async def txt_cmd(bot: Client, m: Message):
    editable = await m.reply_text("**Please send TXT file for download**")
    input: Message = await bot.listen(editable.chat.id)

    y = await input.download()
    file_name, ext = os.path.splitext(os.path.basename(y))
    x = y

    path = f"./downloads/{m.chat.id}"

    try:
        # ✅ FIXED: encoding safe
        with open(x, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        content = content.split("\n")
        links = []
        for i in content:
            if i.strip():
                links.append(i.split("://", 1))
        os.remove(x)
    except:
        await m.reply_text("Invalid file input.")
        try:
            os.remove(x)
        except:
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

    if raw_text0 == "df":
        b_name = file_name
    else:
        b_name = raw_text0

    await editable.edit("**Enter resolution** `1080` , `720` , `480` , `360` , `240` , `144`")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)

    try:
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
            res = "1280x720"
    except Exception:
        res = "UN"

    await editable.edit("**Now enter caption (or send `df` for default)**")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)

    if raw_text3 == "df":
        MR = "Group Admin"
    else:
        MR = raw_text3

    await editable.edit("**If PW MPD links enter working token (else send df)**")
    input11: Message = await bot.listen(editable.chat.id)
    token = input11.text
    await input11.delete(True)

    await editable.edit(
        "Now send Thumb url for Custom Thumbnail.\n"
        "Example: `https://envs.sh/Hlb.jpg`\n"
        "Or if you don't want custom thumbnail send: `no`"
    )
    input6 = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = raw_text6
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    if len(links) == 1:
        count = 1
    else:
        count = int(raw_text)

    try:
        for i in range(count - 1, len(links)):
            # ----------------------------
            # ✅ FIXED URL building
            # ----------------------------
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

            elif "https://cpvod.testbook.com/" in url:
                url = url.replace("https://cpvod.testbook.com/", "https://media-cdn.classplusapp.com/drm/")
                url = "https://dragoapi.vercel.app/classplus?link=" + url
                mpd, keys = helper.get_mps_and_keys(url)
                url = mpd
                keys_string = " ".join([f"--key {key}" for key in keys])

            elif "classplusapp.com/drm/" in url:
                url = "https://dragoapi.vercel.app/classplus?link=" + url
                mpd, keys = helper.get_mps_and_keys(url)
                url = mpd
                keys_string = " ".join([f"--key {key}" for key in keys])

            elif "edge.api.brightcove.com" in url:
                await m.reply_text("Brightcove links are not supported in this bot build.")
                continue

            elif "tencdn.classplusapp" in url:
                headers = {
                    "Host": "api.classplusapp.com",
                    "x-access-token": f"{token_cp}",
                    "user-agent": "Mobile-Android",
                    "app-version": "1.4.37.1",
                    "api-version": "18",
                    "device-id": "5d0d17ac8b3c9f51",
                    "device-details": "2848b866799971ca_2848b8667a33216c_SDK-30",
                    "accept-encoding": "gzip",
                }
                params = (("url", f"{url}"),)
                response = requests.get(
                    "https://api.classplusapp.com/cams/uploader/video/jw-signed-url",
                    headers=headers,
                    params=params,
                )
                url = response.json()["url"]

            elif "videos.classplusapp" in url:
                url = requests.get(
                    f"https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}",
                    headers={"x-access-token": f"{token_cp}"},
                ).json()["url"]

            elif (
                "media-cdn.classplusapp.com" in url
                or "media-cdn-alisg.classplusapp.com" in url
                or "media-cdn-a.classplusapp.com" in url
            ):
                headers = {"x-access-token": f"{token_cp}", "X-CDN-Tag": "empty"}
                response = requests.get(
                    f"https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}",
                    headers=headers,
                )
                url = response.json()["url"]

            elif "encrypted.m" in url and "*" in url:
                appxkey = url.split("*")[1]
                url = url.split("*")[0]

            elif url.startswith("https://videotest.adda247.com/"):
                if url.split("/")[3] != "demo":
                    url = f'https://videotest.adda247.com/demo/{url.split("https://videotest.adda247.com/")[1]}'

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
                .replace(".", "")
                .replace("https", "")
                .replace("http", "")
                .strip()
            )

            if not name1:
                name1 = f"File_{count}"

            name = f"{name1[:60]}"

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:
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

                ccyt = (
                    f"🎬 **Title:** `{name1}.mkv`\n"
                    f"🎥 **Video Link:** {url}\n"
                    f"🖥️ **Resolution:** [{res}]\n\n"
                    f"📘 **Course:** `{b_name}`\n\n"
                    f"🚀 **Extracted By:** `{MR}`"
                )

                if "drive" in url:
                    ka = await helper.download(url, name)
                    await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
                    count += 1
                    os.remove(ka)
                    time.sleep(1)

                elif "pdf*" in url:
                    pdf_key = url.split("*")[1]
                    url = url.split("*")[0]
                    pdf_enc = await helper.download_and_decrypt_pdf(url, name, pdf_key)
                    await bot.send_document(chat_id=m.chat.id, document=pdf_enc, caption=cc1)
                    count += 1
                    os.remove(pdf_enc)
                    continue

                elif ".pdf" in url:
                    cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                    download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                    os.system(download_cmd)
                    await bot.send_document(chat_id=m.chat.id, document=f"{name}.pdf", caption=cc1)
                    count += 1
                    os.remove(f"{name}.pdf")

                elif any(img in url.lower() for img in [".jpeg", ".png", ".jpg"]):
                    subprocess.run(["wget", url, "-O", f"{name}.jpg"], check=True)
                    await bot.send_photo(chat_id=m.chat.id, caption=cc2, photo=f"{name}.jpg")
                    if os.path.exists(f"{name}.jpg"):
                        os.remove(f"{name}.jpg")

                elif "youtu" in url:
                    await bot.send_photo(chat_id=m.chat.id, photo=photo, caption=ccyt)
                    count += 1

                elif ".ws" in url and url.endswith(".ws"):
                    await helper.pdf_download(f"{api_url}utkash-ws?url={url}&authorization={api_token}", f"{name}.html")
                    time.sleep(1)
                    await bot.send_document(chat_id=m.chat.id, document=f"{name}.html", caption=cc1)
                    os.remove(f"{name}.html")
                    count += 1
                    time.sleep(5)

                elif "encrypted.m" in url:
                    prog = await m.reply_text(f"Downloading encrypted video: **{name1}**")
                    res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    await asyncio.sleep(1)
                    continue

                elif "drmcdni" in url or "drm/wv" in url:
                    prog = await m.reply_text(f"Decrypting DRM video: **{name1}**")
                    res_file = await helper.decrypt_and_merge_video(mpd, keys_string, path, name, raw_text2)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    await asyncio.sleep(1)
                    continue

                else:
                    prog = await m.reply_text(f"Downloading: **{name1}**")
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)

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
