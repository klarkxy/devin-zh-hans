# -*- coding: utf-8 -*-
"""w45 builder: webapp-todo.json lines 10801-10965 (1-based, inclusive).

Keys are extracted verbatim from the source lines (json.loads per line), so a
typo in the key is impossible: only translations are hand-written here.
"""
import json
import io
import os

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w45.json"
FIRST, LAST = 10801, 10965

T = {
    10801: "{{name}} 将不再记得此文件中保存的内容。",
    10802: "{{name}} 将停止响应。你可以稍后再取消归档。",
    10803: "{{name}} 将停止审查拉取请求并移入已归档列表，之后可从那里恢复。它已发布的发现会保留。",
    10807: "{{name}} — 值班",
    10808: "{{name}} 自己的",
    10809: "{{name}} 自己的账号",
    10810: "{{name}} 自己的指令位于其设置中",
    10811: "{{name}} 专属的 {{botName}}",
    10812: "{{name}}，已固定，可拖动",
    10813: "{{name}}：本期已消耗 {{consumed}}，共 {{limit}}",
    10814: "{{name}} 的 {{botName}}",
    10815: "按产品统计的 {{noun}}",
    10816: "已消耗的 {{noun}}",
    10817: "所选区间内已消耗的 {{noun}}",
    10818: "已使用的 {{noun}}",
    10820: "{{organization}} 的账号",
    10821: "{{org}}（默认）",
    10822: "{{org}} 无法访问 {{layer}} 来源的仓库，因此它们在此处不显示。",
    10823: "{{other}} 已与其他人员共享。所有能使用 {{other}} 的人都会看到 {{name}} 写入其中的内容。",
    10824: "{{outpost}} 及其本地网络",
    10825: "{{owner}}（通过 {{bot}}）",
    10827: "{{path}} 的内容",
    10829: "占全部的 {{percent}}",
    10830: "已用上下文 {{percent}}%（{{used}} / {{limit}}）",
    10831: "{{percent}}% 可用",
    10832: "{{period}} · 已合并 {{merged}} · 未关闭 {{open}}",
    10833: "{{price}}/月",
    10834: "{{price}}/月",
    10835: "{{price}}/年",
    10836: "{{productName}} + Devin CLI 管理员",
    10837: "{{productName}} + Devin CLI 权限",
    10838: "需要 {{productName}} 访问权限",
    10839: "{{productName}} 没有打开？",
    10841: "{{provider}} 已连接",
    10842: "无法连接到 {{provider}}。请检查该服务器及其与 Devin 的连接是否正常，然后刷新。",
    10843: "新加入队列 {{queued}} 个，已在队列中 {{pending}} 个，未找到 {{missing}} 个。",
    10844: "已提出 {{raised}} 个 · 合并率 {{rate}}",
    10845: "{{rate}} ACU/分钟",
    10846: "{{rate}}/分钟",
    10849: "{{reason}}。取消勾选“保存到以后的会话”，即可仅在本次会话中提供此密钥。",
    10851: "{{repo}} 将在你选择的组织中变为可用。",
    10853: "{{route}} 已通过 {{gateway}} 路由",
    10854: "{{route}} 不是精确的主机名或 IPv4 地址/CIDR",
    10855: "{{row}} 操作",
    10856: "{{count}} 个扫描配置中有 {{running}} 个正在运行",
    10858: "{{seats}} 个未分配",
    10859: "已选择 {{selectedReposCount}} 个仓库",
    10860: "已选择 {{selected}} / {{total}} 个域名",
    10861: "{{sender}} 将能够读取 {{target}}、向其发送消息并指挥其会话，并使用其权限、连接和密钥。你可以在“访问”页面中撤销。",
    10864: "{{severities, list}} 严重级别",
    10865: "{{severities, list}}（含 <skills/>）",
    10866: "占全部 ACU 的 {{share}}",
    10867: "占已关联 ACU 的 {{share}}",
    10868: "占已关联会话的 {{share}}",
    10869: "占 {{total}} 个合同的 {{share}}",
    10870: "占 {{total}} 个会话的 {{share}}",
    10871: "占 {{total}} 个会话的 {{share}}",
    10873: "{{sites, list}} 会以连接它们的管理员账号发表评论。添加服务账号凭据后，Devin 就能以自己的身份发表评论，议题也可以指派给它。",
    10874: "{{sites, list}} 会以连接它的管理员账号发表评论。添加服务账号凭据后，Devin 就能以自己的身份发表评论，议题也可以指派给它。",
    10881: "已选择 {{size}}",
    10882: "{{skill}} 已变更。在你批准之前，此审查器会沿用当前的指令。",
    10883: "{{source}} 详情",
    10891: "由 {{approver}} 于 {{at}} {{status}}",
    10892: "由 {{name}} 于 {{at}} {{status}}",
    10893: "{{status}} 列表",
    10894: "{{status}} · {{count}} 个发现",
    10895: "{{status}} · {{count}} 个发现",
    10897: "{{status}} — <backLink>返回所有映射</backLink>",
    10898: "来自 {{orgs}} 的 {{subjects}}",
    10899: "发往 {{orgs}} 的 {{subjects}}",
    10903: "已测试 {{tested}} 个，有发现的 {{finding}} 个，未关闭 {{open}} 个，不适用 {{notApplicable}} 个",
    10904: "{{time}}。在相对时间和绝对时间之间切换",
    10908: "{{totaluses}} 次调用",
    10909: "共 {{total}} 分",
    10910: "共 {{total}} 分",
    10911: "{{total}} 个会话",
    10912: "{{total}} 个会话",
    10914: "{{trigger}} 尚不可用",
    10915: "{{trigger}} 触发器需要先选择团队",
    10916: "{{trigger}} 触发器需要按“{{field}}”设置筛选条件",
    10917: "{{type}} · 客户端 ID {{clientId}}",
    10919: "本周期已消耗的 {{unit}}",
    10920: "上一周期已消耗的 {{unit}}",
    10921: "本月已消耗的 {{unit}}",
    10922: "上一周期（{{cycle}}）的 {{unit}}",
    10923: "本周期（{{cycle}}）的 {{unit}}",
    10924: "本月的 {{unit}}",
    10925: "已消耗 {{used}} / {{budget}} ACU",
    10926: "已消耗 {{used}} / {{budget}}",
    10928: "{{used}} / {{maxSlots}} 个槽位",
    10929: "{{used}} ACU",
    10930: "{{used}} / {{limit}} ACU",
    10931: "已使用按需额度 {{used}} / {{limit}} · {{resetsOn}} 重置",
    10932: "已使用按需额度 {{used}} · {{resetsOn}} 重置",
    10933: "{{users}} 和 {{groups}}",
    10934: "{{valid}} 个有效，{{invalid}} 个无效",
    10938: "{{value}} 字符",
    10939: "{{value}} 分",
    10940: "{{value}} 分",
    10943: "{{value}}K 字符",
    10944: "{{value}} 小时前",
    10945: "{{value}} 分钟前",
    10947: "{{value}} 秒前",
    10949: "{{wait}} 在 <elapsed></elapsed> 后放弃。",
    10950: "{{wait}} 在 <elapsed></elapsed> 后就绪。",
    10951: "{{wait}} 目前已等待 <elapsed></elapsed>。",
    10952: "{{width}} × {{height}} px 区域 · {{count}} 个元素",
    10953: "{{width}} × {{height}} px 区域 · {{count}} 个元素",
    10954: "横向 {{x}}，纵向 {{y}}",
    10955: "约占未分类会话的 {{share}}%",
    10956: "· 创建者",
    10957: "· 生成中",
    10958: "· 于 {{time}} 开始",
    10960: "“{{name}}”为内置安全审查保留。请另选一个名称。",
    10961: "“{{value}}”看起来不是邮箱地址，将被视为无效",
    10962: "• 每条命令的超时时间为 2 分钟",
    10963: "• 启动命令在主目录中运行",
    10964: "• 它们按所列顺序执行",
    10965: "……（已截断）",
}


