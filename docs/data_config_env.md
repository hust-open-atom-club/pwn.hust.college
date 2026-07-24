# `config.env` 文件说明

`config.env` 是 **pwn.hust.college 平台的核心配置文件**，位于路径：

```sh
data/config.env
```

若不存在，由 `dojo-init` 自动创建。该文件以 **环境变量键值对** 的形式，集中定义了平台的运行参数，用于控制整体运行环境和功能启用情况。例如：

* 平台运行环境（如 `production` 或 `development`）
* 系统依赖与工具安装选项
* 服务端口与访问主机配置
* 与外部服务（如 KOOK、OpenAI API）的对接参数

文件内容大致如下所示：

```ini
DOJO_HOST=pwn.cse.hust.edu.cn
DOJO_ENV=production
DOJO_CHALLENGE=challenge-full
SECRET_KEY=
DOCKER_PSLR=
UBUNTU_VERSION=22.04
INTERNET_FOR_ALL=False
ARCH=amd64
ENABLE_SSO=False
CAS_SERVER_URL=https://pass.hust.edu.cn/cas/login
CAS_REDIRECT_URL=
CAS_EMAIL_SUFFIX=@hust.edu.cn
CAS_VERSION=2
KOOK_TOKEN=""
KOOK_GUILD_ID=""
KOOK_CHANNEL_ID_AWARD=""
KOOK_CHANNEL_ID_WELCOME=""
KOOK_CHANNEL_ID_NOTIFICATION=""
KOOK_CLIENT_ID=""
KOOK_CLIENT_SECRET=""
KOOK_APP_ID=""
DISCORD_CLIENT_ID=""
DISCORD_CLIENT_SECRET=""
DISCORD_BOT_TOKEN=""
DISCORD_GUILD_ID=""
DISCORD_CHANNEL_ID_AWARD=""
DISCORD_CHANNEL_ID_WELCOME=""
DISCORD_CHANNEL_ID_NOTIFICATION=""
OPENAI_API_BASE_URL=""
OLLAMA_BASE_URLS=""
```

## 核心配置字段

| 字段名 | 类型 | 用途说明 |
| ------ | ---- | -------- |
| `DOJO_HOST` | 域名 | 服务监听的域名（如 `pwn.cse.hust.edu.cn`）。**必需**。 |
| `DOJO_ENV` | 字符串 | 运行环境。`development` 使用 Flask 开发服务器，其他值使用 gunicorn。 |
| `DOJO_CHALLENGE` | 字符串 | 挑战镜像级别：`challenge-nano` / `micro` / `mini` / `full`。默认 `challenge-mini`。 |
| `SECRET_KEY` | 字符串 | HMAC 密钥，用于 flag 签名。由 `dojo-init` 自动生成，丢失会使所有用户 flag 失效。 |
| `DOCKER_PSLR` | 字符串 | Docker TLS 密钥，由 `dojo-init` 自动生成。 |
| `UBUNTU_VERSION` | 字符串 | 挑战镜像的 Ubuntu 版本。默认 `22.04`。 |
| `INTERNET_FOR_ALL` | 布尔值 | 是否允许用户容器访问外网。默认 `False`。 |
| `ARCH` | 字符串 | 硬件架构。`amd64` 或 `arm64`，由 `dojo-init` 自动检测。 |
| `HOST_DATA_PATH` | 路径 | 宿主机数据目录路径。**必需**。 |

## SSO 统一身份认证配置

| 字段名 | 类型 | 用途说明 |
| ------ | ---- | -------- |
| `ENABLE_SSO` | 布尔值 | 是否启用华科统一身份认证。默认 `False`。 |
| `CAS_SERVER_URL` | URL | CAS 服务器地址。默认 `https://pass.hust.edu.cn/cas/login`。 |
| `CAS_REDIRECT_URL` | URL | CAS 登录回调地址。需设置为 `https://<域名>/cas-login/`。 |
| `CAS_EMAIL_SUFFIX` | 字符串 | 自动注册用户的邮箱后缀。默认 `@hust.edu.cn`。 |
| `CAS_VERSION` | 字符串 | CAS 协议版本。默认 `2`。 |

启用后，用户可通过导航栏"统一身份认证"按钮登录，首次登录自动创建账户。禁用时（默认），SSO 路由返回 501。

## AI 助教（sensai）配置

| 字段名 | 类型 | 用途说明 |
| ------ | ---- | -------- |
| `OLLAMA_BASE_URLS` | URL | Ollama 服务地址列表。 |
| `OPENAI_API_BASE_URL` | URL | OpenAI 兼容 API 地址。 |

