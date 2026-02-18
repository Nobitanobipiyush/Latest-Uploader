import os
import subprocess
import mmap
import logging
import datetime
import asyncio
import requests
import time
import aiohttp
import aiofiles
import tgcrypto
import concurrent.futures
from pathlib import Path
from pyrogram.types import Message
from pyrogram import Client

from p_bar import progress_bar


# ------------------ BASIC HELPERS ------------------

def duration(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)


def get_mps_and_keys(api_url):
    response = requests.get(api_url)
    response_json = response.json()
    mpd = response_json.get("MPD")
    keys = response_json.get("KEYS")
    return mpd, keys


# ------------------ PDF DOWNLOAD (FINAL FIXED) ------------------

async def pdf_download(url, file_name, chunk_size=1024 * 1024):
    """
    FIXED:
    - Works for static-db.appx.co.in pdf links
    - Uses User-Agent header
    - Checks file exists + size
    """
    if os.path.exists(file_name):
        os.remove(file_name)

    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(
        url,
        headers=headers,
        allow_redirects=True,
        stream=True,
        timeout=60
    )

    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")

    with open(file_name, "wb") as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)

    if not os.path.exists(file_name) or os.path.getsize(file_name) < 100:
        raise Exception("PDF not downloaded / empty")

    return file_name


# ------------------ VIDEO DOWNLOAD ------------------

failed_counter = 0


async def download_video(url, cmd, name):
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32" --cookies cookies.txt'
    global failed_counter

    print(download_cmd)
    logging.info(download_cmd)

    k = subprocess.run(download_cmd, shell=True)

    if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
        failed_counter += 1
        await asyncio.sleep(1)
        return await download_video(url, cmd, name)

    failed_counter = 0

    # return correct file
    if os.path.isfile(name):
        return name
    if os.path.isfile(f"{name}.webm"):
        return f"{name}.webm"

    name2 = name.split(".")[0]
    if os.path.isfile(f"{name2}.mkv"):
        return f"{name2}.mkv"
    if os.path.isfile(f"{name2}.mp4"):
        return f"{name2}.mp4"
    if os.path.isfile(f"{name2}.mp4.webm"):
        return f"{name2}.mp4.webm"

    return None


# ------------------ XOR DECRYPT (APPX ENCRYPTED) ------------------

def decrypt_file(file_path, key):
    """
    XOR decrypt first 28 bytes of the file using the key.
    SAFE:
    - handles None key
    - handles short key
    """
    if not file_path or not os.path.exists(file_path):
        return False

    if not key:
        return False

    try:
        with open(file_path, "r+b") as f:
            num_bytes = min(28, os.path.getsize(file_path))
            with mmap.mmap(f.fileno(), length=num_bytes, access=mmap.ACCESS_WRITE) as mmapped_file:
                for i in range(num_bytes):
                    mmapped_file[i] ^= ord(key[i % len(key)])
        return True
    except:
        return False


async def download_and_decrypt_video(url, cmd, name, key):
    """
    FIXED:
    - if key missing => returns normal video
    - if download returns None => raises error
    """
    video_path = await download_video(url, cmd, name)

    if not video_path:
        raise Exception("Download failed (file not created).")

    if not key:
        return video_path

    ok = decrypt_file(video_path, key)
    if not ok:
        raise Exception("Decryption failed (wrong key or file issue).")

    return video_path


async def download_and_decrypt_pdf(url, name, key):
    """
    - downloads pdf using pdf_download()
    - decrypts if key given
    """
    file_path = await pdf_download(url, f"{name}.pdf")

    if not key:
        return file_path

    ok = decrypt_file(file_path, key)
    if not ok:
        raise Exception("PDF decrypt failed (wrong key).")

    return file_path


# ------------------ DRM DECRYPT ------------------

async def decrypt_and_merge_video(mpd_url, keys_string, output_path, output_name, quality="720"):
    try:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        cmd1 = f'yt-dlp -f "bv[height<={quality}]+ba/b" -o "{output_path}/file.%(ext)s" --allow-unplayable-format --no-check-certificate --external-downloader aria2c "{mpd_url}"'
        os.system(cmd1)

        avDir = list(output_path.iterdir())

        video_decrypted = False
        audio_decrypted = False

        for data in avDir:
            if data.suffix == ".mp4" and not video_decrypted:
                cmd2 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/video.mp4"'
                os.system(cmd2)
                if (output_path / "video.mp4").exists():
                    video_decrypted = True
                data.unlink()

            elif data.suffix == ".m4a" and not audio_decrypted:
                cmd3 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/audio.m4a"'
                os.system(cmd3)
                if (output_path / "audio.m4a").exists():
                    audio_decrypted = True
                data.unlink()

        if not video_decrypted or not audio_decrypted:
            raise FileNotFoundError("Decryption failed: video or audio file not found.")

        cmd4 = f'ffmpeg -i "{output_path}/video.mp4" -i "{output_path}/audio.m4a" -c copy "{output_path}/{output_name}.mp4"'
        os.system(cmd4)

        if (output_path / "video.mp4").exists():
            (output_path / "video.mp4").unlink()
        if (output_path / "audio.m4a").exists():
            (output_path / "audio.m4a").unlink()

        filename = output_path / f"{output_name}.mp4"
        if not filename.exists():
            raise FileNotFoundError("Merged video file not found.")

        return str(filename)

    except Exception as e:
        raise Exception(str(e))


