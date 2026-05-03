# 🏰 Retro MUD Revival

一个复刻早期经典文字 MUD（Multi-User Dungeon）的 Python 实现，支持 Telnet 直连和 Web 终端双端游玩。

## 快速开始

```powershell
cd retro-mud-revival
.\start.ps1
```

自动打开浏览器，显示复古 CRT 终端界面，输入名字即可开始冒险。

## 连接方式

| 方式 | 地址 |
|------|------|
| Web 终端 | `web/index.html`（通过 WebSocket 桥接） |
| Telnet | `telnet localhost 4000` |
| WebSocket | `ws://localhost:8080` |

## 可用命令

```
look / l              观察周围环境
go <方向>             移动 (north/south/east/west/up/down)
take <物品>           捡起物品
drop <物品>           丢弃物品
inventory / i         查看背包
use <物品>            使用消耗品（药水、食物）
equip <武器>          装备武器
attack <目标>         攻击敌人
talk <NPC>            与 NPC 对话 / 接任务 / 交易
say <内容>            同房间玩家可见的聊天
quest                 查看任务列表
quest accept <id>     接受任务
buy <物品>            从商人购买
sell <物品>           向商人出售
save                  存档
load                  读档
status                查看自身状态
help / ?              帮助
quit                  退出
```

## 世界地图

```
                    [地牢三层] ← [地牢二层] ← [地牢一层]
                                                 ↑
[酒馆] ← [新手村广场] → [铁匠铺]              [黑暗洞穴入口]
           ↓                                         ↑
      [森林边缘] → [幽深小径] → [古遗迹入口]
           ↓
      [湖边营地]
```

## 任务列表

| 任务ID | 名称 | 类型 | 发布人 |
|--------|------|------|--------|
| `kill_wolf` | 森林的威胁 | 击杀野狼 | 铁匠老王 |
| `collect_potion` | 采集药水 | 收集红色药水 | 酒馆老板 |
| `explore_cave` | 洞穴调查 | 击杀地精侦察兵 | 酒馆老板 |

## 技术栈

- **后端**: Python asyncio + Telnet Server
- **桥接**: WebSocket → Telnet 双向转发
- **前端**: xterm.js + CRT 扫描线特效
- **协议**: ACPrompt Agent 网络协作

## 项目成员

- **kimi-cli** (lead) — 后端架构、游戏引擎、地图系统
- **claude-code** (member) — 剧情设计、Web 终端优化、ASCII 地图
