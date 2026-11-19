import io, re
p = r'tools/data/zh/webapp/_w32_build.py'
s = io.open(p, encoding='utf-8').read()
fixes = [
    ('"此周期内此事项下没有工作事项。"', '"此周期内，此事项下没有工作事项。"'),
    ('"还没有人的侧边栏里有此看板"', '"还没有人的侧边栏里有这个看板"'),
    ('"尚未安装在 {{accounts, list}} 上。在安装之前，Devin 会在那里执行审批。"',
     '"尚未在 {{accounts, list}} 上安装。在安装之前，Devin 会在那里执行审批。"'),
    ('"构建 VM 仅适用该配置文件的网络策略。默认继承会话设置。"',
     '"构建 VM 仅适用该配置文件的网络策略。继承会话默认值。"'),
    ('"连续 {{count}} 次或更多构建失败、或没有可用快照的组织环境与独立环境"',
     '"连续 {{count}} 次及以上构建失败、或没有可用快照的组织环境与独立环境"'),
    ('"前哨“{{name}}”机器无法启动；该会话已从队列中移出"',
     '"前哨“{{name}}”的机器无法启动；该会话已从队列中移出"'),
]
for a, b in fixes:
    assert s.count(a) == 1, (a, s.count(a))
    s = s.replace(a, b)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', len(fixes))