# ------------------ UPLOAD FUNCTIONS ------------------

EMOJIS = ["🔥", "💥", "⚡", "💫", "🌹", "🦋"]
emoji_counter = 0


def get_next_emoji():
    global emoji_counter
    emoji = EMOJIS[emoji_counter]
    emoji_counter = (emoji_counter + 1) % len(EMOJIS)
    return emoji


async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog):
    emoji = get_next_emoji()

    # thumbnail
    subprocess.run(
        f'ffmpeg -i "{filename}" -ss 00:00:02 -vframes 1 "{filename}.jpg"',
        shell=True
    )

    try:
        await prog.delete(True)
    except:
        pass

    reply = await m.reply_text(f"**Uploading ...** - `{name}`")
    start_time = time.time()

    if thumb == "no":
        thumbnail = f"{filename}.jpg"
    else:
        thumbnail = thumb

    dur = int(duration(filename))
    processing_msg = await m.reply_text(emoji)

    try:
        await m.reply_video(
            filename,
            caption=cc,
            supports_streaming=True,
            height=720,
            width=1280,
            thumb=thumbnail,
            duration=dur,
            progress=progress_bar,
            progress_args=(reply, start_time),
        )
    except:
        await m.reply_document(
            filename,
            caption=cc,
            progress=progress_bar,
            progress_args=(reply, start_time),
        )

    # cleanup
    try:
        os.remove(filename)
    except:
        pass

    try:
        os.remove(f"{filename}.jpg")
    except:
        pass

    try:
        await processing_msg.delete(True)
    except:
        pass

    try:
        await reply.delete(True)
    except:
        import os
import requests
import subprocess
import mmap
import logging
import datetime
import asyncio
import requests
import time
import aiohttp
import aiofiles
import tgcrypto
import concurrent.futures
from pathlib import Path
from pyrogram.types import Message
from pyrogram import Client

from p_bar import progress_bar


# ------------------ BASIC HELPERS ------------------

def duration(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)


def get_mps_and_keys(api_url):
    response = requests.get(api_url)
    response_json = response.json()
    mpd = response_json.get("MPD")
    keys = response_json.get("KEYS")
    return mpd, keys


# ------------------ PDF DOWNLOAD (FINAL FIXED) ------------------

async def pdf_download(url, file_name, chunk_size=1024 * 1024):
    """
    FIXED:
    - Works for static-db.appx.co.in pdf links
    - Uses User-Agent header
    - Checks file exists + size
    """
    if os.path.exists(file_name):
        os.remove(file_name)

    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(
        url,
        headers=headers,
        allow_redirects=True,
        stream=True,
        timeout=60
    )

    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")

    with open(file_name, "wb") as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)

    if not os.path.exists(file_name) or os.path.getsize(file_name) < 100:
        raise Exception("PDF not downloaded / empty")

    return file_name


# ------------------ VIDEO DOWNLOAD ------------------

failed_counter = 0


async def download_video(url, cmd, name):
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32" --cookies cookies.txt'
    global failed_counter

    print(download_cmd)
    logging.info(download_cmd)

    k = subprocess.run(download_cmd, shell=True)

    if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
        failed_counter += 1
        await asyncio.sleep(1)
        return await download_video(url, cmd, name)

    failed_counter = 0

    # return correct file
    if os.path.isfile(name):
        return name
    if os.path.isfile(f"{name}.webm"):
        return f"{name}.webm"

    name2 = name.split(".")[0]
    if os.path.isfile(f"{name2}.mkv"):
        return f"{name2}.mkv"
    if os.path.isfile(f"{name2}.mp4"):
        return f"{name2}.mp4"
    if os.path.isfile(f"{name2}.mp4.webm"):
        return f"{name2}.mp4.webm"

    return None


# ------------------ XOR DECRYPT (APPX ENCRYPTED) ------------------

