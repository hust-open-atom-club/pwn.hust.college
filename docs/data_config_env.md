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
```

## pwn.hust.college 平台 KOOK 配置说明

平台在 `config.env` 文件中保存了核心运行配置，其中包括与 **KOOK 机器人服务** 对接的参数。这部分内容将详细说明 KOOK 相关字段的含义、用途及获取方式。

---

## 字段与用途对照表

| 字段名                         | 类型       | 用途说明                                              |
| ------------------------------ | ---------- | ----------------------------------------------------- |
| `KOOK_GUILD_ID`                | 服务器 ID  | 指定 KOOK 服务器（Guild），即机器人运行的目标服务器。 |
| `KOOK_CHANNEL_ID_AWARD`        | 频道 ID    | 授勋频道，机器人在此推送完成道馆后的奖励消息。        |
| `KOOK_CHANNEL_ID_WELCOME`      | 频道 ID    | 欢迎频道，机器人在此发送新成员加入欢迎信息。          |
| `KOOK_CHANNEL_ID_NOTIFICATION` | 频道 ID    | 通知频道，预留字段，目前暂未启用。                    |
| `KOOK_APP_ID`                  | 应用 ID    | 标识 KOOK 应用，是 API 调用和机器人开发的基础。       |
| `KOOK_TOKEN`                   | 机器人密钥 | 机器人连接 KOOK 服务器所需的身份凭证。                |
| `KOOK_CLIENT_ID`               | OAuth 参数 | OAuth2 授权的客户端 ID。                              |
| `KOOK_CLIENT_SECRET`           | OAuth 参数 | OAuth2 授权的客户端密钥。                             |

---

## 配置字段说明

### `KOOK_GUILD_ID`

* **说明**：KOOK 服务器（Guild）的唯一标识符。
* **用途**：指明机器人运行的目标服务器。
* **当前配置**：`KOOK_GUILD_ID="7617016560630459"`

---

### `KOOK_CHANNEL_ID_AWARD`

* **说明**：授勋频道的 ID。
* **用途**：当用户完成一个完整道馆时，机器人会在此频道发送庆祝信息并授予徽章。
* **当前配置**：`KOOK_CHANNEL_ID_AWARD="1076014908789177"`
* **位置**：位于 KOOK 服务器 **“道馆”** 分组下的 **“徽章授予”** 频道。

---

### `KOOK_CHANNEL_ID_WELCOME`

* **说明**：欢迎频道的 ID。
* **用途**：当新成员加入 KOOK 服务器时，机器人会在此频道发送欢迎信息。
* **当前配置**：`KOOK_CHANNEL_ID_WELCOME="3433368715926516"`
* **位置**：位于 KOOK 服务器 **“道馆”** 分组下的 **“新手区”** 频道。

---

### `KOOK_CHANNEL_ID_NOTIFICATION`

* **说明**：通知频道的 ID。
* **用途**：作为预留字段，目前暂未启用。
* **当前配置**：`KOOK_CHANNEL_ID_NOTIFICATION="5298166608038709"`

---

### `KOOK_APP_ID`

* **说明**：机器人应用的 ID。
* **用途**：KOOK 开放平台为应用分配的唯一标识，用于 API 调用和机器人绑定。
* **当前配置**：`KOOK_APP_ID="30520"`

---

### `KOOK_TOKEN`

* **说明**：机器人连接 KOOK 所需的 **密钥**。
* **用途**：用于身份验证，保证机器人能正常接入服务器。
* **当前配置**：`KOOK_TOKEN=""`（需在部署时填入实际值）。
* **备注**：在本平台中，该 Token 对应 `pwn.hust.college` 机器人。

---

### `KOOK_CLIENT_ID`

* **说明**：KOOK **OAuth2 客户端 ID**。
* **用途**：用于 OAuth2 授权流程，标识平台对应的 KOOK 应用。
* **当前配置**：`KOOK_CLIENT_ID=""`（需在部署时填入实际值）

---

### `KOOK_CLIENT_SECRET`

* **说明**：KOOK **OAuth2 客户端密钥**。
* **用途**：与 `KOOK_CLIENT_ID` 配合使用，完成 OAuth2 授权。
* **当前配置**：`KOOK_CLIENT_SECRET=""`（需在部署时填入实际值）

---

## KOOK 字段获取与配置

KOOK 配置字段的获取方式大致分为两类：

* **服务器与频道相关字段**（Guild ID、Channel ID）
* **应用与机器人相关字段**（App ID、Token、OAuth2 参数）

### 1. 获取服务器与频道 ID

涉及字段：`KOOK_GUILD_ID`、`KOOK_CHANNEL_ID_AWARD`、`KOOK_CHANNEL_ID_WELCOME`

#### 1.1 获取用户 ID

1. 开启开发者模式：

   * 点击界面左下角头像 → **用户设置**
   * 在左侧菜单底部找到 **高级设置** → 打开 **开发者模式**。
2. 复制用户 ID：

   * 在任意聊天界面，右键目标用户头像 → **复制 ID**。
   * 获取的 ID 为纯数字，可用于 `<@用户ID>` 格式提及。

#### 1.2 获取频道 ID

1. 右键频道名称 → **复制 ID**，即可获得频道 ID。
2. 若需查看服务器 ID：点击服务器名称旁的齿轮 → **服务器设置** → **基础信息** → **服务器 ID**。

   * 服务器 ID 用于唯一标识整个 KOOK 社群实例。

---

### 2. 获取应用与机器人参数

涉及字段：`KOOK_APP_ID`、`KOOK_TOKEN`

#### 2.1 App ID 的作用

* 应用身份标识：App ID 是 KOOK 平台分配的唯一代码，相当于应用的“身份证”。
* API 调用基础：调用 KOOK 接口时需结合 App ID、App Secret、Token 进行身份验证。
* 机器人开发必需：开发 KOOK 机器人需先获取 App ID，再绑定机器人并生成 Token。

#### 2.2 获取 App ID 的步骤

1. 访问 KOOK 开放平台 <https://developer.kookapp.cn>，登录 KOOK 账号并完成实名认证。
2. 进入 **应用管理** → **新建应用**，填写名称、描述和使用场景。
3. 系统生成 App ID（即 Client ID）和 App Secret。
4. 如需开发机器人，在 **机器人** 页面创建机器人并获取专属 Token，App ID 会自动绑定该机器人。

---

### 3. OAuth2 相关参数

涉及字段：`KOOK_CLIENT_ID`、`KOOK_CLIENT_SECRET`

#### 3.1 字段说明

* `KOOK_CLIENT_ID`：OAuth 客户端 ID。
* `KOOK_CLIENT_SECRET`：OAuth 客户端密钥，用于鉴权。

#### 3.2 Access Token 获取流程

1. 在 KOOK 开放平台 **应用管理 → OAuth2** 页面配置授权回调地址（redirect\_uri）
2. 平台使用 Client ID 构造授权 URL，引导用户跳转至 KOOK 授权页面。
3. 用户授权后，KOOK 回调 redirect\_uri 并返回授权码。
4. 平台使用授权码、Client ID、Client Secret 向 KOOK 服务器交换 Access Token。

Access Token 为临时凭证，常用于用户登录和数据访问。

---

## pwn.hust.college 平台 Discord 配置说明

平台在 `config.env` 文件中保存了核心运行配置，其中包括与 **Discord 机器人服务** 对接的参数。这部分内容将详细说明 Discord 相关字段的含义、用途及获取方式。

---

## 字段与用途对照表

| 字段名                            | 类型       | 用途说明                                              |
| --------------------------------- | ---------- | ----------------------------------------------------- |
| `DISCORD_GUILD_ID`                | 服务器 ID  | 指定 Discord 服务器（Guild），即机器人运行的目标服务器。 |
| `DISCORD_CHANNEL_ID_AWARD`        | 频道 ID    | 授勋频道，机器人在此推送完成道馆后的奖励消息。        |
| `DISCORD_CHANNEL_ID_WELCOME`      | 频道 ID    | 欢迎频道，机器人在此发送新成员加入欢迎信息。          |
| `DISCORD_CHANNEL_ID_NOTIFICATION` | 频道 ID    | 通知频道，用于发送系统通知消息。                      |
| `DISCORD_CLIENT_ID`               | OAuth 参数 | OAuth2 授权的客户端 ID。                              |
| `DISCORD_CLIENT_SECRET`           | OAuth 参数 | OAuth2 授权的客户端密钥。                             |
| `DISCORD_BOT_TOKEN`               | 机器人令牌 | 机器人连接 Discord 服务器所需的身份凭证。                |

---

## 配置字段说明

### `DISCORD_GUILD_ID`

* **说明**：Discord 服务器（Guild）的唯一标识符。
* **用途**：指明机器人运行的目标服务器。
* **获取方式**：在 Discord 开发者模式下，右键服务器名称 → **复制服务器 ID**。

---

### `DISCORD_CHANNEL_ID_AWARD`

* **说明**：授勋频道的 ID。
* **用途**：当用户完成一个完整道馆时，机器人会在此频道发送庆祝信息并授予徽章。
* **获取方式**：在 Discord 开发者模式下，右键频道名称 → **复制频道 ID**。

---

### `DISCORD_CHANNEL_ID_WELCOME`

* **说明**：欢迎频道的 ID。
* **用途**：当新成员绑定 Discord 账号时，机器人会在此频道发送欢迎信息。
* **获取方式**：在 Discord 开发者模式下，右键频道名称 → **复制频道 ID**。

---

### `DISCORD_CHANNEL_ID_NOTIFICATION`

* **说明**：通知频道的 ID。
* **用途**：用于发送系统通知消息。
* **获取方式**：在 Discord 开发者模式下，右键频道名称 → **复制频道 ID**。

---

### `DISCORD_CLIENT_ID`

* **说明**：Discord **OAuth2 客户端 ID**。
* **用途**：用于 OAuth2 授权流程，标识平台对应的 Discord 应用。
* **获取方式**：在 Discord 开发者门户创建应用后，在 **OAuth2** 页面获取 Client ID。
* **当前配置**：`DISCORD_CLIENT_ID=""`（需在部署时填入实际值）

---

### `DISCORD_CLIENT_SECRET`

* **说明**：Discord **OAuth2 客户端密钥**。
* **用途**：与 `DISCORD_CLIENT_ID` 配合使用，完成 OAuth2 授权。
* **获取方式**：在 Discord 开发者门户的 **OAuth2** 页面获取 Client Secret。
* **当前配置**：`DISCORD_CLIENT_SECRET=""`（需在部署时填入实际值）

---

### `DISCORD_BOT_TOKEN`

* **说明**：机器人连接 Discord 所需的 **令牌（Token）**。
* **用途**：用于身份验证，保证机器人能正常接入服务器并执行操作（如发送消息、添加角色等）。
* **获取方式**：在 Discord 开发者门户创建机器人后，在 **Bot** 页面生成 Token。
* **当前配置**：`DISCORD_BOT_TOKEN=""`（需在部署时填入实际值）
* **备注**：Token 需要妥善保管，泄露后应立即重置。

---

## Discord 字段获取与配置

Discord 配置字段的获取方式大致分为两类：

* **服务器与频道相关字段**（Guild ID、Channel ID）
* **应用与机器人相关字段**（Client ID、Client Secret、Bot Token）

### 1. 获取服务器与频道 ID

涉及字段：`DISCORD_GUILD_ID`、`DISCORD_CHANNEL_ID_AWARD`、`DISCORD_CHANNEL_ID_WELCOME`、`DISCORD_CHANNEL_ID_NOTIFICATION`

#### 1.1 开启开发者模式

1. 打开 Discord 客户端，进入 **用户设置**（点击左下角齿轮图标）
2. 在左侧菜单中找到 **高级** → 开启 **开发者模式**

#### 1.2 获取服务器 ID

1. 右键点击服务器名称（或服务器图标）
2. 选择 **复制服务器 ID**，即可获得服务器 ID

#### 1.3 获取频道 ID

1. 右键点击频道名称
2. 选择 **复制频道 ID**，即可获得频道 ID

---

### 2. 获取应用与机器人参数

涉及字段：`DISCORD_CLIENT_ID`、`DISCORD_CLIENT_SECRET`、`DISCORD_BOT_TOKEN`

#### 2.1 创建 Discord 应用

1. 访问 Discord 开发者门户 <https://discord.com/developers/applications>，登录 Discord 账号
2. 点击右上角 **New Application**，填写应用名称
3. 创建完成后，进入应用管理页面

#### 2.2 获取 OAuth2 参数

1. 在应用管理页面，进入左侧菜单 **OAuth2** → **General**
2. 在 **Client Information** 部分可以看到：
   * **CLIENT ID**：即 `DISCORD_CLIENT_ID`
   * **CLIENT SECRET**：点击 **Reset Secret** 可生成新的 Client Secret，即 `DISCORD_CLIENT_SECRET`
3. 在 **Redirects** 部分添加授权回调地址（redirect_uri），例如：`https://your-domain.com/discord/redirect`

