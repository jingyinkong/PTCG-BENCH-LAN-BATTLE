#!/bin/bash
# ============================================================
# git-ez — 傻瓜式 GitHub 提交脚本
# 用法: ./scripts/git-ez.sh [描述]
# ============================================================
set -e

# ---- 颜色 ----
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}══════════════════════════════════════${NC}"
echo -e "${CYAN}  git-ez · 傻瓜式 GitHub 提交${NC}"
echo -e "${CYAN}══════════════════════════════════════${NC}"
echo ""

# ---- 1. 检查是否在 git 仓库中 ----
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo -e "${RED}❌ 当前目录不是 git 仓库${NC}"
    exit 1
fi

# ---- 2. 显示当前状态 ----
BRANCH=$(git branch --show-current)
echo -e "📍 当前分支: ${GREEN}$BRANCH${NC}"

# 检查是否有未提交的变更
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo -e "${YELLOW}✅ 工作区干净，没有需要提交的内容${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}📋 变更文件:${NC}"
git status --short
echo ""

# ---- 3. 自动检测 commit 类型 ----
detect_type() {
    # 从分支名推断
    if echo "$BRANCH" | grep -qiE '^(feat|feature)[-/]'; then
        echo "feat"
        return
    elif echo "$BRANCH" | grep -qiE '^fix[-/]'; then
        echo "fix"
        return
    elif echo "$BRANCH" | grep -qiE '^(docs|doc)[-/]'; then
        echo "docs"
        return
    elif echo "$BRANCH" | grep -qiE '^chore[-/]'; then
        echo "chore"
        return
    fi

    # 从变更内容推断
    CHANGED=$(git diff --name-only HEAD 2>/dev/null || git diff --cached --name-only)
    NEW=$(git ls-files --others --exclude-standard)
    ALL="$CHANGED $NEW"

    if echo "$ALL" | grep -qiE '(\.md$|README|docs/)'; then
        echo "docs"
    elif echo "$ALL" | grep -qiE '(test|spec)'; then
        echo "test"
    elif echo "$ALL" | grep -qiE '\.github/'; then
        echo "ci"
    else
        if [ -n "$NEW" ] && [ -z "$(echo "$NEW" | grep -v '\.')" ]; then
            echo "feat"
        else
            echo "feat"
        fi
    fi
}

AUTO_TYPE=$(detect_type)

# ---- 4. 选择 commit 类型 ----
echo -e "${YELLOW}🏷️  选择提交类型 (自动检测: ${GREEN}$AUTO_TYPE${YELLOW}):${NC}"
echo "  1) feat     — 新功能"
echo "  2) fix      — Bug 修复"
echo "  3) docs     — 文档更新"
echo "  4) chore    — 杂项维护"
echo "  5) style    — 样式调整"
echo "  6) refactor — 代码重构"
echo "  7) test     — 测试相关"
echo "  8) ci       — CI/CD 相关"
echo ""
read -p "  输入数字 [1-8] 或直接回车使用自动检测: " TYPE_NUM

case "$TYPE_NUM" in
    1) TYPE="feat" ;;
    2) TYPE="fix" ;;
    3) TYPE="docs" ;;
    4) TYPE="chore" ;;
    5) TYPE="style" ;;
    6) TYPE="refactor" ;;
    7) TYPE="test" ;;
    8) TYPE="ci" ;;
    "") TYPE="$AUTO_TYPE" ;;
    *) echo -e "${RED}❌ 无效选择，使用自动检测: $AUTO_TYPE${NC}"; TYPE="$AUTO_TYPE" ;;
esac

echo -e "  选择: ${GREEN}$TYPE${NC}"
echo ""

