# 系统架构

> PTCG-Bench 的系统架构、项目结构、技术栈与通信协议。

---

## 目录

- [架构总览](#架构总览)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [PvP 消息协议](#pvp-消息协议)
- [数据存储](#数据存储)

---

## 架构总览

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

### 三层架构

| 层级 | 职责 | 技术 |
|------|------|------|
| **前端 (Frontend)** | 游戏 UI 渲染、用户交互、WebSocket 通信 | React 18 + TypeScript + Zustand + Vite |
| **后端 (Backend)** | REST API、WebSocket 管理、游戏房间协调 | FastAPI + Pydantic |
| **引擎 (Engine)** | PTCG 规则执行、状态转移、合法动作生成 | ptcg-engine (Gymnasium-like API) |

### 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| 认证 | `backend/auth.py` | JWT 用户注册/登录/认证 |
| 游戏房间 | `backend/game_rooms.py` | 房间 CRUD + 后台 GC |
| PvP 管理 | `backend/pvp_game.py` | PvP 连接/断开/验证/广播 |
| 比赛记录 | `backend/match_records.py` | 比赛记录查询/统计 |
| 主入口 | `backend/main.py` | FastAPI 入口 + WebSocket 处理 |
| 数据库 | `backend/database.py` | SQLite 初始化与迁移 |
| 引擎补丁 | `backend/engine_patches.py` | Monkey-patch 修复 |

---

## 项目结构

```
PTCG-BENCH-LAN-BATTLE/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # FastAPI 入口 + PvP WebSocket 处理
│   ├── auth.py                 # JWT 用户注册/登录/认证
│   ├── database.py             # SQLite 数据库初始化
│   ├── game_rooms.py           # 房间 CRUD + 后台 GC
│   ├── pvp_game.py             # PvP 管理器
│   ├── match_records.py        # 比赛记录查询/统计
│   ├── test_runner.py          # Web 端 AI 测试管理
│   ├── deck_manager.py         # 牌组管理 API
│   ├── issue_reporter.py       # 问题报告 API
│   ├── cost_tracker.py         # LLM 成本追踪
│   ├── engine_patches.py       # 引擎 Monkey-patch
│   └── settings.py             # 后端配置
│
├── frontend/src/               # React 前端
│   ├── App.tsx                 # 主应用路由
│   ├── stores/                 # Zustand 状态管理
│   │   ├── gameStore.ts        # 游戏状态
│   │   ├── authStore.ts        # 认证状态
│   │   └── deckStore.ts        # 牌组状态
│   ├── components/             # UI 组件
│   │   ├── GameBoard.tsx       # 游戏棋盘
│   │   ├── PlayerArea.tsx      # 玩家区域
│   │   ├── ActionPanel.tsx     # 操作面板
│   │   ├── LobbyPage.tsx       # 对战大厅
│   │   ├── MatchHistory.tsx    # 比赛记录
│   │   ├── AuthPage.tsx        # 登录/注册
│   │   ├── TestManager.tsx     # AI 测试管理
│   │   ├── IssueReview.tsx     # 问题审查
│   │   └── NavBar.tsx          # 导航栏
│   ├── services/               # API 调用封装
│   ├── i18n/                   # 国际化资源
│   └── types/                  # 类型定义
│
├── ptcg/                       # PTCG 游戏引擎
│   ├── core/                   # 核心引擎
│   │   ├── envs.py             # PokemonTCG 主环境
│   │   ├── state.py            # 游戏状态
│   │   ├── player.py           # 玩家区域管理
│   │   ├── action.py           # 动作系统
│   │   ├── card.py             # 卡牌基类
│   │   ├── recorder.py         # 对局录像
│   │   └── enums.py            # 枚举定义
│   ├── cards/                  # 卡牌实现
│   ├── decks/                  # 牌组文件
│   └── utils/                  # 工具函数
│
├── ptcgbench/                  # Agent + Bench + 服务
│   ├── agents/                 # AI Agent 实现
│   ├── bench/                  # 评测管线
│   └── services/               # 外部服务
│
├── tests/                      # 测试
├── scripts/                    # 工具脚本
├── docs/                       # 文档
├── battle_log/                 # 对局录像输出
├── card_data/                  # 卡牌数据缓存
├── pyproject.toml              # Python 项目配置
└── README.md
```

---

## 技术栈

| 层级 | 技术 | 来源 |
|------|------|------|
| 游戏引擎 | ptcg-engine | [gemelom/ptcg-engine](https://github.com/gemelom/ptcg-engine) |
| AI 对战平台 | PTCG-Bench | [zjunet/PTCG-Bench](https://github.com/zjunet/PTCG-Bench) |
| 后端框架 | FastAPI + WebSocket | 本项目 |
| LLM SDK | openai >= 2.29.0 (多 provider) | 本项目 |
| 前端框架 | React 18 + TypeScript | 本项目 |
| 状态管理 | Zustand | 本项目 |
| 构建工具 | Vite 8 + Tailwind CSS | 本项目 |
| 数据库 | SQLite | 本项目 |
| 认证 | JWT + bcrypt | 本项目 |
| 包管理 | uv + setuptools | 本项目 |
| 测试 | pytest >= 9.0.2 | 本项目 |

---

## PvP 消息协议

| 消息 | 方向 | 说明 |
|------|------|------|
| `COIN_TOSS` | 服务端→客户端 | 硬币抛掷各阶段（phase: call / result） |
| `COIN_TOSS_CALL` | 客户端→服务端 | 猜方选择 heads 或 tails |
| `COIN_TOSS_CHOOSE` | 客户端→服务端 | 权利方选择 first 或 second |
| `ROLE_ASSIGN` | 服务端→客户端 | 先手角色分配 |
| `STATE_UPDATE` | 服务端→客户端 | 游戏状态更新（含手牌过滤） |
| `ACTION` | 客户端→服务端 | 玩家操作 |
| `GAME_OVER` | 服务端→客户端 | 游戏结束 + 胜者 |
| `OPPONENT_DISCONNECTED` | 服务端→客户端 | 对手断线（30 秒重连窗口） |

---

## 数据存储

| 数据类型 | 位置 | 格式 |
|---------|------|------|
| 用户/会话/比赛记录 | `backend/data/ptcg.db` | SQLite |
| 对局录像 | `battle_log/seed_{seed}.jsonl` | JSONL |
| 卡牌元数据 | `card_data_cache.json` | JSON |
| 中文翻译 | `card_chinese_data.json` | JSON |
| 卡牌图片 | `card_data/` | 二进制图片 |
| Agent 记忆 | MemoryStore 路径配置 | JSON |
