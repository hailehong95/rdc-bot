#!/usr/bin/env python
import os
import string
import random
import platform
import PyInstaller.__main__

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(BASE_DIR, 'build')
PACKER_DIR = os.path.join(BASE_DIR, 'packer')
RELEASE_DIR = os.path.join(BASE_DIR, 'releases')
PYTHON_SCRIPT = "rdcbot.py"
WINDOWS_EXE = "rdcbot"


def string_random(n):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(n))


def is_win64():
    return platform.architecture()[0] == "64bit"


def get_upx_path():
    upx32 = os.path.join(PACKER_DIR, "upx32", "upx.exe")
    upx64 = os.path.join(PACKER_DIR, "upx64", "upx.exe")
    if is_win64() and os.path.isfile(upx64):
        return os.path.dirname(upx64)
    if not is_win64() and os.path.isfile(upx32):
        return os.path.dirname(upx32)
    return ""


def build_task():
    try:
        if platform.system() != "Windows":
            print("This platform does not support!")
            return
        upx_path = get_upx_path()
        cmd = ['--clean', '--noconsole', '--uac-admin', '--icon', 'NONE', '--onefile', '--name', WINDOWS_EXE,
               '--distpath', RELEASE_DIR, '--key', string_random(16)]
        if upx_path:
            cmd.extend(['--upx-dir', upx_path])
        cmd.append(PYTHON_SCRIPT)
        PyInstaller.__main__.run(cmd)
    except Exception as ex:
        print("Exception - build_task: %s" % str(ex))


if __name__ == '__main__':
    build_task()
