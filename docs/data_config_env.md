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

## pwn.hust.college 平台 KOOK 配置说明

平台在 `config.env` 文件中保存了核心运行配置，其中包括与 **KOOK 机器人服务** 对接的参数。这部分内容将详细说明 KOOK 相关字段的含义、用途及获取方式。

---

### 字段与用途对照表

| 字段名 | 类型 | 用途说明 |
| ------ | ---- | -------- |
| `KOOK_GUILD_ID` | 服务器 ID | 指定 KOOK 服务器（Guild），即机器人运行的目标服务器。 |
| `KOOK_CHANNEL_ID_AWARD` | 频道 ID | 授勋频道，机器人在此推送完成道馆后的奖励消息。 |
| `KOOK_CHANNEL_ID_WELCOME` | 频道 ID | 欢迎频道，机器人在此发送新成员加入欢迎信息。 |
| `KOOK_CHANNEL_ID_NOTIFICATION` | 频道 ID | 通知频道，预留字段，目前暂未启用。 |
| `KOOK_APP_ID` | 应用 ID | 标识 KOOK 应用，是 API 调用和机器人开发的基础。 |
| `KOOK_TOKEN` | 机器人密钥 | 机器人连接 KOOK 服务器所需的身份凭证。 |
| `KOOK_CLIENT_ID` | OAuth 参数 | OAuth2 授权的客户端 ID。 |
| `KOOK_CLIENT_SECRET` | OAuth 参数 | OAuth2 授权的客户端密钥。 |

---

### 配置字段说明

#### `KOOK_GUILD_ID`

- **说明**：KOOK 服务器（Guild）的唯一标识符。
- **用途**：指明机器人运行的目标服务器。

#### `KOOK_CHANNEL_ID_AWARD`

- **说明**：授勋频道的 ID。
- **用途**：当用户完成一个完整道馆时，机器人会在此频道发送庆祝信息并授予徽章。
- **位置**：位于 KOOK 服务器 **"道馆"** 分组下的 **"徽章授予"** 频道。

#### `KOOK_CHANNEL_ID_WELCOME`

- **说明**：欢迎频道的 ID。
- **用途**：当新成员加入 KOOK 服务器时，机器人会在此频道发送欢迎信息。
- **位置**：位于 KOOK 服务器 **"道馆"** 分组下的 **"新手区"** 频道。

#### `KOOK_CHANNEL_ID_NOTIFICATION`

- **说明**：通知频道的 ID。
- **用途**：作为预留字段，目前暂未启用。

#### `KOOK_APP_ID`

- **说明**：机器人应用的 ID。
- **用途**：KOOK 开放平台为应用分配的唯一标识，用于 API 调用和机器人绑定。

#### `KOOK_TOKEN`

- **说明**：机器人连接 KOOK 所需的 **密钥**。
- **用途**：用于身份验证，保证机器人能正常接入服务器。
- **备注**：在本平台中，该 Token 对应 `pwn.hust.college` 机器人。

#### `KOOK_CLIENT_ID`

- **说明**：KOOK **OAuth2 客户端 ID**。
- **用途**：用于 OAuth2 授权流程，标识平台对应的 KOOK 应用。

#### `KOOK_CLIENT_SECRET`

- **说明**：KOOK **OAuth2 客户端密钥**。
- **用途**：与 `KOOK_CLIENT_ID` 配合使用，完成 OAuth2 授权。

---

### KOOK 字段获取与配置

KOOK 配置字段的获取方式大致分为两类：

- **服务器与频道相关字段**（Guild ID、Channel ID）
- **应用与机器人相关字段**（App ID、Token、OAuth2 参数）

#### 1. 获取服务器与频道 ID

涉及字段：`KOOK_GUILD_ID`、`KOOK_CHANNEL_ID_AWARD`、`KOOK_CHANNEL_ID_WELCOME`

1. 开启开发者模式：
   - 点击界面左下角头像 → **用户设置**
   - 在左侧菜单底部找到 **高级设置** → 打开 **开发者模式**。

2. 获取频道 ID：右键频道名称 → **复制 ID**，即可获得频道 ID。

3. 获取服务器 ID：点击服务器名称旁的齿轮 → **服务器设置** → **基础信息** → **服务器 ID**。

#### 2. 获取应用与机器人参数

涉及字段：`KOOK_APP_ID`、`KOOK_TOKEN`

1. 访问 KOOK 开放平台 <https://developer.kookapp.cn>，登录 KOOK 账号并完成实名认证。
2. 进入 **应用管理** → **新建应用**，填写名称、描述和使用场景。
3. 系统生成 App ID（即 Client ID）和 App Secret。
4. 如需开发机器人，在 **机器人** 页面创建机器人并获取专属 Token，App ID 会自动绑定该机器人。

#### 3. OAuth2 相关参数

涉及字段：`KOOK_CLIENT_ID`、`KOOK_CLIENT_SECRET`

1. 在 KOOK 开放平台 **应用管理 → OAuth2** 页面配置授权回调地址（redirect_uri），例如 `https://<域名>/kook/redirect`。
2. 平台使用 Client ID 构造授权 URL，引导用户跳转至 KOOK 授权页面。
3. 用户授权后，KOOK 回调 redirect_uri 并返回授权码。
4. 平台使用授权码、Client ID、Client Secret 向 KOOK 服务器交换 Access Token。

未配置 KOOK 凭据时，相关功能自动禁用。

---

## pwn.hust.college 平台 Discord 配置说明

平台在 `config.env` 文件中保存了核心运行配置，其中包括与 **Discord 机器人服务** 对接的参数。这部分内容将详细说明 Discord 相关字段的含义、用途及获取方式。

