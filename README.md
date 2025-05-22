# DOJO

**Deploy your pwn.hust.college dojo instance** – a customized fork of the original [pwn.college platform](https://github.com/pwncollege/dojo) – to create tailored cybersecurity training environments.

![](docs/static/landing_page.png)

## Introduction

Same with pwn.college, the pwn.hust.college dojo infrastructure is based on [CTFd](https://github.com/CTFd/CTFd). CTFd provides features like user authentication, challenge management, and flag validation, this repository extends its capabilities to create a structured, scalable environment for cybersecurity training. Furthermore, the pwn.hust.college also provides some features related to HUST(Huazhong University of Science and Technology), e.g., HUST SSO login, DeepSeek TA, KOOK integration and cybersecurity courses.

The pwn.hust.college infrastructure allows users the ability to "start" challenges, which spins up a private docker container for that user.
This docker container will have the associated challenge binary injected into the container as root-suid, as well as the flag to be submitted as readable only by the the root user.
Users can enter this container via vscode in the browser ([code-server](https://github.com/cdr/code-server)), via XFCE desktop environment in the browser([noVNC](https://github.com/novnc/noVNC)), via `ssh` by supplying a public ssh key in their profile settings.
The associated challenge binary may be either global, which means all users will get the same binary, or instanced, which means that different users will receive different variants of the same challenge.

## Setup

```sh
export DOWNLOAD_URL="https://mirrors.hust.edu.cn/docker-ce" && curl -fsSL https://get.docker.com | /bin/sh
git clone https://github.com/hust-open-atom-club/dojo.git
docker build -t pwncollege/dojo dojo
docker run --privileged -d -v "dojo:/opt/pwn.college:shared" -p 22:22 -p 80:80 -p 443:443 --name dojo pwncollege/dojo
```

This will run the initial setup, including building the challenge docker image. It would build docker image based on the host architecture.

### Local Setup

By default, the dojo will initialize itself to listen on and serve from `localhost.pwn.college` (which resolves 127.0.0.1).
This is fine for development, but to serve your dojo to the world, you will need to update this (see [Production Setup](#production-setup)).

It will take some time to initialize everything and build the challenge docker image.
You can check on your container (and the progress of the initial build) with:

```sh
docker exec dojo dojo logs
```

Once things are setup, you should be able to access the dojo and login with username `admin` and password `admin`.
You **MUST** change these admin credentials in the admin panel.

### Production Setup

Customizing the setup process is done through `-e KEY=value` arguments to the `docker run` command.
You can stop the already running dojo instance with `docker stop dojo`, and then re-run the `docker run` command with the appropriately modified flags.

In order to change where the host is serving from, you can modify `DOJO_HOST`, e.g., `-e DOJO_HOST=localhost.pwn.college`.
In order for this to work correctly, you must correctly point the domain at the server's IP via DNS.
If you don't have a domain name, you can enter your IP address in the `DOJO_HOST` parameter.

By default, a minimal challenge image is built.
If you want more of the features you are used to, you can modify `DOJO_CHALLENGE`, e.g., `-e DOJO_CHALLENGE=challenge-mini`.
The following options are available:
- `challenge-nano`: A very minified setup.
- `challenge-micro`: Adds VSCode.
- `challenge-mini`: Adds a minified desktop (by default).
- `challenge-full`: The full (70+ GB) setup.

When you want to deploy it on platforms with different architectures, you can use the `ARCH` parameter in 
the `config.env` file. The default parameter value is `amd64`, and if deploying on ARM architecture, the parameter value is `arm64`.

For more arguments, please refer to `data/config.env` created in the dojo directory.

For https certificates, you can copy to the pwncollege_certs mounted volume.
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
The https certificate will be configured automatically by executing the following command.
```
dojo compose down
dojo update
```

## Updating

When updating your dojo deployment, there is only one supported method in the `dojo` directory:

```sh
docker kill pwncollege/dojo
docker rm pwncollege/dojo
git pull
docker build -t pwncollege/dojo dojo
docker run --privileged -d -v "dojo:/opt/pwn.college:shared" -p 22:22 -p 80:80 -p 443:443 --name dojo pwncollege/dojo
```

This will cause downtime when the dojo is rebuilding.

Some changes _can_ be applied without a complete restart, however this is not guaranteed.

If you really know what you're doing (the changes that you're pulling in are just to `ctfd`), inside the `pwncollege/dojo` container you can do the following:

```sh
dojo update
```

Note that `dojo update` is not guaranteed to be successful and should only be used if you fully understand each commit/change that you are updating.

## Customization

_All_ dojo data will be stored in the `./data` directory.

Once logged in, you can add a dojo by visiting `/dojos/create`. Dojos are contained within git repositories. 
Refer to [the example dojo](https://github.com/pwncollege/example-dojo) for more information.

Have more questions? Open an ❓[issue](https://github.com/hust-open-atom-club/dojo/issues) or reach out to us on our 💬 [KOOK](https://kook.top/soUkFL).

## Contributing

We love Pull Requests! 🌟
Have a small update?
Send a PR so everyone can benefit.

Together, we make this project better for all! 🚀 
Please refer to [CONTRIBUTING.md](/CONTRIBUTING.md) for more details.
