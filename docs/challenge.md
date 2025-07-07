# 挑战

一、挑战定义

挑战由遵循 “夺旗” 范式的 docker 镜像定义。所有挑战的环境基础设施（如 VSCode、桌面环境、虚拟机等）和标准工具（如 gdb、ghidra、pwntools、wireshark 等）通过 nix 在 /nix 目录以只读挂载方式提供，包含必要的程序、库和配置文件。这使得挑战镜像无需关注运行环境细节，可专注于挑战本身。

二、挑战入口点

/challenge/.init 在初始化接近尾声、工作区对学生开放前执行。该程序以 root 用户身份运行，负责设置任何动态的挑战特定配置，或启动挑战可能需要的服务。该程序必须退出（状态码为 0）后工作区才对学生开放，因此应将任何长期运行的进程 fork 出去，自身快速终止。

过时提示

此接口创建于平台能够将任意 docker 镜像作为挑战运行之前。目前，挑战镜像的 ENTRYPOINT 和 CMD 被完全忽略。未来计划调整为 ENTRYPOINT 仍由平台控制，但 CMD 将优先于 /challenge/.init。若希望挑战兼容未来变化，应将挑战镜像的 CMD 设置为 /challenge/.init。

三、挑战 Bashrc

过时提示
此接口创建于平台能够将任意 docker 镜像作为挑战运行之前。未来可能会移除该接口，转而使用 /etc/bashrc 或 /run/challenge/etc/bashrc（旨在确保平台和挑战都能对 bashrc 有所控制）。若有相关想法或担忧，请提交 issue！

四、$PATH 中的 /run/challenge/bin

初始化期间，/nix/var/nix/profiles/dojo-workspace 位置的 nix 配置文件被符号链接到 /run/dojo。为确保标准工具易于访问，PATH 被设置为优先考虑 /run/dojo/bin 而非默认 PATH。这意味着当用户运行 gdb 时，将使用工作区提供的标准 gdb（位于 /run/dojo/bin/gdb），而非挑战镜像可能提供的其他 gdb（如 /usr/bin/gdb）。

工作区通过这种方式提供大量工具，为所有挑战提供一致的环境，确保学生能够使用熟悉的工具。若挑战希望优先使用自身程序，可通过 /run/challenge/bin 目录中的符号链接实现。但应谨慎使用，仅当挑战确实期望默认使用特定的程序版本时才这样做。

遗憾的是，一些基础设施程序可能依赖 PATH 来查找其依赖项，因此修改 PATH 有时可能导致问题（若遇到这种情况，请提交 issue）。例如，若希望学生运行 python 时使用挑战镜像的 python（带有特定的挑战 python 依赖），可将 /run/challenge/bin/python 符号链接到所需的程序版本。

PATH 的设置为 PATH="/run/challenge/bin:/run/dojo/bin:$PATH"。默认情况下，若不存在 /run/challenge/bin 目录，会自动从 /challenge/bin 创建符号链接。因此，也可选择将符号链接放在 /challenge/bin 目录；但 /challenge 接口已过时，长期来看应优先使用 /run/challenge/bin。

有关 PATH 的更多信息，请参阅《8.3 其他环境变量》（https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap08.html#tag_08_03）。

五、平台工作区要求

目前尚无完美方法整合满足平台、挑战和用户精确需求的文件系统，但仍尽力实现。

平台完全控制以下目录：

/run/workspace
/run/dojo
/run/current-system
/nix

用户完全拥有以下目录：

/home/hacker

挑战拥有其他所有目录，但需遵循以下约束和共识：

平台将确保 /tmp 存在，权限为 root:root 01777。
平台将控制 /etc/passwd 和 /etc/group 中 hacker（UID 1000）和 root（UID 0）用户的信息，权限为 root:root 0644。
/bin/sh 必须符合 POSIX 标准；若不存在，平台将把 /bin/sh 符号链接到 /run/dojo/bin/sh。
/usr/bin/env 必须符合 POSIX 标准；若不存在，平台将把 /usr/bin/env 符号链接到 /run/dojo/bin/env。
平台可能会自动使用各种配置文件；例如，用户的默认 shell /run/dojo/bin/bash 会尝试使用 /etc/bashrc[^1]、/etc/inputrc 和 /etc/nsswitch.conf。

[^1]: 这与 ubuntu:24.04 使用 /etc/bash.basrch 不同。
