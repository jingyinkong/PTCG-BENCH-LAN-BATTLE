# 开发指南

> 开发环境配置、测试、Git 工作流与 CI/CD。

---

## 目录

- [环境配置](#环境配置)
- [运行测试](#运行测试)
- [代码检查](#代码检查)
- [Git 工作流](#git-工作流)
- [CI/CD](#cicd)
- [AI Agent 提交规范](#ai-agent-提交规范)
- [快捷提交 (git-ez)](#快捷提交-git-ez)

---

## 环境配置

### 前置要求

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）

### 安装

```bash
git clone https://github.com/jingyinkong/PTCG-BENCH-LAN-BATTLE.git
cd PTCG-BENCH-LAN-BATTLE

# 安装 Python 依赖
uv sync

# 安装前端依赖
cd frontend && npm install && cd ..
```

### 启动开发服务器

```bash
# 终端 1：启动后端（默认端口 8000）
uv run python backend/main.py

# 终端 2：启动前端（默认端口 5173）
cd frontend && npm run dev
```

---

## 运行测试

```bash
# 全量测试
uv run python -m pytest tests/ -q

# 跳过特定测试
uv run python -m pytest tests/test_ai_battle_framework.py tests/ -q \
  --ignore=tests/agents/test_observer.py \
  --ignore=tests/test_auto_events.py

# 前端构建检查
cd frontend && npm run build
```

---

## 代码检查

```bash
# Python lint
uv run ruff check

# 前端类型检查
cd frontend && npx tsc --noEmit
```

---

## Git 工作流

本项目采用 **GitHub Flow** 工作流。所有变更通过 feature 分支和 Pull Request 进行，main 分支受保护。

### 分支命名

与 [Conventional Commits](https://www.conventionalcommits.org/) 对齐：

| 类型 | 前缀 | 示例 |
|------|------|------|
| 新功能 | `feat/` | `feat/add-dark-mode` |
| Bug 修复 | `fix/` | `fix/coin-toss-edge-case` |
| 杂项维护 | `chore/` | `chore/update-deps` |

### 开发流程

```
main ──●────●────●────●── (受保护，不可直接 push)
        \         /
feat/xxx  ●──●──●  ← PR + Squash merge
```

1. 从 `main` 创建 feature 分支：`git checkout -b feat/your-feature main`
2. 开发和提交（遵循 conventional commits）
3. Push 分支并创建 Pull Request
4. CI 自动运行 lint + test + type check
5. 审查 diff 后，以 **Squash merge** 合并到 main
6. `feat:` 或 `fix:` 前缀的 PR 合并后，自动触发版本发布和打 tag

### 分支保护设置

在 GitHub 仓库 **Settings → Branches → Add branch protection rule** 中设置：

- **Branch name pattern**: `main`
- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
- ✅ Do not allow bypassing the above settings（Administrators 除外）

---

## CI/CD

| Workflow | 触发时机 | 内容 |
|----------|----------|------|
| **CI** (`.github/workflows/ci.yml`) | PR 打开/更新、push main | ruff lint + pytest + tsc type check |
| **Release** (`.github/workflows/release.yml`) | PR 合并到 main | 根据 PR 标题自动 SemVer bump + tag + GitHub Release |

---

## AI Agent 提交规范

如果使用 AI Agent 生成代码并提交 PR，请在 PR 描述中勾选"此 PR 由 AI Agent 生成"并确保已人工审查所有变更。

---

## 快捷提交 (git-ez)

一步完成 stage → commit → push，自动检测 commit 类型：

```bash
# 最简用法（交互式选择类型 + 输入描述）
./scripts/git-ez.sh

# 带描述跳过交互
./scripts/git-ez.sh "添加牌组导入功能"

# 全局别名（可选）
alias gitez='bash scripts/git-ez.sh'
```

脚本会自动：
- 显示变更文件列表
- 从分支名和变更内容推断 commit 类型（feat/fix/docs...）
- 生成 conventional commit 格式的提交信息
- 一键 `git add -A && git commit && git push`