def decrypt_file(file_path, key):
    """
    XOR decrypt first 28 bytes of the file using the key.
    SAFE:
    - handles None key
    - handles short key
    """
    if not file_path or not os.path.exists(file_path):
        return False

    if not key:
        return False

    try:
        with open(file_path, "r+b") as f:
            num_bytes = min(28, os.path.getsize(file_path))
            with mmap.mmap(f.fileno(), length=num_bytes, access=mmap.ACCESS_WRITE) as mmapped_file:
                for i in range(num_bytes):
                    mmapped_file[i] ^= ord(key[i % len(key)])
        return True
    except:
        return False


async def download_and_decrypt_video(url, cmd, name, key):
    """
    FIXED:
    - if key missing => returns normal video
    - if download returns None => raises error
    """
    video_path = await download_video(url, cmd, name)

    if not video_path:
        raise Exception("Download failed (file not created).")

    if not key:
        return video_path

    ok = decrypt_file(video_path, key)
    if not ok:
        raise Exception("Decryption failed (wrong key or file issue).")

    return video_path


async def download_and_decrypt_pdf(url, name, key):
    """
    - downloads pdf using pdf_download()
    - decrypts if key given
    """
    file_path = await pdf_download(url, f"{name}.pdf")

    if not key:
        return file_path

    ok = decrypt_file(file_path, key)
    if not ok:
        raise Exception("PDF decrypt failed (wrong key).")

    return file_path


# ------------------ DRM DECRYPT ------------------

async def decrypt_and_merge_video(mpd_url, keys_string, output_path, output_name, quality="720"):
    try:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        cmd1 = f'yt-dlp -f "bv[height<={quality}]+ba/b" -o "{output_path}/file.%(ext)s" --allow-unplayable-format --no-check-certificate --external-downloader aria2c "{mpd_url}"'
        os.system(cmd1)

        avDir = list(output_path.iterdir())

        video_decrypted = False
        audio_decrypted = False

        for data in avDir:
            if data.suffix == ".mp4" and not video_decrypted:
                cmd2 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/video.mp4"'
                os.system(cmd2)
                if (output_path / "video.mp4").exists():
                    video_decrypted = True
                data.unlink()

            elif data.suffix == ".m4a" and not audio_decrypted:
                cmd3 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/audio.m4a"'
                os.system(cmd3)
                if (output_path / "audio.m4a").exists():
                    audio_decrypted = True
                data.unlink()

        if not video_decrypted or not audio_decrypted:
            raise FileNotFoundError("Decryption failed: video or audio file not found.")

        cmd4 = f'ffmpeg -i "{output_path}/video.mp4" -i "{output_path}/audio.m4a" -c copy "{output_path}/{output_name}.mp4"'
        os.system(cmd4)

        if (output_path / "video.mp4").exists():
            (output_path / "video.mp4").unlink()
        if (output_path / "audio.m4a").exists():
            (output_path / "audio.m4a").unlink()

        filename = output_path / f"{output_name}.mp4"
        if not filename.exists():
            raise FileNotFoundError("Merged video file not found.")

        return str(filename)

    except Exception as e:
        raise Exception(str(e))


# ------------------ UPLOAD FUNCTIONS ------------------

EMOJIS = ["🔥", "💥", "⚡", "💫", "🌹", "🦋"]
emoji_counter = 0


def get_next_emoji():
    global emoji_counter
    emoji = EMOJIS[emoji_counter]
    emoji_counter = (emoji_counter + 1) % len(EMOJIS)
    return emoji


async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog):
    emoji = get_next_emoji()

    # thumbnail
    subprocess.run(
        f'ffmpeg -i "{filename}" -ss 00:00:02 -vframes 1 "{filename}.jpg"',
        shell=True
    )

    try:
        await prog.delete(True)
    except:
        pass

    reply = await m.reply_text(f"**Uploading ...** - `{name}`")
    start_time = time.time()

    if thumb == "no":
        thumbnail = f"{filename}.jpg"
    else:
        thumbnail = thumb

    dur = int(duration(filename))
    processing_msg = await m.reply_text(emoji)

    try:
        await m.reply_video(
            filename,
            caption=cc,
            supports_streaming=True,
            height=720,
            width=1280,
            thumb=thumbnail,
            duration=dur,
            progress=progress_bar,
            progress_args=(reply, start_time),
        )
    except:
        await m.reply_document(
            filename,
            caption=cc,
            progress=progress_bar,
            progress_args=(reply, start_time),
        )

    # cleanup
    try:
        os.remove(filename)
    except:
        pass

    try:
        os.remove(f"{filename}.jpg")
    except:
        pass

    try:
        await processing_msg.delete(True)
    except:
        pass

    try:
        await reply.delete(True)
    except:
        pass
