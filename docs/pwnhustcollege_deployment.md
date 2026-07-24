# pwn.hust.college 部署

## 概述

本文档介绍 pwn.hust.college 的 HUST 特定部署流程。常规 pwn.college 部署步骤见 `general_deployment.md`，本文档聚焦华科镜像源、SSO 统一身份认证、KOOK/Discord 集成、AI 助教和监控栈等 HUST 特有组件的配置。

## 前置条件

- 一台运行 Linux 的服务器（推荐 Ubuntu 22.04）
- 域名（如 `pwn.cse.hust.edu.cn`），DNS 已正确指向服务器 IP
- 磁盘空间：`challenge-full` 级别约需 70 GB
- Docker 环境

## 部署步骤

### 安装 Docker

使用华科镜像源安装 Docker CE：

```sh
export DOWNLOAD_URL="https://mirrors.hust.edu.cn/docker-ce"
curl -fsSL https://get.docker.com | /bin/sh
```

### 克隆仓库并构建

```sh
git clone https://github.com/hust-open-atom-club/pwn.hust.college.git
cd pwn.hust.college
docker build -t pwncollege/dojo .
```

构建过程中，Dockerfile 使用华科镜像源（`mirrors.hust.edu.cn`）替代 Ubuntu 默认源，从清华镜像源下载 Docker CE，从 Gitee 镜像获取默认 seccomp 配置。

### 启动 dojo 容器

```sh
docker run --privileged -d \
  -v "$(pwd):/opt/pwn.college:shared" \
  -p 22:22 -p 80:80 -p 443:443 \
  -e DOJO_HOST=pwn.cse.hust.edu.cn \
  -e DOJO_ENV=production \
  -e DOJO_CHALLENGE=challenge-full \
  --name dojo pwncollege/dojo
```

等待初始化完成：

```sh
docker exec dojo dojo wait
```

首次运行会构建挑战镜像，根据 `DOJO_CHALLENGE` 级别不同，可能耗时数十分钟到数小时。

### 修改管理员密码

登录后（默认 `admin`/`admin`），**必须立即修改管理员密码**。进入右上角设置 → 修改密码。

## HTTPS 证书

将证书文件放入 `pwncollege_certs` 命名卷：

```sh
# 查看卷的挂载路径
docker inspect pwncollege_certs

# 将证书文件复制到卷的挂载点
# 文件名格式：<DOJO_HOST>.crt 和 <DOJO_HOST>.key
# 例如：pwn.cse.hust.edu.cn.crt 和 pwn.cse.hust.edu.cn.key
```

nginx-proxy 和 acme-companion 会自动检测和加载证书。如果未提供证书，acme-companion 会尝试通过 Let's Encrypt 自动申请。

## SSO 统一身份认证配置

pwn.hust.college 集成华中科技大学统一身份认证系统（CAS 协议）。配置方式：

在 `data/config.env` 中设置：

```ini
ENABLE_SSO=True
CAS_SERVER_URL=https://pass.hust.edu.cn/cas/login
CAS_REDIRECT_URL=https://pwn.cse.hust.edu.cn/cas-login/
CAS_EMAIL_SUFFIX=@hust.edu.cn
CAS_VERSION=2
```

或在 `docker run` 时通过 `-e` 传入。设置后需重启 ctfd：

```sh
docker exec dojo dojo compose restart ctfd
```

启用后：
- 导航栏出现"统一身份认证"按钮，点击跳转到华科 CAS 登录页。
- 认证成功后自动注册用户（邮箱格式为 `学号@hust.edu.cn`）。
- 登录页显示 SSO 提示。

禁用时（`ENABLE_SSO=False` 或未设置），SSO 路由返回 501，用户使用 CTFd 自带登录。

## KOOK 机器人配置

平台支持 KOOK（原"开黑啦"）聊天平台的机器人集成，用于在用户完成道馆时发送奖励通知。

在 `data/config.env` 中配置以下字段：

| 字段 | 说明 |
|------|------|
| `KOOK_TOKEN` | 机器人连接密钥 |
| `KOOK_GUILD_ID` | 目标服务器 ID |
| `KOOK_CHANNEL_ID_AWARD` | 奖励通知频道 ID |
| `KOOK_CHANNEL_ID_WELCOME` | 欢迎频道 ID |
| `KOOK_CHANNEL_ID_NOTIFICATION` | 系统通知频道 ID |
| `KOOK_CLIENT_ID` | OAuth2 客户端 ID |
| `KOOK_CLIENT_SECRET` | OAuth2 客户端密钥 |
| `KOOK_APP_ID` | 应用 ID |

