## 部署 (Deployment)

```sh
# 设置 Docker CE 的下载镜像源为华中科技大学镜像站，并执行官方安装脚本
export DOWNLOAD_URL="https://mirrors.hust.edu.cn/docker-ce" && curl -fsSL https://get.docker.com | /bin/sh
# 从 GitHub 克隆 dojo 的源代码
git clone https://github.com/hust-open-atom-club/dojo.git
# 使用克隆下来的 Dockerfile 构建一个名为 pwncollege/dojo 的 Docker 镜像
docker build -t pwncollege/dojo dojo
# 运行 dojo 容器
docker run --privileged -d -v "$(pwd)/dojo:/opt/pwn.college:shared" -p 22:22 -p 80:80 -p 443:443 --name dojo pwncollege/dojo
```

这个过程会运行初始设置，包括构建挑战所用的 Docker 镜像。它会根据宿主机的硬件架构来构建镜像。

### 本地设置 (Local Setup)

默认情况下，dojo 会初始化并监听 `localhost.pwn.college` 这个域名（该域名解析到 127.0.0.1）。
这对于本地开发来说没有问题，但如果你想把你的 dojo 服务开放给全世界访问，你需要更新这个设置（参考下文的 [生产环境设置](#production-setup)）。

初始化所有内容并构建挑战镜像会花费一些时间。
你可以通过以下命令来检查你的容器状态（以及初始构建的进度）：

```sh
docker exec dojo dojo logs
```

一旦设置完成，你应该就可以访问 dojo 了，使用用户名 `admin` 和密码 `admin` 登录。
你 **必须** 在管理员后台修改这些默认的管理员凭据。

### 生产环境设置 (Production Setup)

通过向 `docker run` 命令添加 `-e KEY=value` 参数可以自定义设置过程。
你可以用 `docker stop dojo` 停止已经运行的 dojo 实例，然后用修改后的参数重新运行 `docker run` 命令。

为了更改服务监听的域名，你可以修改 `DOJO_HOST`，例如：`-e DOJO_HOST=localhost.pwn.college`。
为了让它正常工作，你必须通过 DNS 将你的域名正确地指向服务器的 IP 地址。
如果你没有域名，你也可以在 `DOJO_HOST` 参数中直接输入你的 IP 地址。

默认情况下，构建的是一个最小化的挑战镜像。
如果你想要更多你习惯使用的功能，可以修改 `DOJO_CHALLENGE`，例如：`-e DOJO_CHALLENGE=challenge-mini`。
可用的选项如下：
-   `challenge-nano`: 一个非常精简的配置。
-   `challenge-micro`: 在 nano 的基础上增加了 VSCode。
-   `challenge-mini`: 在 micro 的基础上增加了一个精简的桌面环境（默认选项）。
-   `challenge-full`: 完整的（超过 70 GB）配置。

当你想在不同硬件架构的平台上部署时，可以使用 `config.env` 文件中的 `ARCH` 参数。该参数的默认值是 `amd64`，如果部署在 ARM 架构上，参数值应为 `arm64`。

更多可配置的参数，请参考在 dojo 目录中创建的 `data/config.env` 文件。

对于 HTTPS 证书，你可以将其复制到名为 `pwncollege_certs` 的挂载卷中。
```
# docker inspect pwncollege_certs
[
    {
        "CreatedAt": "2024-04-02T13:03:24Z",
        "Driver": "local",
        "Labels": {
            "com.docker.compose.project": "pwncollege",
            "com.docker.compose.version": "2.20.2",
            "com.docker.compose.volume": "certs"
        },
        "Mountpoint": "/opt/pwn.college/data/docker/volumes/pwncollege_certs/_data",
        "Name": "pwncollege_certs",
        "Options": null,
        "Scope": "local"
    }
]

/opt/pwn.college/data/docker/volumes/pwncollege_certs/_data# ls -al
-rw-r--r-- 1 root root 7769 May 21 10:16 pwn.cse.hust.edu.cn.crt
-rw-r--r-- 1 root root 1704 May 21 10:16 pwn.cse.hust.edu.cn.key
```
通过执行以下命令，HTTPS 证书将会被自动配置：
```
dojo compose down
dojo update
```

## 更新 (Updating)

当更新你的 dojo 部署时，在 `dojo` 源码目录下，官方只支持一种方法：

```sh

docker kill dojo
docker rm dojo
# 拉取最新的代码
git pull
# 重新构建镜像
docker build -t pwncollege/dojo dojo
# 重新运行容器
sudo docker run --privileged -d -v "$(pwd)/dojo:/opt/pwn.college:shared" -p 22:22 -p 80:80 -p 443:443 --name dojo pwncollege/dojo
```


这种更新方式会在 dojo 重建期间导致服务中断。

有些更改**可以**在不完全重启的情况下应用，但这并不能保证一定成功。

如果你真的清楚你在做什么（比如你拉取的更新只涉及 `ctfd` 部分），你可以在 `pwncollege/dojo` 容器内部执行以下操作：

```sh
dojo update
```

请注意，`dojo update` 并不能保证一定成功，只有在你完全理解你所更新的每一个提交/更改时才应该使用它。

## 自定义 (Customization)

**所有** dojo 的数据都将存储在 `./data` 目录中。
**【译者注】**：此处的 `./data` 指的是**绑定挂载**到容器内的那个宿主机目录下的 `data` 子目录。如果使用的是命名卷，则这些数据会存在于 Docker 管理的卷中。

登录后，你可以通过访问 `/dojos/create` 页面来添加一个 dojo。Dojo 是包含在 Git 仓库中的。
更多信息请参考 [示例 dojo](https://github.com/pwncollege/example-dojo)。