def load_source_slice():
    with io.open(SRC, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    out = []  # [(lineno, key)]
    for lineno in range(FIRST, LAST + 1):
        raw = lines[lineno - 1].rstrip()
        if raw.endswith(","):
            raw = raw[:-1]
        obj = json.loads("{" + raw + "}")
        (key,) = obj.keys()
        out.append((lineno, key))
    return out


def main():
    src = load_source_slice()
    pairs = []
    skipped = []
    for lineno, key in src:
        if lineno in T:
            pairs.append((lineno, key, T[lineno]))
        else:
            skipped.append((lineno, key))

    unknown = sorted(set(T) - set(ln for ln, _ in src))
    assert not unknown, "translations for lines outside slice: %r" % (unknown,)

    lines_out = ["{"]
    for i, (lineno, key, val) in enumerate(pairs):
        k = json.dumps(key, ensure_ascii=False)
        v = json.dumps(val, ensure_ascii=False)
        lines_out.append("  %s: %s%s" % (k, v, "," if i < len(pairs) - 1 else ""))
    lines_out.append("}")
    data = "\n".join(lines_out) + "\n"

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)

    print("source entries : %d" % len(src))
    print("translated     : %d" % len(pairs))
    print("skipped        : %d" % len(skipped))
    for lineno, key in skipped:
        print("  SKIP %d  %s" % (lineno, key))


if __name__ == "__main__":
    main()
