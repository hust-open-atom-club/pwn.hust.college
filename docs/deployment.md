# 3. 部署文档（deployment.md）

## 部署概述
pwn.hust.college平台基于pwn.college的DOJO架构开发，采用Docker容器技术与QEMU技术构建虚拟化环境，支持本地部署、生产环境部署及多节点扩展。平台部署需满足国产化技术适配要求，优先集成openEuler操作系统及LoongArch等国产架构支持，同时兼容GitHub与Gitee代码托管平台，确保教学资源的安全性与合规性。


## 基础部署流程
### 环境准备
1. **依赖安装**：  
   需预先安装Docker服务并启用`br_netfilter`模块以支持网络配置，执行以下命令初始化基础环境：  
   ```sh
   curl -fsSL https://get.docker.com | /bin/sh
   modprobe br_netfilter  # 启用网络过滤模块
   ```

2. **代码与镜像构建**：  
   克隆平台代码仓库并构建Docker镜像，指定本地路径存储数据（含用户数据、挑战关卡及配置文件）：  
   ```sh
   DOJO_PATH="./dojo"
   DATA_PATH="./dojo/data"
   git clone https://github.com/pwncollege/dojo "$DOJO_PATH"  # 支持替换为Gitee镜像仓库
   docker build -t pwncollege/dojo "$DOJO_PATH"
   ```

3. **容器启动**：  
   通过`docker run`启动平台容器，映射必要端口（SSH、HTTP/HTTPS）并挂载数据卷，确保国产化环境配置生效：  
   ```sh
   docker run \
       --name dojo \
       --privileged \
       -v "${DOJO_PATH}:/opt/pwn.college" \
       -v "${DATA_PATH}:/data" \
       -p 22:22 -p 80:80 -p 443:443 \
       -d \
       pwncollege/dojo
   ```
   - **MacOS特殊配置**：因嵌套挂载限制，需将`data/docker`替换为Docker卷以支持OverlayFS：  
     ```sh
     -v "dojo-data-docker:/data/docker"
     ```

4. **初始化验证**：  
   容器启动后，通过以下命令查看初始化进度（含挑战镜像构建与国产化组件适配）：  
   ```sh
   docker exec dojo dojo logs
   ```  
   完成后可通过`localhost.pwn.college`访问平台，默认管理员账号为`admin:admin`。


## 生产环境部署
### 配置定制
- **核心参数**：通过`-e KEY=VALUE`或修改`$DATA_PATH/config.env`调整配置，关键参数包括：  
  - `DOJO_ENV=production`：切换至生产模式（禁用调试工具）；  
  - `DOJO_HOST=example.com`：指定域名（需配置DNS指向服务器IP）；  
  - 国产化配置：自动加载openEuler镜像源及LoongArch架构工具链。

- **统一身份认证集成**：通过配置SSO接口对接华中科技大学统一身份认证系统，实现学生免注册登录：  
  ```env
  SSO_ENABLED=true
  SSO_URL=https://sso.hust.edu.cn/cas
  ```

### 多节点扩展
为支持大规模教学场景，平台可部署主节点与工作区节点的分布式架构：

1. **主节点部署**：  
   暴露WireGuard端口（51820/udp）用于节点通信，执行：  
   ```sh
   docker run \
       --name dojo-main \
       --privileged \
       -v "${DOJO_PATH}:/opt/pwn.college" \
       -v "/tmp/dojo-data-main:/data" \
       -p 22:22 -p 80:80 -p 443:443 -p 51820:51820/udp \
       -d \
       pwncollege/dojo
   ```  
   获取认证密钥与主机地址：  
   ```sh
   docker exec -it dojo-main bash
   dojo node show | grep -oP 'WORKSPACE_KEY: \K[A-Za-z0-9+/]+={0,2}'  # 工作区节点认证密钥
   ip -4 addr show eth0 | grep -oP 'inet \K[0-9\.]+'                  # 主节点IP
   ```

2. **工作区节点部署**：  
   使用主节点的`WORKSPACE_KEY`与`DOJO_HOST`初始化，指定节点ID（从1开始递增）：  
   ```sh
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
   ```

3. **节点注册**：  
   在主节点中添加工作区节点的`NODE_KEY`（从工作区节点获取）：  
   ```sh
   docker exec -it dojo-main bash
   dojo node add 1 <NODE_KEY>  # 1为工作区节点ID
   dojo compose restart --no-deps ctfd
   ```


## 平台更新与维护
### 版本更新
1. **完整更新**（推荐）：  
   ```sh
   docker rm -f dojo
   git -C "$DOJO_PATH" pull  # 支持从Gitee仓库同步
   docker build -t pwncollege/dojo "$DOJO_PATH"
   docker run ...  # 重复启动命令
   ```

2. **快速更新**（仅限CTFd插件变更）：  
   ```sh
   docker exec -it dojo bash
   dojo update
   ```

### 数据备份与恢复
- 自动备份：每小时将数据库备份至`/data/backups`，支持配置S3兼容存储（如阿里云OSS）保存备份。  
- 手动备份：执行`dojo db dump > backup.sql`导出数据库，通过`dojo db restore < backup.sql`恢复。


## 常见问题与国产化适配
1. **权限错误**：  
   若构建时出现`permission denied`，检查代码仓库目录权限，确保`data`目录不在构建上下文（参考`.dockerignore`配置）。

2. **共享挂载问题**：  
   日志中出现`not a shared mount`时，需将`/data`挂载为共享卷：  
   ```sh
   -v /host/path:/data:shared
   ```

3. **国产化架构支持**：  
   部署时自动检测CPU架构，LoongArch平台需额外安装专用工具链：  
   ```sh
   docker exec dojo apt install -y loongarch64-linux-gnu-gcc
   ```


