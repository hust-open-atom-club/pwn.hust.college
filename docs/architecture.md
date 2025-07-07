# TODO

平台核心架构概览

pwn.hust.college 平台基于 pwn.college 的 DOJO 架构开发，核心定位为实操型网络安全教育平台。平台采用夺旗赛（CTF）竞赛模式，学习者通过解决挑战获取 flag 以证明技能掌握。与传统平台不同，平台提供预配置环境，支持浏览器或 SSH 访问，学习者可直接投入实战挑战，无需自行搭建环境。
平台重点支持学习者在环境中完成高级技术挑战的全流程操作，包括发现、实现和调试。尽管代码量仅约 5000 行，但架构复杂。整体作为热门 CTFd 平台的 “插件” 实现，CTFd 提供用户、挑战及提交 flag 等基础功能，平台在此基础上扩展，允许教师创建挑战，学生在浏览器式工作区环境中解题。

基础设施容器化

平台组件由 docker compose 管理，管理员可在裸机上启动，不过实际部署时整个基础设施运行在一个 docker 容器（称为 “外部 docker”）内。工作区环境相互隔离，基于 Docker 容器实现，比虚拟机部署性能更优。学生开始挑战时工作区启动，完成挑战后（或超时后）停止，自动生成多个服务，如 VSCode 实例和桌面环境，通过内部 nginx 重定向在浏览器中访问。学生也可在个人资料设置中提供 SSH 公钥后，通过 SSH 连接工作区。
工作区的 home 目录在实例间持久化，方便学生保存工作并后续继续。若挑战需要（如内核漏洞利用），工作区可适时启动虚拟机，或配置自定义网络（如网络漏洞利用）。此外，工作区预装一系列工具，包括调试器、反汇编器和漏洞开发工具。
挑战目标始终是 “夺旗”。学习者以 hacker 用户（UID 1000）身份运行，/flag 位置有 flag 文件，仅 root 用户（UID 0）可读取。挑战程序作为 root 拥有的 setuid 二进制文件运行，因此能够读取 flag，学习者需满足挑战要求或利用挑战程序漏洞来获取 flag。

平台脚本

dojo-init：初始化主机环境，为后续运行做准备。
dojo：提供与数据库（支持 Python 接口和直接通过 DB 客户端）、用户容器及平台容器的交互功能。
dojo-node：管理平台主机与其用户托管节点的连接，主要用于主部署。

平台启动流程

外部 docker 通过 dojo-init 初始化环境，然后运行 systemd，最终调用 dojo up。同时存在一些其他 systemd 服务，如每小时将平台主数据库备份到 /data/backups、将备份同步到云端、每分钟刷新各种 redis 缓存以保证前端流畅、每分钟刷新所有节点的挑战容器等。

平台配置

平台大部分配置位于两个文件：

/data/config.env：若不存在，由 dojo-init 创建，控制多种选项。
/data/workspace_nodes.json：由 dojo-node 创建，默认为空列表，dojo-node 脚本负责更新添加新节点，
列表中每个条目为节点的 wireguard 公钥。

平台数据库

平台使用 mysql 数据库，默认情况下数据库位于 db 容器中。通过在 config.env 中设置 DB_HOST 可使用外部数据库，为节省资源，设置 DB_EXTERNAL 为 yes 可避免 db 容器启动 mysql。可通过 dojo db 启动数据库客户端会话。
CTFd 与平台插件
平台前端界面是一个全转换式 CTFd 插件，插件及其配套主题 / 模板几乎取代所有前端功能。CTFd 使用 SQLAlchemy ORM 访问平台数据库，可通过 dojo flask 进入 python shell 利用该功能。docker-in-docker 守护进程的 docker 套接字映射到 CTFd 容器中，使 CTFd 能够启动用户挑战容器。

挑战容器

当用户启动挑战时，CTFd 启动一个与基础设施容器并行运行的 docker 容器，具体操作包括：
将挑战文件复制到容器中。
将工作区工具覆盖层挂载到容器。
将用户的 home 目录挂载到容器。
容器初始化通过另一个 dojo-init 完成，包括确保某些标准文件充分初始化（如 hacker 用户在 /etc/passwd 中存在、/bin/sh 有效等）、设置 /flag 以及若存在 /challenge/.init 则运行该文件。挑战容器启动命令为 sleep 6，因此 6 小时后超时。

平台工作区

平台通过在每个启动的挑战的 /nix 目录挂载基于 nix 的覆盖层，为用户提供标准安全工具。该覆盖层由 workspace-builder 容器构建（安装 nix 包），在平台启动前完成，可能导致全新平台启动延迟。为提高挑战与用户工具的隔离性，平台使用基于 fuse 的覆盖层阻止挑战默认访问 /nix 工具，该功能由 workspace_fs 容器提供，通过 compose 自动启动。

平台用户 home 目录

平台支持每个用户的持久化 home 目录，存储在 /dojo/homes/btrfs.img 的 btrfs 卷中，每个 home 是一个子卷，挂载在 /dojo/homes 并映射到每个 docker 容器。可通过 btrfs subvolume list /data/homes 等命令检查和管理。每个用户分配 1GB 空间。
用户 home 目录通过 docker 卷插件的巧妙使用挂载到 docker 容器：homefs 容器启动一个服务，通过 docker-in-docker 守护进程插件目录中的 “homefs” unix 套接字通信，home 目录挂载类型指定为 homefs，使 docker 自动与 homefs 服务通信以挂载子卷。

平台工作区访问
HTTP 访问：通过 CTFd 代理，当 dojo-plugin 收到请求时，自动在用户容器中启动相关服务。
SSH 访问：由 sshd 容器处理，该容器检查提供的公钥与数据库中的密钥表，检索对应的用户，并通过 docker exec 进入该用户正在运行的容器。

平台日志
管理或开发时可能需要查看的有用日志：

dojo-init：docker logs dojo（外部 docker 的日志）
dojo：journalctl -b -u pwn.college.*
ctfd：docker logs ctfd
nginx：docker logs nginx-proxy

除第一个外，其余需在外部 docker 内部运行。若在外部 docker 外（如主机本身），可使用 docker exec dojo journalctl -b -u dojo-up 等命令。

The pwn.hust.college infrastructure allows users the ability to "start" challenges, which spins up a private docker container for that user.
This docker container will have the associated challenge binary injected into the container as root-suid, as well as the flag to be submitted as readable only by the the root user.
Users can enter this container via vscode in the browser ([code-server](https://github.com/cdr/code-server)), via XFCE desktop environment in the browser([noVNC](https://github.com/novnc/noVNC)), via `ssh` by supplying a public ssh key in their profile settings.
The associated challenge binary may be either global, which means all users will get the same binary, or instanced, which means that different users will receive different variants of the same challenge.