获取方式简述：
1. 访问 [KOOK 开放平台](https://developer.kookapp.cn) 创建应用，获取 App ID 和密钥。
2. 在应用管理中创建机器人，获取 Token。
3. 在 KOOK 客户端开启开发者模式后，右键服务器/频道 → 复制 ID。
4. 配置 OAuth2 回调地址为 `https://<域名>/kook/redirect`。

未配置时，KOOK 功能自动禁用，不影响平台其他功能。详细获取教程见 `data_config_env.md` 中 KOOK 配置章节。

## Discord 机器人配置

平台同样支持 Discord 机器人集成，功能与 KOOK 类似。

在 `data/config.env` 中配置以下字段：

| 字段 | 说明 |
|------|------|
| `DISCORD_BOT_TOKEN` | 机器人令牌 |
| `DISCORD_GUILD_ID` | 目标服务器 ID |
| `DISCORD_CHANNEL_ID_AWARD` | 奖励通知频道 ID |
| `DISCORD_CHANNEL_ID_WELCOME` | 欢迎频道 ID |
| `DISCORD_CHANNEL_ID_NOTIFICATION` | 系统通知频道 ID |
| `DISCORD_CLIENT_ID` | OAuth2 客户端 ID |
| `DISCORD_CLIENT_SECRET` | OAuth2 客户端密钥 |

获取方式简述：
1. 访问 [Discord 开发者门户](https://discord.com/developers/applications) 创建应用。
2. 在 Bot 页面创建机器人并获取 Token。
3. 在 Discord 客户端开启开发者模式后，右键服务器/频道 → 复制 ID。
4. 通过 OAuth2 URL Generator 生成邀请链接，将机器人添加到服务器。
5. 配置 OAuth2 回调地址为 `https://<域名>/discord/redirect`。

未配置时，Discord 功能自动禁用。详细获取教程见 `data_config_env.md` 中 Discord 配置章节。

## AI 助教（sensai）配置

平台集成基于 Open WebUI 的 AI 助教，需配置后端 LLM 服务：

在 `data/config.env` 中设置：

```ini
OLLAMA_BASE_URLS=http://ollama-server:11434
OPENAI_API_BASE_URL=https://api.openai.com/v1
```

支持 Ollama 和 OpenAI 兼容 API 两种后端。配置后，学生在挑战页面的"帮助"选项卡中可与 AI 交互。

## Prometheus / Grafana 监控配置

监控栈默认随 docker compose 启动。访问方式：

- Prometheus：`http://<域名>:9090`
- Grafana：`http://<域名>/monitoring/`（通过 nginx 子路径代理）

Grafana 默认管理员密码为 `admin`（可通过 `GF_SECURITY_ADMIN_PASSWORD` 环境变量修改）。

监控组件包括：
- 系统资源（node-exporter）
- 数据库（mysql-exporter）
- 缓存（redis-exporter）
- Web 服务器（nginx-exporter）
- 自定义应用指标（`/metrics` 端点）

配置文件位置：
- `monitoring/prometheus/prometheus.yml`：采集目标与规则
- `monitoring/grafana/provisioning/`：Grafana 数据源与仪表盘

## 备份与恢复

平台提供自动备份和手动备份两种方式。

自动备份：systemd timer 每小时执行一次，备份文件存储在 `data/backups/`。

手动备份：

```sh
docker exec dojo dojo backup
```

恢复：

```sh
docker exec dojo dojo restore <备份文件名>
```

备份文件为 gzip 压缩的 SQL dump，包含完整的数据库结构和数据。

## 更新

在生产环境中更新平台：

```sh
docker kill dojo
docker rm dojo
git pull
docker build -t pwncollege/dojo .
docker run --privileged -d \
  -v "$(pwd):/opt/pwn.college:shared" \
  -p 22:22 -p 80:80 -p 443:443 \
  --name dojo pwncollege/dojo
```

此方式会导致服务中断。若仅更新插件或主题代码（不涉及 ctfd 或 challenge 修改），可在 dojo 容器内使用 `dojo sync` 热更新，无需重启容器。

注意：`dojo update` 命令（`git pull + sync + compose up --build`）仅在完全理解每个提交的变更时使用。
