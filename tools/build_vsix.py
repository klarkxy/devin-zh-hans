# -*- coding: utf-8 -*-
"""
build_vsix.py — 把本仓库打包成可安装的 .vsix

本仓库专门维护一个插件，仓库根目录就是插件根目录，因此打包器只做一件事：
把根目录下**属于插件的那部分**塞进 VSIX 的 `extension/`，仓库级目录一律排除。

    extension/  ←  package.json / extension.js / assets/ / dist/ / translations/ / README.md / LICENSE

用法:
    python tools/build_vsix.py                  # 输出到 build/
    python tools/build_vsix.py --out somedir
    python tools/build_vsix.py --dry-run        # 只列出会打包哪些文件

VSIX 就是一个 zip：
    [Content_Types].xml
    extension.vsixmanifest
    extension/**
关键 manifest 属性：
    Microsoft.VisualStudio.Code.Engine             = 引擎版本范围
    Microsoft.VisualStudio.Code.LocalizedLanguages = zh-cn   ← 语言包标识
"""
import argparse, json, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 仓库级目录 / 文件：不属于插件，不进 VSIX
EXCLUDE_DIRS = {
    ".git", ".github", ".vscode", "tools", "docs", "build", ".verify",
    ".learnings",
    "node_modules", "__pycache__", ".venv",
    # .backup 里是 patch_now.js 留的原始 webapp chunk（2.2 MB），纯本地调试产物
    ".backup",
    # 受限 shell 下的构建暂存区（重定向产物与调查脚本），绝不进分发包
    ".tmp-data", ".acl-recovery",
}
EXCLUDE_FILES = {
    ".gitignore", ".gitattributes", ".editorconfig", "CHANGELOG.md",
    # 会话工作痕迹，不属于插件
    ".scratch-write-test.txt", ".acl-recovery",
}

MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{name}" Version="{version}" Publisher="{publisher}" />
    <DisplayName>{displayName}</DisplayName>
    <Description xml:space="preserve">{description}</Description>
    <Tags>{tags}</Tags>
    <Categories>{categories}</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{engine}" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value="" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value="" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionSettings" Value="" />
      <Property Id="Microsoft.VisualStudio.Code.LocalizedLanguages" Value="{languages}" />
    </Properties>
    <License>extension/LICENSE</License>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE" Addressable="true" />
  </Assets>
</PackageManifest>
'''

CONTENT_TYPES = '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension=".json" ContentType="application/json"/>
  <Default Extension=".js" ContentType="application/javascript"/>
  <Default Extension=".md" ContentType="text/markdown"/>
  <Default Extension=".txt" ContentType="text/plain"/>
  <Default Extension=".vsixmanifest" ContentType="text/xml"/>
  <Default Extension=".xml" ContentType="text/xml"/>
  <Default Extension=".png" ContentType="image/png"/>
</Types>
'''


def localized_languages(pkg):
    return ",".join(loc.get("languageId", "")
                    for loc in (pkg.get("contributes", {}) or {}).get("localizations", []) or []
                    if loc.get("languageId"))


def collect():
    """返回 (相对路径列表, package.json 对象)"""
    pkg_path = os.path.join(ROOT, "package.json")
    if not os.path.exists(pkg_path):
        raise SystemExit("✗ 根目录没有 package.json")
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    for req in ("name", "version", "publisher", "displayName", "description", "engines"):
        if req not in pkg:
            raise SystemExit("✗ package.json 缺少字段: %s" % req)

    files = []
    for dirpath, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in names:
            if fn in EXCLUDE_FILES:
                continue
            p = os.path.join(dirpath, fn)
            files.append(os.path.relpath(p, ROOT).replace("\\", "/"))
    return sorted(files), pkg


def pack(out_dir):
    files, pkg = collect()
    manifest = MANIFEST.format(
        name=pkg["name"], version=pkg["version"], publisher=pkg["publisher"],
        displayName=pkg["displayName"], description=pkg["description"],
        engine=pkg["engines"]["vscode"],
        tags=",".join(pkg.get("keywords", [])),
        categories=",".join(pkg.get("categories", ["Other"])),
        languages=localized_languages(pkg),
    )
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "%s-%s.vsix" % (pkg["name"], pkg["version"]))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("extension.vsixmanifest", manifest)
        for rel in files:
            z.write(os.path.join(ROOT, rel), "extension/" + rel)
    print("✓ %s" % out)
    print("    %d 个文件, %.2f MB, ID = %s.%s @ %s"
          % (len(files), os.path.getsize(out) / 1048576,
             pkg["publisher"], pkg["name"], pkg["version"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "build"), help="产物目录（默认 build/）")
    ap.add_argument("--dry-run", action="store_true", help="只列出会打包哪些文件")
    args = ap.parse_args()

    if args.dry_run:
        files, pkg = collect()
        print("会打包 %d 个文件到 extension/：\n" % len(files))
        for f in files:
            print("   %-46s %9d B" % (f, os.path.getsize(os.path.join(ROOT, f))))
        print("\n排除的仓库级目录: %s" % ", ".join(sorted(EXCLUDE_DIRS)))
        print("排除的文件:       %s" % ", ".join(sorted(EXCLUDE_FILES)))
        return 0

    pack(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