# ---- 5. 自动总结变更 ----
auto_summary() {
    local out=""
    local changed=$(git diff --name-only HEAD 2>/dev/null)
    local staged=$(git diff --cached --name-only 2>/dev/null)
    local new=$(git ls-files --others --exclude-standard)
    local all=$(echo -e "$changed\n$staged\n$new" | sort -u | grep -v '^$')

    # 统计每个目录的文件数
    local dirs=$(echo "$all" | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn)

    # 提取关键目录（取前3个）
    local top_dirs=$(echo "$dirs" | head -3 | awk '{
        d=$2; gsub(/^\.$/, "根目录", d);
        printf "%s(%s个文件) ", d, $1
    }')

    # 统计文件类型
    local added=$(echo "$new" | grep -c . 2>/dev/null || echo 0)
    local modified=$(echo "$changed" | grep -c . 2>/dev/null || echo 0)
    local deleted=$(git diff --name-only --diff-filter=D HEAD 2>/dev/null | grep -c . 2>/dev/null || echo 0)

    # 生成摘要
    local parts=""
    [ "$added" -gt 0 ] && parts="${parts}新增${added}个文件"
    [ "$modified" -gt 0 ] && parts="${parts}${parts:+、}修改${modified}个文件"
    [ "$deleted" -gt 0 ] && parts="${parts}${parts:+、}删除${deleted}个文件"

    # 提取关键文件名作为上下文
    local key_files=$(echo "$all" | grep -vE '(^\.|AGENTS\.md|package-lock|uv\.lock)' | head -5 | sed 's|.*/||' | tr '\n' ' ' | sed 's/ $//')

    if [ -n "$parts" ]; then
        out="${parts}"
        [ -n "$key_files" ] && out="${out}（涉及: ${key_files}）"
    elif [ -n "$key_files" ]; then
        out="更新 ${key_files}"
    else
        out="更新代码"
    fi

    echo "$out"
}

AUTO_DESC=$(auto_summary)

# ---- 6. 输入描述 ----
DESC="${1:-}"
if [ -z "$DESC" ]; then
    echo -e "${YELLOW}📝 自动生成的描述:${NC}"
    echo -e "   ${CYAN}${AUTO_DESC}${NC}"
    echo ""
    read -p "   回车确认 / 输入新描述: " DESC
    if [ -z "$DESC" ]; then
        DESC="$AUTO_DESC"
    fi
fi

if [ -z "$DESC" ]; then
    echo -e "${RED}❌ 描述不能为空${NC}"
    exit 1
fi

# ---- 6. 构建 commit message ----
COMMIT_MSG="${TYPE}: ${DESC}"

echo ""
echo -e "${CYAN}──────────────────────────────────────${NC}"
echo -e "  分支:   ${GREEN}$BRANCH${NC}"
echo -e "  类型:   ${GREEN}$TYPE${NC}"
echo -e "  描述:   ${GREEN}$DESC${NC}"
echo -e "  Commit: ${GREEN}$COMMIT_MSG${NC}"
echo -e "${CYAN}──────────────────────────────────────${NC}"
echo ""

read -p "🚀 确认提交并推送? [Y/n] " CONFIRM
if [ "$CONFIRM" = "n" ] || [ "$CONFIRM" = "N" ]; then
    echo -e "${YELLOW}已取消${NC}"
    exit 0
fi

# ---- 7. Stage & Commit ----
echo ""
echo -e "${YELLOW}📦 暂存所有变更...${NC}"
git add -A

echo -e "${YELLOW}💾 提交...${NC}"
git commit -m "$COMMIT_MSG"

echo -e "${YELLOW}🚀 推送到 GitHub...${NC}"
if git push github "$BRANCH" 2>&1; then
    echo ""
    echo -e "${GREEN}══════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ 完成!${NC}"
    echo -e "${GREEN}  $COMMIT_MSG${NC}"
    echo -e "${GREEN}══════════════════════════════════════${NC}"
else
    echo ""
    echo -e "${RED}❌ 推送失败。提交已保存在本地。${NC}"
    echo -e "${YELLOW}   手动推送: git push github $BRANCH${NC}"
    exit 1
fi
