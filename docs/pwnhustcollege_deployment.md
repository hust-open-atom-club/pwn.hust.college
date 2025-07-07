# pwn平台定制化部署

## 平台定制化部署框架
pwn.hust.college平台基于Docker与QEMU技术构建，在校园网环境下需针对域名访问、证书配置及服务路由进行定制化部署。由于校园网域名解析和SSL证书无法通过自动化流程配置，需通过手动配置NGINX实现服务转发与安全访问，同时保留平台核心的容器化架构与国产化技术支持特性。

## 基础环境准备
1. **依赖组件安装**  
   部署前需在校园网服务器中安装Docker、Docker Compose及QEMU相关工具，确保内核支持容器化与嵌套虚拟化：  
   ```bash
   # 安装Docker
   curl -fsSL https://get.docker.com | sh
   # 启用内核模块
   modprobe br_netfilter
   modprobe kvm
   # 安装QEMU
   apt-get install -y qemu-system-x86 qemu-system-loongarch64
   ```

2. **代码与数据目录配置**  
   克隆平台代码仓库（支持GitHub或Gitee），并创建数据目录用于持久化存储用户数据与挑战配置：  
   ```bash
   # 从Gitee克隆（国内访问优化）
   git clone https://gitee.com/hust-cse/pwn.hust.college.git ./platform
   # 创建数据目录（含用户home、数据库备份）
   mkdir -p ./platform/data/{homes,db,backups}
   chmod 777 ./platform/data  # 确保容器有读写权限
   ```

## 容器化部署核心配置
### Docker Compose定制
平台核心服务通过`docker-compose.yml`管理，需针对校园网环境调整端口映射与服务依赖：  
```yaml
version: '3'
services:
  ctfd:
    build: ./ctfd
    volumes:
      - ./data/ctfd:/var/www/ctfd/data
      - ./challenges:/var/www/ctfd/challenges
    environment:
      - SECRET_KEY=校园网环境专用密钥
      - DATABASE_URL=mysql+pymysql://ctfd:password@db/ctfd
      - WORKERS=4  # 根据服务器CPU核心数调整
    depends_on:
      - db
      - redis

  db:
    image: mysql:8.0
    volumes:
      - ./data/db:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=root密码
      - MYSQL_DATABASE=ctfd
      - MYSQL_USER=ctfd
      - MYSQL_PASSWORD=password

  redis:
    image: redis:alpine
    volumes:
      - ./data/redis:/data

  workspace:
    build: ./workspace
    privileged: true
    volumes:
      - ./data/homes:/dojo/homes
      - ./data/docker:/var/lib/docker
    environment:
      - DOJO_HOST=校园网内部IP（如10.10.10.10）
      - DOJO_PORT=8080  # 避开80/443端口冲突

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"  # 校园网HTTP端口
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl  # 存放手动配置的证书
    depends_on:
      - ctfd
      - workspace
```

### 国产化环境适配
1. **操作系统镜像替换**  
   在`workspace/Dockerfile`中指定国产openEuler基础镜像，确保挑战环境基于国产化系统：  
   ```dockerfile
   # 替换默认基础镜像为openEuler
   FROM openeuler/openeuler:22.03-lts
   RUN dnf install -y gcc gdb ghidra  # 安装必要工具
   ```

2. **LoongArch架构支持**  
   针对国产LoongArch架构的挑战，需在容器中预装专用工具链：  
   ```dockerfile
   # 安装LoongArch交叉编译工具
   RUN dnf install -y loongarch64-linux-gnu-gcc loongarch64-linux-gnu-gdb
   ```

## NGINX手动配置（校园网核心）
### 基础路由配置
创建`./nginx/conf.d/default.conf`，实现校园网内部服务转发：  
```nginx
server {
    listen 80;
    server_name pwn.hust.local;  # 校园网内部域名

    # 转发CTFd前端
    location / {
        proxy_pass http://ctfd:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 转发工作区服务（VSCode/WebSSH）
    location /workspace/ {
        proxy_pass http://workspace:8080/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态资源缓存（挑战描述、图片）
    location ~* \.(jpg|jpeg|png|css|js)$ {
        proxy_pass http://ctfd:8000;
        expires 1d;
        add_header Cache-Control "public";
    }
}
```

### 证书与安全配置（手动部署）
由于校园网域名无法自动申请公网证书，需使用自签证书或校园网CA颁发的证书：  
1. **生成自签证书**（仅供内部测试）：  
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout ./nginx/ssl/key.pem -out ./nginx/ssl/cert.pem -days 365 -nodes
   ```

2. **配置HTTPS（可选）**：  
   在NGINX中添加HTTPS支持（需校园网允许443端口）：  
   ```nginx
   server {
       listen 443 ssl;
       server_name pwn.hust.local;

       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;

       # 其他配置同HTTP部分
       location / {
           proxy_pass http://ctfd:8000;
       }
   }
   ```

## 校园网特殊场景处理
### 网络隔离与访问控制
1. **限制内部访问**  
   通过`iptables`限制仅校园网IP段（如10.0.0.0/8）访问平台：  
   ```bash
   # 在宿主机执行
   iptables -A INPUT -p tcp --dport 80 -s 10.0.0.0/8 -j ACCEPT
   iptables -A INPUT -p tcp --dport 80 -j DROP
   ```

2. **SSH访问配置**  
   学生需通过校园网SSH访问工作区，需在`workspace`容器中启用SSH服务并映射端口：  
   ```yaml
   # 在docker-compose.yml中添加
   workspace:
     ports:
       - "2222:22"  # 宿主机2222端口映射到容器SSH
   ```

### 数据备份与同步
针对校园网服务器可能的断电或维护，配置定时备份任务：  
```bash
# 创建备份脚本（每日凌晨3点执行）
cat > ./platform/backup.sh << 'EOF'
#!/bin/bash
docker exec platform_db_1 mysqldump -uroot -ppassword ctfd > ./data/backups/$(date +%Y%m%d).sql
# 保留最近30天备份
find ./data/backups -name "*.sql" -mtime +30 -delete
EOF

# 添加到crontab
chmod +x ./platform/backup.sh
echo "0 3 * * * $(pwd)/platform/backup.sh" | crontab -
```

## 部署验证与问题排查
1. **服务启动检查**  
   启动所有服务后，通过以下命令验证核心组件状态：  
   ```bash
   docker-compose up -d
   # 检查容器运行状态
   docker-compose ps
   # 查看CTFd日志（确认是否正常初始化）
   docker-compose logs -f ctfd
   ```

2. **常见问题解决**  
   - **端口冲突**：若80端口被校园网其他服务占用，修改NGINX映射端口（如`8080:80`）并更新校园网DNS解析；  
   - **国产化工具缺失**：检查`Dockerfile`中是否正确安装openEuler工具包，可通过`docker exec -it 容器ID dnf list installed`验证；  
   - **证书信任问题**：学生访问时若提示证书错误，需手动将校园网CA证书导入浏览器或操作系统信任列表。

通过以上定制化部署流程，平台可在校园网环境中稳定运行，既保留开源项目的容器化架构与游戏化教学特性，又适配国产化技术栈与校园网特殊网络环境，为学生提供安全、便捷的网络安全实践平台。
