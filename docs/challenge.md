# Challenge

## 挑战环境概述

平台挑战运行在独立 Docker 容器中，核心安全模型为：

- 用户以 `hacker` 身份运行（UID 1000）。
- `/flag` 文件仅 **root**（UID 0）可读。
- 挑战程序在 `/challenge/` 目录下，作为 root 拥有的 **setuid 二进制文件**运行，因此能够读取 `/flag`。
- 学习者需通过漏洞利用或满足挑战要求，使挑战程序输出 `/flag` 的内容。

每次解题获得的 flag 是**按用户和挑战独立签发**的（HMAC 签名），不存在静态 flag 表。不同用户在同一挑战中获得的 flag 不同，这有效防止了 flag 共享。

## 道馆与挑战结构

平台采用道馆（Dojo）→ 模块（Module）→ 挑战（Challenge）的三层结构。道馆通过 Git 仓库管理，每个道馆仓库根目录包含一个 `dojo.yml` 定义文件。

### Dojo 定义

`Dojo` 是道馆的顶层对象，包含以下属性：

- `id`：**必需**。Dojo 的唯一标识符。
- `name`：**必需**。Dojo 的显示名称。
- `type`：**可选**。取值 `welcome`（入门篇）、`elementary`（初级篇）、`intermediate`（中级篇）、`advanced`（高级篇）、`course`（课程）、`topic`（主题）、`example`（示例）、`hidden`（隐藏）。省略或取其他值时显示在"更多"区域。
- `password`：**可选**。加入道馆需要的密码，省略则任何人可加入。
- `modules`：**必需**。模块对象数组。
- `award`：**可选**。子参数 `belt` 为绶带图片文件名，`emoji` 为徽章图片文件名。文件存放于 `dojo_theme/static/img/dojo/`。

### Module 定义

`modules` 数组中每个 `Module` 对象包含：

- `id`：**必需**。模块的唯一标识符。
- `name`：**必需**。模块的显示名称。
- `challenges`：**必需**。挑战对象数组。
- `resources`：**可选**。学习资源数组（视频/讲义）。
- `icon`：**可选**。模块图标文件名，存放于 `dojo_theme/static/img/dojo/`。

### Challenge 定义

`challenges` 数组中每个 `Challenge` 对象包含：

- `id`：**必需**。挑战的唯一标识符。
- `name`：**必需**。挑战的显示名称。
- `icon`：**可选**。挑战图标文件名。
- `level`：**可选**。挑战等级显示。

### 使用样例

```yaml
id: example-dojo
name: 示例道馆
type: example
award:
  belt: PokeBall
  emoji: PokeBall
modules:
- id: module-1
  name: 第一个模块
  icon: Pikachu
  challenges:
  - id: level-1
    name: 第一关
    level: 1
  resources:
  - name: 课程视频
    type: lecture
    video: "438064585"
    playlist: "BV1mj411M7NZ"
  - name: 补充说明
    type: markdown
    content: |
      这是补充的文本内容。
```

### Resources 类型

- `lecture`：视频资源。仅支持 bilibili，`video` 为 cid，`playlist` 为 BV 号，需配合使用。`slides` 可选，指向 PDF 文件名。
- `markdown`：文本内容，`content` 为 Markdown 格式文本。

## 挑战容器生命周期

1. 用户在道馆页面点击 **Start** 按钮，前端调用 `/pwncollege_api/v1/docker` API。
2. 后端创建挑战容器（`dojo_plugin/api/v1/docker.py::start_challenge()`）：
   - 设置 home 目录（从 `homes/homefs` 稀疏复制）。
   - 基于挑战镜像创建容器，挂载 home 目录，连接 `user_network`。
   - 插入挑战文件、签发 flag、初始化容器。
   - 如果是练习模式（practice），额外授予 sudo 权限并使用占位 flag。
3. 容器启动后，用户可通过 VSCode、桌面或 SSH 访问。
4. 容器运行 `sleep 6h`，**6 小时后自动停止**。
5. 用户可随时重新启动挑战（旧容器会被移除并重建）。

## 挑战镜像构建

挑战镜像由 `challenge/` 目录构建，采用多阶段 Docker 构建：

- 构建上下文：`challenge/`
- Dockerfile：`Dockerfile_amd64` 或 `Dockerfile_arm64`（由 `ARCH` 变量选择）
- 目标阶段：`challenge-final`
- 关键构建参数：`DOJO_CHALLENGE`、`UBUNTU_VERSION`、`INSTALL_*` 系列

镜像尺寸由 `DOJO_CHALLENGE` 变量控制：

| 级别 | 说明 |
|------|------|
| `challenge-nano` | 精简配置，仅基础工具 |
| `challenge-micro` | 在 nano 基础上增加 VSCode |
| `challenge-mini` | 在 micro 基础上增加精简桌面环境（默认） |
| `challenge-full` | 完整配置，约 70 GB，含 Ghidra、IDA Free、内核调试等全部工具 |

工具安装由 `INSTALL_*` 构建参数控制（如 `INSTALL_GDB`、`INSTALL_GHIDRA`、`INSTALL_RADARE2`、`INSTALL_KERNEL`、`INSTALL_DESKTOP` 等），默认值由 `DEFAULT_INSTALL_SELECTION` 决定，可按需在 `config.env` 中覆盖。

## 工作区访问方式

启动挑战后，用户可通过三种方式与挑战环境交互：

- **VSCode 工作空间**：浏览器内代码编辑器 + 终端。提供文件管理、代码编辑、终端操作和插件扩展能力。适用于命令行工具和脚本编写。
- **桌面环境**：基于 XFCE + noVNC 的浏览器内图形桌面。适用于需要图形界面工具的挑战（如 Ghidra 逆向分析）。
- **SSH 访问**：用户上传 SSH 公钥后，通过 `ssh -p 22 hacker@<域名>` 连接挑战容器。支持 SCP 文件传输。

## 工具预装

挑战环境预装常用的安全工具，包括：

- **调试器**：gdb（含 pwndbg/gef 插件）
- **漏洞开发**：pwntools、ipython
- **逆向工程**：Ghidra、radare2、Binary Ninja（需配置 API key）
- **网络分析**：wireshark、nmap、tcpdump、scapy
- **其他**：tmux、strace、curl、requests

完整工具列表取决于 `DOJO_CHALLENGE` 级别和 `INSTALL_*` 参数配置。

## 内核挑战与虚拟机

对于需要内核漏洞利用的挑战，平台支持两种额外虚拟化方式：

- **用户命名空间**：允许挑战创建任意网络拓扑和进程隔离。需要 seccomp 配置允许相关系统调用。
- **虚拟机**：在用户容器内运行 QEMU/KVM 虚拟机（需宿主机 `/dev/kvm` 可用）。虚拟机透明地与容器共享文件系统，文件修改双向同步。

## 挑战题目变体与反作弊

为每个用户和挑战组合独立签发 flag 是平台的主要反作弊机制。此外，挑战可配置多个变体（variant）：在挑战目录下创建 `_option1/`、`_option2/` 等子目录，每个子目录包含不同的挑战文件。系统根据用户 ID 和挑战 ID 的哈希值随机分配一个变体，使不同学生获得略有不同的挑战。

## 参考资源

- 示例道馆仓库：[hust-open-atom-club/example-dojo](https://github.com/hust-open-atom-club/example-dojo)
- 教师手册：`User_Manual_For_Teachers.md`
