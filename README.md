# PTCG-BENCH-LAN-BATTLE

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12%2B-blue.svg" alt="Python 3.12+"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-20%2B-green.svg" alt="Node 20+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-backend-teal.svg" alt="FastAPI"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-18-blue.svg" alt="React 18"></a>
</p>

基于 [PTCG-Bench](https://github.com/zjunet/PTCG-Bench) 二次开发的局域网 PvP 对战增强版。原项目是用于评估 LLM 智能体在宝可梦卡牌游戏中表现的基准测试平台（详见原论文 [arXiv:2605.29653](https://arxiv.org/abs/2605.29653)）。本项目在此基础上新增了实时双人对战功能，支持两位真人玩家通过浏览器进行局域网宝可梦卡牌对战。

---

## 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [局域网对战指南](#局域网对战指南)
- [游戏流程](#游戏流程)
- [硬币抛掷规则](#硬币抛掷规则)
- [系统架构](#系统架构)
- [开发指南](#开发指南)
- [技术栈](#技术栈)
- [引用与致谢](#引用与致谢)

---

## 功能特性

### 🎮 局域网 PvP 对战（本项目新增）

| 功能 | 说明 |
|------|------|
| 房间系统 | 创建房间、加入房间、房间列表、房间删除 |
| 实时 WebSocket | 双方操作实时同步，回合制对战 |
| 硬币抛掷 | 完全遵循 PTCG 官方规则（猜方选正反→胜者选先/后攻） |
| 手牌隐藏 | 每方只能看到自己的手牌，对手手牌以 `???` 隐藏 |
| 视角切换 | 自己始终在棋盘底部，对手在上方 |
| 回合控制 | 非己方回合操作按钮自动禁用，显示等待状态 |
| 投降/退出 | 游戏中可随时点击红色按钮退出 |
| 比赛记录 | 对战结果自动保存到 SQLite 数据库 |

### 🤖 原版 PTCG-Bench 功能

以下功能来自上游项目 [PTCG-Bench](https://github.com/zjunet/PTCG-Bench)：

- 完整宝可梦卡牌游戏引擎（基于 [ptcg-engine](https://github.com/gemelom/ptcg-engine)）
- AI 智能体对战（Random、Charizard Heuristic、ReAct、Skill Evolving）
- 对战回放查看与 JSONL 导出
- Agent 排行榜（基于 OpenSkill 评级）
- 卡组浏览与详情查看
- 卡牌图片自动获取与缓存

---

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）

### 安装

```bash
git clone https://github.com/jingyinkong/PTCG-BENCH-LAN-BATTLE.git
cd PTCG-BENCH-LAN-BATTLE

# 安装 Python 依赖（含 ptcg-engine）
uv sync

# 安装前端依赖
cd frontend && npm install && cd ..
```

### 启动

```bash
# 终端 1：启动后端（默认端口 8000）
uv run python backend/main.py

# 终端 2：启动前端（默认端口 5173）
cd frontend && npm run dev
```

浏览器访问 **http://localhost:5173** 即可。

> 💡 **局域网提示**：如需在同一局域网内对战，设置环境变量 `LAN_MODE=1` 启动后端，Vite 配置中添加 `--host 0.0.0.0` 即可让其他设备访问。

---

## 局域网对战指南

### 1. 注册/登录

首次使用需要注册账号。用户名 3–20 个字符，密码至少 6 个字符。

> 📌 测试账号：`liuyang` / `yangfan`，密码均为 `123456`

### 2. 进入大厅

登录后点击首页的 **"LAN Battle"** 按钮进入对战大厅。

### 3. 创建或加入房间

| 操作 | 按钮 | 说明 |
|------|------|------|
| 创建房间 | **Create Room** | 选择卡组后创建，自己的房间会**蓝色高亮**显示 |
| 加入房间 | **Join** | 在列表中点击对手的房间 |
| 取消房间 | **Cancel Room** | 红色按钮，仅房主可见 |

### 4. 开始对战

房主确认对手已加入后，点击 **"Start Game"**。

### 5. 硬币抛掷 🎲

系统随机选一位玩家作为「猜方」：

- 猜方选择 **Heads（正面）** 或 **Tails（反面）**
- 猜对 → 猜方获得选择先/后攻的权利
- 猜错 → 对手获得选择先/后攻的权利
- 获得权利的一方选择 **Go First（先攻）** 或 **Go Second（后攻）**

### 6. 对战操作

- **选择宝可梦上场**：游戏开始时选择基础宝可梦放到战斗场 → 点击 Confirm
- **攻击**：能量满足时选择攻击技能攻击对手宝可梦
- **贴能量**：每回合可贴一张能量卡
- **使用训练家卡**：物品、支援者、道具等
- **撤退**：将战斗宝可梦与备战宝可梦交换
- **投降**：随时点击红色 **"Surrender / Leave Game"** 退出

### 7. 胜负判定

击倒对手宝可梦（Knock Out）可拿取奖赏卡。**率先拿完 6 张奖赏卡的一方获胜**。

---

## 游戏流程

```
注册/登录
    ↓
LAN Battle 大厅
    ↓
创建房间 / 加入房间（选择卡组）
    ↓
房主点击 Start Game
    ↓
🎲 硬币抛掷（确定先手）
    ↓
🃏 选择宝可梦上场 + 备战（双方各自确认）
    ↓
╔═════════ 对战循环 ═════════╗
║  ① 抽卡                     ║
║  ② 贴能量、进化、训练家卡   ║
║  ③ 攻击对手宝可梦           ║
║  ④ 击倒对手 → 拿取奖赏卡   ║
║  ⑤ 回合结束，换对手操作     ║
╚═════════════════════════════╝
    ↓
🏆 奖赏卡拿完 → 分出胜负
    ↓
📊 比赛记录自动保存
```

---

## 硬币抛掷规则

完整遵循 PTCG 官方规则，通过 WebSocket 实现交互式抛硬币：

```
双方连接 WebSocket
    ↓
服务端随机选出「猜方」
    ↓  COIN_TOSS { phase: "call" }
猜方选择 Heads / Tails
    ↓  COIN_TOSS_CALL { choice: "heads"|"tails" }
服务端抛硬币
    ↓  COIN_TOSS { phase: "result", coin: "heads"|"tails" }
┌─ 猜对 → 猜方获权利 ─┐
│                      ↓
│               选择先攻 / 后攻
│                      ↓
└─ 猜错 → 对手获权利 ─┘
    ↓  COIN_TOSS_CHOOSE { choice: "first"|"second" }
🎮 游戏引擎创建，先攻方为 PLAYER1
```

---

## 系统架构

```
┌──────────────┐    WebSocket     ┌──────────────┐
│  玩家 1 浏览器 │◄══════════════►│  玩家 2 浏览器 │
│  React SPA   │    REST API     │  React SPA   │
└──────┬───────┘        ▲        └──────┬───────┘
       │                │               │
       ▼                ▼               ▼
┌──────────────────────────────────────────────┐
│              FastAPI 后端                     │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐  │
│  │ auth.py   │ │game_rooms│ │ pvp_game.py │  │
│  │ JWT 认证  │ │ 房间CRUD │ │ PvP WS 管理 │  │
│  └──────────┘ └──────────┘ └─────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │    PTCG 游戏引擎 (ptcg-engine)       │    │
│  │    状态管理 │ 动作系统 │ 卡牌逻辑   │    │
│  └──────────────────────────────────────┘    │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │    SQLite 数据库                      │    │
│  │    用户表 │ 会话表 │ 比赛记录表      │    │
│  └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

---

## 开发指南

### 项目结构

```
PTCG-BENCH-LAN-BATTLE/
├── backend/
│   ├── main.py               # FastAPI 入口 + PvP WebSocket 处理
│   ├── auth.py               # JWT 用户注册/登录/认证
│   ├── database.py           # SQLite 数据库初始化
│   ├── game_rooms.py         # 房间 CRUD + 后台 GC
│   ├── pvp_game.py           # PvP 管理器（连接/断开/验证/广播）
│   └── match_records.py      # 比赛记录查询/统计
├── frontend/src/
│   ├── App.tsx               # 主应用路由
│   ├── stores/
│   │   ├── gameStore.ts      # 游戏状态管理 (Zustand)
│   │   └── authStore.ts      # 认证状态管理
│   └── components/
│       ├── GameBoard.tsx          # 游戏棋盘（PvP 视角自动切换）
│       ├── PlayerArea.tsx         # 玩家区域渲染
│       ├── ActionPanel.tsx        # 操作面板（回合控制）
│       ├── CardSelectionOverlay   # 选牌弹窗（Confirm 确认）
│       ├── LobbyPage.tsx          # 对战大厅（房间列表）
│       ├── MatchHistory.tsx       # 比赛记录页面
│       ├── AuthPage.tsx           # 登录/注册页面
│       └── NavBar.tsx             # 导航栏
├── pyproject.toml            # Python 项目配置
└── uv.lock                   # Python 依赖锁定
```

### 运行测试

```bash
# 后端单元测试
uv run python -m pytest tests/ -x -q

# 前端构建检查
cd frontend && npm run build
```

### PvP 消息协议

| 消息 | 方向 | 说明 |
|------|------|------|
| `COIN_TOSS` | 服务端→客户端 | 硬币抛掷各阶段（phase: call / result） |
| `COIN_TOSS_CALL` | 客户端→服务端 | 猜方选择 heads 或 tails |
| `COIN_TOSS_CHOOSE` | 客户端→服务端 | 权利方选择 first 或 second |
| `ROLE_ASSIGN` | 服务端→客户端 | 先手角色分配（交换 WS 连接后通知） |
| `STATE_UPDATE` | 服务端→客户端 | 游戏状态更新（含手牌过滤 + 选牌提示过滤） |
| `ACTION` | 客户端→服务端 | 玩家操作（攻击/上场/贴能/进化/训练家等） |
| `GAME_OVER` | 服务端→客户端 | 游戏结束 + 胜者 |
| `OPPONENT_DISCONNECTED` | 服务端→客户端 | 对手断线（30 秒重连窗口） |

---

## 技术栈

| 层级 | 技术 | 来源 |
|------|------|------|
| 游戏引擎 | ptcg-engine | [gemelom/ptcg-engine](https://github.com/gemelom/ptcg-engine) |
| AI 对战平台 | PTCG-Bench | [zjunet/PTCG-Bench](https://github.com/zjunet/PTCG-Bench) |
| 后端框架 | FastAPI + WebSocket | 本项目 |
| 前端框架 | React 18 + TypeScript | 本项目（基于原版修改） |
| 状态管理 | Zustand | 本项目 |
| 构建工具 | Vite 8 + Tailwind CSS | 本项目 |
| 数据库 | SQLite | 本项目 |
| 认证 | JWT + bcrypt | 本项目 |

---

## 引用与致谢

### 上游项目

本项目的游戏引擎和 AI 对战功能来自以下开源项目：

- **[PTCG-Bench](https://github.com/zjunet/PTCG-Bench)** — 用于评估 LLM 智能体的宝可梦卡牌基准测试平台
- **[ptcg-engine](https://github.com/gemelom/ptcg-engine)** — 宝可梦卡牌游戏引擎（PTCG 规则实现）

如果您在学术研究中使用本项目，请引用原论文：

```bibtex
@misc{hua2026ptcgbenchllmagentsmaster,
      title={PTCG-Bench: Can LLM Agents Master Pok\'emon Trading Card Game?},
      author={Dongdong Hua and Yifei Sun and Renhong Huang and Feng Gao
              and Chunping Wang and Yang Yang},
      year={2026},
      eprint={2605.29653},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2605.29653},
}
```

### 本项目贡献

在 PTCG-Bench 基础上新增的局域网 PvP 功能包括：房间系统、交互式硬币抛掷、WebSocket 实时通信、手牌隐藏、视角切换、回合控制、游戏中投降、比赛记录持久化等。

---

## 许可证

本项目基于 PTCG-Bench 修改，遵循原项目的 MIT License。详见 [LICENSE](LICENSE)。

## 商标声明

本独立研究项目与 The Pokémon Company、Nintendo、Creatures Inc. 或 GAME FREAK inc. 无任何关联。Pokémon 及相关名称、卡牌、图像均为其各自所有者的商标或版权材料。
