# 部署
一、部署概述

pwn.hust.college 平台基于 pwn.college 的 DOJO 架构开发，采用 Docker 容器技术与 QEMU 技术构建虚拟化环境，支持本地部署、生产环境部署及多节点扩展。平台部署需满足国产化技术适配要求，优先集成 openEuler 操作系统及 LoongArch 等国产架构支持，同时兼容 GitHub 与 Gitee 代码托管平台，确保教学资源的安全性与合规性。

二、基础部署流程

2.1环境准备

2.1.1依赖安装：
需预先安装 Docker 服务并启用br_netfilter模块以支持网络配置，执行以下命令初始化基础环境：
sh
curl -fsSL https://get.docker.com | /bin/sh
modprobe br_netfilter  # 启用网络过滤模块

2.1.2代码与镜像构建：
克隆平台代码仓库并构建 Docker 镜像，指定本地路径存储数据（含用户数据、挑战关卡及配置文件）：
sh
DOJO_PATH="./dojo"
DATA_PATH="./dojo/data"
git clone https://github.com/pwncollege/dojo "$DOJO_PATH"  # 支持替换为Gitee镜像仓库
docker build -t pwncollege/dojo "$DOJO_PATH"

2.1.3容器启动：
通过docker run启动平台容器，映射必要端口（SSH、HTTP/HTTPS）并挂载数据卷，确保国产化环境配置生效：
sh
docker run \
    --name dojo \
    --privileged \
    -v "${DOJO_PATH}:/opt/pwn.college" \
    -v "${DATA_PATH}:/data" \
    -p 22:22 -p 80:80 -p 443:443 \
    -d \
    pwncollege/dojo

MacOS 特殊配置：因嵌套挂载限制，需将data/docker替换为 Docker 卷以支持 OverlayFS：
sh
-v "dojo-data-docker:/data/docker"

2.1.4初始化验证：
容器启动后，通过以下命令查看初始化进度（含挑战镜像构建与国产化组件适配）：
sh
docker exec dojo dojo logs

完成后可通过localhost.pwn.college访问平台，默认管理员账号为admin:admin。

三、生产环境部署

3.1配置定制

3.1.1核心参数：通过-e KEY=VALUE或修改$DATA_PATH/config.env调整配置，关键参数包括：
DOJO_ENV=production：切换至生产模式（禁用调试工具）；
DOJO_HOST=example.com：指定域名（需配置 DNS 指向服务器 IP）；
国产化配置：自动加载 openEuler 镜像源及 LoongArch 架构工具链。

3.1.2统一身份认证集成：通过配置 SSO 接口对接华中科技大学统一身份认证系统，实现学生免注册登录：
env
SSO_ENABLED=true
SSO_URL=https://sso.hust.edu.cn/cas

3.2多节点扩展
为支持大规模教学场景，平台可部署主节点与工作区节点的分布式架构：

3.2.1主节点部署：
暴露 WireGuard 端口（51820/udp）用于节点通信，执行：
sh
docker run \
    --name dojo-main \
    --privileged \
    -v "${DOJO_PATH}:/opt/pwn.college" \
    -v "/tmp/dojo-data-main:/data" \
    -p 22:22 -p 80:80 -p 443:443 -p 51820:51820/udp \
    -d \
    pwncollege/dojo

获取认证密钥与主机地址：
sh
docker exec -it dojo-main bash
dojo node show | grep -oP 'WORKSPACE_KEY: \K[A-Za-z0-9+/]+={0,2}'  # 工作区节点认证密钥
ip -4 addr show eth0 | grep -oP 'inet \K[0-9\.]+'                  # 主节点IP

3.2.2工作区节点部署：
使用主节点的WORKSPACE_KEY与DOJO_HOST初始化，指定节点 ID（从 1 开始递增）：
sh
WORKSPACE_NODE=1
WORKSPACE_KEY=xxx
DOJO_HOST=xxx.xxx.xxx.xxx
docker run \
    --name dojo-workspace \
    --privileged \
    -e DOJO_HOST=$DOJO_HOST \
    -e WORKSPACE_KEY=$WORKSPACE_KEY \
    -e WORKSPACE_NODE=$WORKSPACE_NODE \
    -v "${DOJO_PATH}:/opt/pwn.college" \
    -v "/tmp/dojo-data-workspace:/data" \
    -d \
    pwncollege/dojo

3.2.3节点注册：
在主节点中添加工作区节点的NODE_KEY（从工作区节点获取）：
sh
docker exec -it dojo-main bash
dojo node add 1 <NODE_KEY>  # 1为工作区节点ID
dojo compose restart --no-deps ctfd

四、平台更新与维护

4.1版本更新

4.1.1完整更新（推荐）：
sh
docker rm -f dojo
git -C "$DOJO_PATH" pull  # 支持从Gitee仓库同步
docker build -t pwncollege/dojo "$DOJO_PATH"
docker run ...  # 重复启动命令

4.2.2快速更新（仅限 CTFd 插件变更）：
sh
docker exec -it dojo bash
dojo update

4.2数据备份与恢复
自动备份：每小时将数据库备份至/data/backups，支持配置 S3 兼容存储（如阿里云 OSS）保存备份。
手动备份：执行dojo db dump > backup.sql导出数据库，通过dojo db restore < backup.sql恢复。

五、常见问题与国产化适配

5.1权限错误：
若构建时出现permission denied，检查代码仓库目录权限，确保data目录不在构建上下文（参考.dockerignore配置）。

5.2共享挂载问题：
日志中出现not a shared mount时，需将/data挂载为共享卷：
sh
-v /host/path:/data:shared

5.3国产化架构支持：
部署时自动检测 CPU 架构，LoongArch 平台需额外安装专用工具链：
sh
docker exec dojo apt install -y loongarch64-linux-gnu-gcc
