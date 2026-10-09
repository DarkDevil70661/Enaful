import json
import subprocess
from typing import Union

def get_readable_time(seconds: int) -> str:
    """Converts seconds into a human-readable string (Days, Hours, Min, Sec)."""
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]
        
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time


def convert_bytes(size: float) -> str:
    """Converts bytes to human readable format (KiB, MiB, GiB)."""
    if not size:
        return ""
    power = 1024
    t_n = 0
    power_dict = {0: " ", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti", 5: "Pi"}
    
    while size > power:
        size /= power
        t_n += 1
        if t_n >= 5: # Break if too large
            break
            
    return "{:.2f} {}B".format(size, power_dict[t_n])


# ✅ OPTIMIZATION: Removed 'async' (CPU bound tasks should be sync)
def int_to_alpha(user_id: int) -> str:
    """Obfuscates User ID to Alphabet string."""
    alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
    text = ""
    user_id = str(user_id)
    for i in user_id:
        try:
            text += alphabet[int(i)]
        except IndexError:
            pass
    return text


# ✅ OPTIMIZATION: Removed 'async'
def alpha_to_int(user_id_alphabet: str) -> int:
    """De-obfuscates Alphabet string back to User ID."""
    alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
    user_id = ""
    for i in user_id_alphabet:
        try:
            index = alphabet.index(i)
            user_id += str(index)
        except ValueError:
            pass
    try:
        return int(user_id)
    except ValueError:
        return 0


def time_to_seconds(time: str) -> int:
    """Converts MM:SS or HH:MM:SS string to seconds."""
    try:
        stringt = str(time)
        return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))
    except:
        return 0


def seconds_to_min(seconds: int) -> str:
    """Converts seconds to MM:SS or HH:MM:SS."""
    if seconds is not None:
        try:
            seconds = int(seconds)
        except:
            return "-"
            
        d, h, m, s = (
            seconds // (3600 * 24),
            seconds // 3600 % 24,
            seconds % 3600 // 60,
            seconds % 3600 % 60,
        )
        if d > 0:
            return "{:02d}:{:02d}:{:02d}:{:02d}".format(d, h, m, s)
        elif h > 0:
            return "{:02d}:{:02d}:{:02d}".format(h, m, s)
        elif m > 0:
            return "{:02d}:{:02d}".format(m, s)
        elif s > 0:
            return "00:{:02d}".format(s)
        else:
            return "00:00"
    return "-"


def speed_converter(seconds, speed):
    """
    Calculates new duration based on playback speed.
    Formula: New Duration = Total Seconds / Speed
    """
    if seconds is None:
        return "-", 0

    try:
        speed = float(speed)
        seconds = int(seconds)
    except:
        return seconds_to_min(seconds), seconds

    # ✅ FIXED LOGIC: Universal formula for any speed
    if speed > 0:
        new_seconds = int(seconds / speed)
    else:
        new_seconds = seconds

    formatted_time = seconds_to_min(new_seconds)
    return formatted_time, new_seconds


def check_duration(file_path):
    """Gets duration of a media file using ffprobe."""
    command = [
        "ffprobe",
        "-loglevel",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]

    try:
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = pipe.communicate()
        _json = json.loads(out)

        if "format" in _json:
            if "duration" in _json["format"]:
                return float(_json["format"]["duration"])

        if "streams" in _json:
            for s in _json["streams"]:
                if "duration" in s:
                    return float(s["duration"])
    except Exception:
        return "Unknown"

    return "Unknown"


# Supported video formats
formats = [
    "webm", "mkv", "flv", "vob", "ogv", "ogg", "rrc", "gifv", "mng", "mov", 
    "avi", "qt", "wmv", "yuv", "rm", "asf", "amv", "mp4", "m4p", "m4v", 
    "mpg", "mp2", "mpeg", "mpe", "mpv", "m4v", "svi", "3gp", "3g2", "mxf", 
    "roq", "nsv", "flv", "f4v", "f4p", "f4a", "f4b"
]
