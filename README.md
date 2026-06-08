# PTCG-BENCH-LAN-BATTLE

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12%2B-blue.svg" alt="Python 3.12+"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-20%2B-green.svg" alt="Node 20+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-backend-teal.svg" alt="FastAPI"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-18-blue.svg" alt="React 18"></a>
</p>

基于 [PTCG-Bench](https://github.com/zjunet/PTCG-Bench) 二次开发的局域网 PvP 对战增强版。原项目是用于评估 LLM 智能体在宝可梦卡牌游戏中表现的基准测试平台（详见原论文 [arXiv:2605.29653](https://arxiv.org/abs/2605.29653)）。本项目在此基础上新增了实时双人对战功能，支持两位真人玩家通过浏览器进行局域网宝可梦卡牌对战。

---

## 文档导航

| 文档 | 说明 |
|------|------|
| [README](README.md) | 项目介绍与快速开始（本文件） |
| [用户手册](docs/USER_GUIDE.md) | 局域网对战指南、游戏流程、硬币抛掷规则 |
| [系统架构](docs/ARCHITECTURE.md) | 架构设计、项目结构、技术栈、通信协议 |
| [开发指南](docs/DEVELOPMENT.md) | 开发环境、测试、Git 工作流、CI/CD |
| [AI Agent](docs/AI_AGENT.md) | AI 智能体类型、接入方式、Agent 开发 |
| [评测系统](docs/EVALUATION.md) | 评测管线、Benchmark、排行榜、对战回放 |

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

### 运行测试

```bash
# 全量测试
uv run python -m pytest tests/ -q

# 前端构建检查
cd frontend && npm run build
```

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

---

## 许可证

本项目基于 PTCG-Bench 修改，遵循原项目的 MIT License。详见 [LICENSE](LICENSE)。

## 商标声明

本独立研究项目与 The Pokémon Company、Nintendo、Creatures Inc. 或 GAME FREAK inc. 无任何关联。Pokémon 及相关名称、卡牌、图像均为其各自所有者的商标或版权材料。
