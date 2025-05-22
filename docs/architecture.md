# TODO

此处可参考上游进行编写！

The pwn.hust.college infrastructure allows users the ability to "start" challenges, which spins up a private docker container for that user.
This docker container will have the associated challenge binary injected into the container as root-suid, as well as the flag to be submitted as readable only by the the root user.
Users can enter this container via vscode in the browser ([code-server](https://github.com/cdr/code-server)), via XFCE desktop environment in the browser([noVNC](https://github.com/novnc/noVNC)), via `ssh` by supplying a public ssh key in their profile settings.
The associated challenge binary may be either global, which means all users will get the same binary, or instanced, which means that different users will receive different variants of the same challenge.