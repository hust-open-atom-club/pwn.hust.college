# 开发

## 环境准备

开发 pwn.hust.college 需要以下环境：

- **Docker**：用于构建和运行平台容器。
- **Git**：用于克隆仓库和管理代码。
- **硬件**：支持 x86_64 或 ARM64 架构。若构建完整挑战镜像（`challenge-full`），需要约 70 GB 磁盘空间。

克隆仓库：

```sh
git clone https://github.com/hust-open-atom-club/pwn.hust.college.git
cd pwn.hust.college
```

## 本地开发环境

构建外部 dojo 容器并启动本地开发实例：

```sh
docker build -t pwncollege/dojo .
docker run --privileged -d -v "$(pwd):/opt/pwn.college:shared" \
  -p 22:22 -p 80:80 -p 443:443 --name dojo pwncollege/dojo
```

等待初始化完成（首次运行会构建挑战镜像，耗时较长）：

```sh
docker exec dojo dojo wait
```

完成后访问 `http://localhost.pwn.hust.college`（该域名默认解析到 `127.0.0.1`），使用用户名 `admin` 和密码 `admin` 登录。**必须**在首次登录后修改默认管理员凭据。

默认情况下，`DOJO_ENV=development` 使用 Flask 开发服务器运行，`DOJO_CHALLENGE=challenge-mini` 构建精简挑战镜像。可通过 `docker run` 的 `-e` 参数覆盖这些默认值。

## 插件与主题热更新

`dojo_plugin` 和 `dojo_theme` 以**只读绑定挂载**方式进入 ctfd 容器。编辑宿主机上的插件或主题文件后，无需重建镜像，执行以下命令即可生效：

```sh
docker exec dojo dojo sync
docker exec dojo dojo compose restart ctfd
```

`dojo sync` 将以下内容复制到容器内对应位置：
- `ctfd/*` → `/opt/CTFd/`
- `dojo_plugin/` → `/opt/CTFd/CTFd/plugins/dojo_plugin`
- `dojo_theme/` → `/opt/CTFd/CTFd/themes/dojo_theme`

注意：对 `ctfd/` 目录或 `challenge/` 目录的修改需要重建镜像（`dojo compose up -d --build`），仅插件和主题支持热更新。

## 代码组织

`dojo_plugin` 采用分层结构：

| 目录 | 职责 |
|------|------|
| `pages/` | Flask Blueprint，处理 HTML 页面视图。每个 Blueprint 对应一个功能模块（dojos、workspace、desktop、sso、kook、discord、sensai、course、writeups、belts、users、settings） |
| `api/v1/` | REST API Blueprint，前缀 `/pwncollege_api/v1`。提供 docker 容器管理、排行榜、绶带、道馆管理、SSO 认证等接口 |
| `utils/` | 业务逻辑模块。包含 flag 序列化、markdown 渲染、道馆加载、防火墙、seccomp、奖励追踪（`awards.py`）、请求日志（`request_logging.py`）、KOOK/Discord 工具等 |
| `models/` | SQLAlchemy ORM 模型。定义 `Dojos`、`DojoModules`、`DojoChallenges`、`Belts`（绶带）、`Emojis`（徽章）、`SSHKeys`、`DiscordUsers` 等 |
| `config.py` | 启动引导 + 环境变量解析。从 docker-compose 环境读取配置，`bootstrap()` 设置 CTFd 初始状态 |
| `__init__.py` | 插件入口。`load()` 函数注册所有 Blueprint、挑战类型、flag 类型，初始化 Prometheus 指标和请求日志 |
| `prometheus_metrics.py` | Prometheus 自定义指标定义 |
| `scripts/warm_cache.py` | 缓存预热脚本（由 systemd timer 定期调用） |

`dojo_theme` 目录结构：

| 目录 | 职责 |
|------|------|
| `templates/` | Jinja2 HTML 模板（dojo 列表、挑战页面、绶带榜、登录页等） |
| `templates/components/` | 可复用组件（导航栏等） |
| `static/` | CSS、JS、图片（道馆图标、宝可梦精灵等） |

## dojo 命令参考

所有 `dojo` 命令在外部 dojo 容器内运行。从宿主机使用 `docker exec dojo dojo <子命令>` 调用。

