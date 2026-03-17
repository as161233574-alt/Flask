#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# 服务器首次初始化 / 手动部署脚本
# 使用方式：
#   1. 将此脚本上传到服务器
#   2. chmod +x deploy.sh && ./deploy.sh
# ─────────────────────────────────────────────────────────
set -euo pipefail

DEPLOY_DIR="/opt/flask-user-system"
REPO_URL="${REPO_URL:-}"          # 可选：自动 git clone
GHCR_OWNER="${GHCR_OWNER:-}"     # GitHub 用户名（小写）

echo "==> [1/5] 检查 Docker 环境"
docker --version
docker compose version

echo "==> [2/5] 准备部署目录"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# 如果提供了仓库地址则克隆/更新代码（用于获取 docker-compose.prod.yml 和 .env）
if [ -n "$REPO_URL" ]; then
  if [ -d ".git" ]; then
    git pull
  else
    git clone "$REPO_URL" .
  fi
fi

echo "==> [3/5] 检查 .env 文件"
if [ ! -f ".env" ]; then
  echo "ERROR: 缺少 .env 文件，请创建后重试"
  echo "参考内容："
  cat <<'EOF'
FLASK_ENV=production
SECRET_KEY=<随机生成的强密钥>
JWT_SECRET_KEY=<随机生成的强密钥>
DATABASE_URL=sqlite:////app/data/users.db
GHCR_OWNER=<你的 GitHub 用户名（小写）>
EOF
  exit 1
fi

# 注入 GHCR_OWNER 到环境（docker compose 会读取）
export GHCR_OWNER="${GHCR_OWNER:-$(grep GHCR_OWNER .env | cut -d= -f2)}"

echo "==> [4/5] 拉取最新镜像并启动"
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans
docker image prune -f

echo "==> [5/5] 检查服务健康状态"
sleep 5
curl -sf http://localhost:8000/health && echo " ✓ 服务正常运行" || echo " ✗ 健康检查失败，请查看日志：docker compose -f docker-compose.prod.yml logs"