配置后，学生在挑战页面点击"帮助"可与 AI 交互。未配置时 sensai 功能自动禁用。

## 工具安装选项

以下选项控制挑战镜像中预装工具的包含与否，默认值由 `DEFAULT_INSTALL_SELECTION` 决定。均取值为 `yes` 或 `no`：

`INSTALL_GDB`、`INSTALL_GHIDRA`、`INSTALL_RADARE2`、`INSTALL_KERNEL`、`INSTALL_DESKTOP`、`INSTALL_AFL`、`INSTALL_ANGR_MANAGEMENT`、`INSTALL_BUSYBOX`、`INSTALL_CAPSTONE`、`INSTALL_GECKODRIVER`、`INSTALL_GLOW`、`INSTALL_IDA_FREE`、`INSTALL_BINJA_FREE`、`INSTALL_RAPPEL`、`INSTALL_RP`、`INSTALL_TCPDUMP`、`INSTALL_TOOLS_APT`、`INSTALL_TOOLS_PIP`、`INSTALL_VIRTIOFSD`

其中 `INSTALL_DESKTOP` 默认为 `yes`，其余默认为 `no`。

## KOOK 配置

平台支持 KOOK 机器人集成，在 `config.env` 中配置以下字段：

| 字段名 | 类型 | 用途说明 |
| ------ | ---- | -------- |
| `KOOK_GUILD_ID` | 服务器 ID | 机器人运行的目标服务器。 |
| `KOOK_CHANNEL_ID_AWARD` | 频道 ID | 授勋频道，用户完成道馆后推送奖励消息。 |
| `KOOK_CHANNEL_ID_WELCOME` | 频道 ID | 欢迎频道，新成员加入时发送欢迎信息。 |
| `KOOK_CHANNEL_ID_NOTIFICATION` | 频道 ID | 通知频道，预留字段。 |
| `KOOK_APP_ID` | 应用 ID | KOOK 应用的唯一标识。 |
| `KOOK_TOKEN` | 机器人密钥 | 机器人连接 KOOK 服务器所需的身份凭证。 |
| `KOOK_CLIENT_ID` | OAuth 参数 | OAuth2 授权的客户端 ID。 |
| `KOOK_CLIENT_SECRET` | OAuth 参数 | OAuth2 授权的客户端密钥。 |

### 获取方式

服务器和频道 ID：在 KOOK 客户端开启开发者模式（设置 → 高级设置 → 开发者模式）后，右键服务器/频道 → 复制 ID。

应用与机器人参数：访问 [KOOK 开放平台](https://developer.kookapp.cn)，创建应用后获取 App ID 和 App Secret。在应用管理 → 机器人页面创建机器人并获取 Token。

OAuth2 参数：在 KOOK 开放平台的应用管理 → OAuth2 页面获取 Client ID 和 Client Secret，配置回调地址为 `https://<域名>/kook/redirect`。

未配置 KOOK 凭据时，相关功能自动禁用。

## Discord 配置

平台支持 Discord 机器人集成，在 `config.env` 中配置以下字段：

| 字段名 | 类型 | 用途说明 |
| ------ | ---- | -------- |
| `DISCORD_GUILD_ID` | 服务器 ID | 机器人运行的目标服务器。 |
| `DISCORD_CHANNEL_ID_AWARD` | 频道 ID | 授勋频道，用户完成道馆后推送奖励消息。 |
| `DISCORD_CHANNEL_ID_WELCOME` | 频道 ID | 欢迎频道，新成员绑定时发送欢迎信息。 |
| `DISCORD_CHANNEL_ID_NOTIFICATION` | 频道 ID | 通知频道，用于发送系统通知。 |
| `DISCORD_CLIENT_ID` | OAuth 参数 | OAuth2 授权的客户端 ID。 |
| `DISCORD_CLIENT_SECRET` | OAuth 参数 | OAuth2 授权的客户端密钥。 |
| `DISCORD_BOT_TOKEN` | 机器人令牌 | 机器人连接 Discord 服务器所需的身份凭证。 |

### 获取方式

服务器和频道 ID：在 Discord 客户端开启开发者模式（设置 → 高级 → 开发者模式）后，右键服务器/频道 → 复制 ID。

应用与机器人参数：访问 [Discord 开发者门户](https://discord.com/developers/applications)，创建应用后在 OAuth2 → General 页面获取 Client ID 和 Client Secret。在 Bot 页面创建机器人并获取 Token。在 OAuth2 → URL Generator 生成邀请链接，将机器人添加到目标服务器。

OAuth2 回调地址配置为 `https://<域名>/discord/redirect`。

未配置 Discord 凭据时，相关功能自动禁用。