---

### 字段与用途对照表

| 字段名 | 类型 | 用途说明 |
| ------ | ---- | -------- |
| `DISCORD_GUILD_ID` | 服务器 ID | 指定 Discord 服务器（Guild），即机器人运行的目标服务器。 |
| `DISCORD_CHANNEL_ID_AWARD` | 频道 ID | 授勋频道，机器人在此推送完成道馆后的奖励消息。 |
| `DISCORD_CHANNEL_ID_WELCOME` | 频道 ID | 欢迎频道，机器人在此发送新成员加入欢迎信息。 |
| `DISCORD_CHANNEL_ID_NOTIFICATION` | 频道 ID | 通知频道，用于发送系统通知消息。 |
| `DISCORD_CLIENT_ID` | OAuth 参数 | OAuth2 授权的客户端 ID。 |
| `DISCORD_CLIENT_SECRET` | OAuth 参数 | OAuth2 授权的客户端密钥。 |
| `DISCORD_BOT_TOKEN` | 机器人令牌 | 机器人连接 Discord 服务器所需的身份凭证。 |

---

### 配置字段说明

#### `DISCORD_GUILD_ID`

- **说明**：Discord 服务器（Guild）的唯一标识符。
- **用途**：指明机器人运行的目标服务器。
- **获取方式**：在 Discord 开发者模式下，右键服务器名称 → **复制服务器 ID**。

#### `DISCORD_CHANNEL_ID_AWARD`

- **说明**：授勋频道的 ID。
- **用途**：当用户完成一个完整道馆时，机器人会在此频道发送庆祝信息并授予徽章。
- **获取方式**：在 Discord 开发者模式下，右键频道名称 → **复制频道 ID**。

#### `DISCORD_CHANNEL_ID_WELCOME`

- **说明**：欢迎频道的 ID。
- **用途**：当新成员绑定 Discord 账号时，机器人会在此频道发送欢迎信息。
- **获取方式**：在 Discord 开发者模式下，右键频道名称 → **复制频道 ID**。

#### `DISCORD_CHANNEL_ID_NOTIFICATION`

- **说明**：通知频道的 ID。
- **用途**：用于发送系统通知消息。
- **获取方式**：在 Discord 开发者模式下，右键频道名称 → **复制频道 ID**。

#### `DISCORD_CLIENT_ID`

- **说明**：Discord **OAuth2 客户端 ID**。
- **用途**：用于 OAuth2 授权流程，标识平台对应的 Discord 应用。
- **获取方式**：在 Discord 开发者门户创建应用后，在 **OAuth2** 页面获取 Client ID。

#### `DISCORD_CLIENT_SECRET`

- **说明**：Discord **OAuth2 客户端密钥**。
- **用途**：与 `DISCORD_CLIENT_ID` 配合使用，完成 OAuth2 授权。
- **获取方式**：在 Discord 开发者门户的 **OAuth2** 页面获取 Client Secret。

#### `DISCORD_BOT_TOKEN`

- **说明**：机器人连接 Discord 所需的 **令牌（Token）**。
- **用途**：用于身份验证，保证机器人能正常接入服务器并执行操作（如发送消息、添加角色等）。
- **获取方式**：在 Discord 开发者门户创建机器人后，在 **Bot** 页面生成 Token。
- **备注**：Token 需要妥善保管，泄露后应立即重置。

---

### Discord 字段获取与配置

Discord 配置字段的获取方式大致分为两类：

- **服务器与频道相关字段**（Guild ID、Channel ID）
- **应用与机器人相关字段**（Client ID、Client Secret、Bot Token）

#### 1. 获取服务器与频道 ID

涉及字段：`DISCORD_GUILD_ID`、`DISCORD_CHANNEL_ID_AWARD`、`DISCORD_CHANNEL_ID_WELCOME`、`DISCORD_CHANNEL_ID_NOTIFICATION`

1. 打开 Discord 客户端，进入 **用户设置**（点击左下角齿轮图标）
2. 在左侧菜单中找到 **高级** → 开启 **开发者模式**
3. 右键点击服务器名称或频道名称 → **复制 ID**，即可获得对应 ID

#### 2. 获取应用与机器人参数

涉及字段：`DISCORD_CLIENT_ID`、`DISCORD_CLIENT_SECRET`、`DISCORD_BOT_TOKEN`

1. 访问 Discord 开发者门户 <https://discord.com/developers/applications>，登录 Discord 账号
2. 点击右上角 **New Application**，填写应用名称
3. 在 **OAuth2 → General** 页面获取 **CLIENT ID** 和 **CLIENT SECRET**
4. 在 **Bot** 页面，点击 **Add Bot** 创建机器人，然后点击 **Reset Token** 生成 Bot Token
5. 在 **OAuth2 → URL Generator** 页面，勾选 `bot` 和 `identify` scopes，以及所需权限（Send Messages、Read Message History、Manage Roles 等），生成邀请链接将机器人添加到目标服务器
6. 在 **Redirects** 部分添加 OAuth2 回调地址，例如 `https://<域名>/discord/redirect`

#### 3. OAuth2 授权流程

1. 平台使用 Client ID 构造授权 URL，引导用户跳转至 Discord 授权页面
2. 用户授权后，Discord 回调 redirect_uri 并返回授权码（code）
3. 平台使用授权码、Client ID、Client Secret 向 Discord 服务器交换 Access Token
4. 使用 Access Token 获取用户的 Discord ID，完成账号绑定

未配置 Discord 凭据时，相关功能自动禁用。