| 命令 | 说明 |
|------|------|
| `dojo start` | 入口点：sync → dojo-init → systemd |
| `dojo sync` | 同步插件/主题/ctfd 文件到容器内 |
| `dojo update` | `git pull && dojo sync && dojo compose up -d --build`（仅在理解每个提交时使用） |
| `dojo compose <args>` | 运行 docker compose 命令（自动加载 config.env） |
| `dojo flask` | 在 ctfd 容器中打开 Flask shell（预导入 CTFd 和 dojo_plugin 模型） |
| `dojo db` | 连接 mariadb 客户端 |
| `dojo enter [-s] <用户ID或用户名>` | 进入用户挑战容器。`-s` 以 root 身份进入 |
| `dojo logs` | 查看 dojo 日志（`journalctl -u pwn.college -f`） |
| `dojo backup` | 备份数据库到 `data/backups/` |
| `dojo restore <路径>` | 从备份恢复数据库 |
| `dojo wait` | 等待 dojo 启动完成 |

## 测试

平台测试使用 pytest，测试文件位于 `test/` 目录。测试需要在一个运行中的 dojo 实例上执行。

运行完整测试套件：

```sh
sudo ./test/local-tester.sh
```

该脚本会停止并删除已有的 `dojo-test` 容器，重建并等待启动完成，然后运行 `pytest -v test/test_running.py`。常用选项：

- `-T`：跳过测试，仅重建容器。
- `-c <容器名> -D`：使用自定义容器名和空白数据卷。

对已在运行的容器执行测试：

```sh
MOZ_HEADLESS=1 pytest -v test/test_running.py
CONTAINER_NAME=my-dojo pytest -v test/test_running.py  # 指定容器
MOZ_HEADLESS=1 pytest -v test/test_running.py::test_login  # 单个测试
```

关键测试辅助函数（`test/utils.py`）：

- `login(name, password)` — 创建认证会话（含 CSRF token）
- `dojo_run(*args)` — 从宿主机运行 `docker exec <容器名> dojo ...`
- `create_dojo(repo_type, repo)` / `create_dojo_yml(spec)` — 通过 API 创建道馆
- `make_dojo_official(dojo_rid, admin_session)` — 将道馆设为全局可见

常用 pytest fixture（`test/conftest.py`）：

- `admin_session`（会话级）— 管理员认证会话
- `random_user`（函数级）— 每个测试独立的新用户
- `example_dojo`（会话级）— `hust-open-atom-club/example-dojo` 作为官方道馆
- `simple_award_dojo`（会话级）— 从 `test/dojos/simple_award_dojo.yml` 加载的道馆

测试道馆 YAML 规格存放在 `test/dojos/` 目录。

## 分支策略

- 默认工作分支为 `hustsec_dev`，不是 `master`/`main`。
- Pull Request 目标分支为 `hustsec_dev`。
- CTFd 版本锁定为 **3.6.0**（在 `Dockerfile` 中通过 `--branch 3.6.0` 指定），升级前需审计 `dojo_plugin/__init__.py` 对 CTFd 视图函数的覆盖是否兼容。
- 贡献流程参见 `CONTRIBUTING.md`。

## 常见开发任务

**添加新页面**：在 `pages/` 中创建 Blueprint → 在 `__init__.py` 的 `load()` 中注册 → 在 `dojo_theme/templates/` 中添加模板。

**添加新 API 接口**：在 `api/v1/` 中添加 Resource → 在 `api/__init__.py` 中注册到 API namespace。

**添加环境变量配置**：在 `docker-compose.yml` 的 ctfd 服务 `environment` 中添加 → 在 `config.py` 中用 `os.getenv()` 读取 → 在 `data/config.env` 中声明默认值。

## 调试技巧

查看各容器日志：

```sh
docker exec dojo dojo logs       # dojo 整体日志
docker logs ctfd                  # CTFd 日志
docker logs nginx-proxy           # nginx 日志
```

进入 Python 交互环境检查数据库状态：

```sh
docker exec dojo dojo flask
```

进入用户挑战容器排查挑战问题：

```sh
docker exec dojo dojo enter <用户名>
docker exec dojo dojo enter -s <用户名>  # 以 root 进入
```
