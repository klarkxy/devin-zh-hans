# -*- coding: utf-8 -*-
r"""
_paths.py — 仓库内所有工具的公共路径解析

本仓库专门维护一个插件，**仓库根目录就是插件根目录**
（package.json / extension.js / assets / translations 都在根上）。
所以这里的「插件」与「仓库」是同一个东西。

Devin 安装位置按常规顺序探测，可用环境变量覆盖：
    DEVIN_INSTALL   例如 D:\Apps\Devin
    DEVIN_HOME      例如 %USERPROFILE%\.devin
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))     # <repo>/tools
ROOT = os.path.dirname(HERE)                          # <repo>

# 受限 shell 写不了仓库部分目录时，用 DEVIN_ZH_ASSETS/DEVIN_ZH_TRANS/DEVIN_ZH_DATA 重定向产物位置
PLUGIN = ROOT                                         # 插件根 = 仓库根
ASSETS = os.environ.get("DEVIN_ZH_ASSETS") or os.path.join(ROOT, "assets")                 # 运行时资源（词典等）
TRANS = os.environ.get("DEVIN_ZH_TRANS") or os.path.join(ROOT, "translations")            # 语言包
DIST = os.environ.get("DEVIN_ZH_DIST") or os.path.join(ROOT, "dist")   # 插件自带的运行时产物（需提交）
BUILD = os.path.join(ROOT, "build")                   # VSIX 打包输出（被 git 忽略）
DATA = os.environ.get("DEVIN_ZH_DATA") or os.path.join(HERE, "data")                     # 中间数据
DICT = os.path.join(HERE, "dict")                     # 人工维护的词表
OUT = BUILD                                           # 兼容旧脚本里的 OUT

# 兼容旧脚本里的别名
SHARED = DICT

_LOCALAPPDATA = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/AppData/Local")
DEVIN_HOME = os.environ.get("DEVIN_HOME") or os.path.join(os.path.expanduser("~"), ".devin")
EXT_ROOT = os.path.join(DEVIN_HOME, "extensions")
BACKUP_ROOT = os.path.join(DEVIN_HOME, "devin-zh-backups")


def find_devin_install():
    """返回 Devin 安装根目录（含 Devin.exe），找不到返回 None。"""
    cands = [
        os.environ.get("DEVIN_INSTALL"),
        os.path.join(_LOCALAPPDATA, "Programs", "Devin"),
        r"C:\Program Files\Devin",
    ]
    for c in cands:
        if c and os.path.exists(os.path.join(c, "Devin.exe")):
            return c
    return None


def find_langpack():
    """返回已安装的简体中文语言包目录，找不到返回 None。"""
    if not os.path.isdir(EXT_ROOT):
        return None
    for d in sorted(os.listdir(EXT_ROOT)):
        if "language-pack-zh-hans" in d:
            p = os.path.join(EXT_ROOT, d)
            if os.path.exists(os.path.join(p, "translations", "main.i18n.json")):
                return p
    return None


DEVIN_INSTALL = find_devin_install()
DEVIN_APP = os.path.join(DEVIN_INSTALL, "resources", "app") if DEVIN_INSTALL else None
LANGPACK = find_langpack()

# 语言包清单（VS Code 的语言包缓存索引）
APPDATA = os.environ.get("APPDATA") or os.path.expanduser("~/AppData/Roaming")
LANGPACKS_JSON = os.path.join(APPDATA, "devin", "languagepacks.json")

CLI = os.path.join(DEVIN_INSTALL, "bin", "devin-desktop.cmd") if DEVIN_INSTALL else None