#### 2.3 创建机器人并获取 Token

1. 在应用管理页面，进入左侧菜单 **Bot**
2. 点击 **Add Bot** 创建机器人
3. 在 **TOKEN** 部分，点击 **Reset Token** 生成 Bot Token，即 `DISCORD_BOT_TOKEN`
4. 在 **Privileged Gateway Intents** 部分，根据需要开启以下权限（如需要）：
   * **SERVER MEMBERS INTENT**：用于获取服务器成员信息
   * **MESSAGE CONTENT INTENT**：用于读取消息内容

#### 2.4 邀请机器人到服务器

1. 在应用管理页面，进入左侧菜单 **OAuth2** → **URL Generator**
2. 在 **SCOPES** 部分勾选：
   * **bot**：机器人权限
   * **identify**：用户身份识别（用于 OAuth2）
3. 在 **BOT PERMISSIONS** 部分勾选所需权限：
   * **Send Messages**：发送消息
   * **Read Message History**：读取消息历史
   * **Manage Roles**：管理角色（用于自动添加角色）
   * **Use External Emojis**：使用外部表情符号
4. 复制生成的 URL，在浏览器中打开并选择要邀请机器人的服务器
5. 确保机器人拥有足够的权限访问目标频道

---

### 3. OAuth2 授权流程

涉及字段：`DISCORD_CLIENT_ID`、`DISCORD_CLIENT_SECRET`

#### 3.1 字段说明

* `DISCORD_CLIENT_ID`：OAuth 客户端 ID，用于标识应用
* `DISCORD_CLIENT_SECRET`：OAuth 客户端密钥，用于鉴权

#### 3.2 Access Token 获取流程

1. 在 Discord 开发者门户 **OAuth2 → General** 页面配置授权回调地址（redirect_uri）
2. 平台使用 Client ID 构造授权 URL，引导用户跳转至 Discord 授权页面
3. 用户授权后，Discord 回调 redirect_uri 并返回授权码（code）
4. 平台使用授权码、Client ID、Client Secret 向 Discord 服务器交换 Access Token
5. 使用 Access Token 获取用户的 Discord ID，完成账号绑定

Access Token 为临时凭证，常用于用户登录和数据访问。
