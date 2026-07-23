# pwn.hust.college 平台用户使用指南

## 一、 概述

pwn.hust.college 平台用于实践网络空间安全，旨在最小化学生和教师的障碍。道馆借鉴了 Capture The Flag（CTF）社区的见解和灵感，该社区开创了使用实践挑战来教授网络空间安全概念的方式。道馆通过提供一个预配置的、功能齐全的学习环境来改进现有平台的可访问性和易用性，该环境可以从任何设备的浏览器进行访问。学生能够在浏览器中编写代码、与 shell 交互、探索复杂的网络配置、调试进程和内核模块等。教师可以轻松地将道馆部署到自己的服务器上，使用单个 docker 运行命令，并通过 git 仓库来管理挑战关卡。

道馆巧妙地融入了神奇宝贝世界的元素，将各类题目按照课程知识点知识点分门别类，安置于独特的道馆之中。每一个道馆都由具有独特能力的宝可梦充当挑战关卡守护者，尊重了原作的设定。学生们化身为一个个青年神奇宝贝训练家，追随着小智的步伐，踏上夺取勋章的征程，挑战各个道馆，攻克难关。对于成功通过道馆考验的学生，本网站将颁发与游戏中一比一的纪念徽章，这一独特设计将极大地提升了同学们的学习热情与动力，为成为一位 Master of PWN（神奇宝贝大师）而不断奋斗。

## 1.1 背景

软件开发领域利用容器化技术确保环境可移植性和可重现性,开发者也采用容器化开发环境标准化工作流程。教育领域效仿此做法,集成容器化学习环境,为初学者提供预配置环境,避免环境配置阻碍学习。网络空间安全等领域亟需此类创新教学模式,解决实操经验缺乏及师资短缺问题。

本指南将介绍“神奇宝贝道馆“平台，这是一个专为网络空间安全设计的平台，灵感来源于广受欢迎的网络安全竞赛形式——夺旗赛(Capture The Flag， CTF)。CTF 竞赛已被证明是教授网络空间安全概念的有效方法，学生通过解决一系列富有挑战性的任务来获取**“****旗帜****(flag)”**，以此来验证自己掌握了新技能。“道馆”平台让学生可以直接在浏览器中访问预配置的学习环境，进行代码编写、网络配置探索、进程调试等实践活动，无需在本地机器上进行繁琐的环境配置。这种沉浸式的学习体验将极大地提高学生的学习兴趣和效率。

本文将在接下来的章节中详细阐述**道馆**平台的设计理念、系统架构和实现细节，展示其如何应用容器化技术，为网络空间安全教育带来全新的学习模式。通过**道馆**平台，我们希望为网络空间安全人才的培养提供一个高效、灵活、有趣的学习环境，助力网络空间安全教育事业的发展。

## 1.2 总体设计

在设计“道馆”平台时，我们的首要任务是最大限度地简化学生访问挑战关卡和教师部署挑战关卡的难度。在这个过程中，我们利用了许多现有的技术，着重于实现平滑集成。“道馆“从网络空间安全竞赛，特别是夺旗赛(Capture The Flag， CTF)中汲取灵感，并扩展这些理念以实现我们的目标：让更多人能够接受网络空间安全教育。

### 1.2.1  挑战环境

"道馆"显著扩展了 CTFd 框架的功能，CTFd 是一个流行的平台，用于举办简单的一次性"Capture The Flag" (CTF)安全竞赛。CTFd 处理用户账户管理、追踪答案提交，并提供列出挑战关卡和展示成绩排行榜的基础网页界面。"道馆"在此基础上增加了功能，创造了一个为学生提供持续、全面学习体验的环境。

在标准的 CTF 竞赛中，参与者通常会得到一个可下载的挑战程序，或是如何与远程运行的挑战关卡进行通信的指示(例如，使用 `nc` 命令)。我们在此基础上进行扩展，为学生提供了一个专用的容器化环境。学生可以在准备好解决挑战关卡时启动这个环境，一旦启动，容器中就包含了挑战本身和任何其他必要的文件。此外，我们也开源了我们的挑战关卡题目，有时还会通过开放题目源码来降低学生负担。

### 1.2.2 工作环境

#### 广泛的工具支持

学生在托管挑战关卡的同一环境中完成实践。这些容器预先配置了必要的安全工具。目前，“道馆”的默认挑战环境配备了 ipython、tmux、strace、gdb、pwntools、pwndbg、gef、radare2、ghidra、wireshark、nmap、scapy、requests、curl 等多种工具。我们的目标是让学生能够直接在“道馆“环境中执行解决挑战关卡的每个步骤——漏洞发现、利用代码实现和调试。

“道馆”平台通过提供一个集成了各种常用工具的统一环境，免去了学生在本地机器上安装和配置工具的繁琐过程，让他们可以专注于学习网络空间安全技能本身。同时，这也确保了学生在解决挑战关卡时拥有一致的工作环境，减少了由于环境差异导致的问题，提高了学习效率。

### 1.2.3 环境访问

学生可通过三种方式访问他们的挑战环境。此外，我们还会讲述一些“道馆”平台的特色。

#### SSH 访问

第一种方式是通过在道馆网页界面上传公钥，利用 SSH 进入挑战关卡，并使用 SCP 进行文件传输。

#### Visual Studio Code

第二种方式是通过道馆内运行的 Visual Studio Code，提供文本编辑器（包括文件上传和下载）、命令行终端、文件管理和插件接口。

#### 浏览器内桌面环境

第三种方式是浏览器内桌面环境，为学生提供在浏览器内运行任意图形界面程序的能力，适用于软件逆向等高级安全课程。这种全浏览器体验消除了硬件进入障碍，适用于笔记本电脑、平板电脑或其他移动设备。

#### 特权模式

此外，道馆还提供特权模式。在此模式下，学生在类似标准模式的环境中工作，但拥有 sudo 权限和占位符标志。通过此根访问权限，学生可全面分析和调试依赖标志访问的挑战程序，同时不泄露实际 flag，确保挑战完整性。

#### 持久化家目录

另外，为了在切换 challenge 和挑战时提高可用性，道馆在所有挑战环境中保持挑战环境的家目录持久化。这种持久化家目录的设计至关重要，因为它使学生能够存储他们之前的解决方案（用于参考和扩展）以及自定义脚本和工具。关键的是，家目录是以 `nosuid` 选项挂载的，这阻止了学生在不同环境之间传递 root-owned SUID 二进制文件。

### 1.2.4 挑战虚拟化

尽管 Docker 在许多挑战场景下表现出色，但它并非总能提供某些特定挑战所需的全部功能。例如，标准的非特权容器无法任意管理网络资源，这限制了网络空间安全教育的范围。为了解决这些限制，道馆提供了两种解决方案:用户命名空间和虚拟机。

#### 用户命名空间

道馆支持嵌套命名空间虚拟化，使挑战能够创建任意网络拓扑、进程隔离和权限模型。这需要道馆修改 Docker 的 seccomp 过滤器，允许相关系统调用(如 unshare)，并创建用户命名空间，从而将必要的 Linux 功能授予挑战关卡，同时不影响道馆系统的整体安全。

#### 虚拟机

对于无法仅通过命名空间虚拟化解决的挑战类型，道馆支持在用户容器内使用虚拟机和系统模拟器。我们的虚拟机实现能够透明地与容器共享文件系统，这意味着文件在容器和虚拟机之间自动共享，且一个环境中的修改将立即反映在另一个环境中。这种方式消除了将解决方案和调试代码传输到传统最小化环境(运行在易受攻击的内核中)的障碍。

### 1.2.5 教师功能

#### 环境共享

道馆拥有一个独特的双向信息共享功能。教师可以将自己的桌面环境广播给学生，让他们实时观察教师的操作。反之，教师也可以访问并与学生的桌面环境互动，或通过 SSH 连接到学生的环境中。通过这种方式，教师能够直接了解学生解决问题的思路，无论是实时观察还是事后检查他们的解决方案脚本。这在混合或在线课程中尤为实用，可以更好地指导学生攻克复杂问题。值得注意的是，教师访问学生环境的权限在课程开始时均会向学生明确告知。

#### 反作弊机制

为防止学生共享挑战标志，道馆为每个用户和挑战生成了单独加密的标志。这使得道馆能够验证某个标志是否对特定用户和挑战是正确的，并自动检测学生间的标志共享行为。此外，教师可以为同一挑战指定多个细微变体，每个学生将被随机分配其中一个，从而增加了学生间解决方案共享的难度，要求他们开发出专门针对自身挑战的解决方案。

#### 自动评分

为方便教师管理大规模学生课程，道馆支持自动评分功能。它能导出学生在每个挑战上的详细进度统计数据，供教师确定成绩并了解学生的时间投入情况。结合查看学生桌面和访问学生文件的能力，教师可以轻松掌握班级整体进度，识别遇到困难的学生以及发现作弊行为。

总的来说，道馆的设计理念是提供一个全面且易于使用的平台，不仅能提高学生的学习效率，还能让教师更高效地管理和指导学生。通过这些精心设计的功能，使之更加高效且易于接受和使用。

![image](static/TI7hbOlhDoNy8Jxgv6pcROaLn5e.png)

## 二、教师手册

## 2.1 道馆编写

道馆是 [pwn.hust.college](https://pwn.cse.hust.edu.cn/) 平台的核心概念，同学们（神奇宝贝训练家）可以通过道馆挑战学习软件安全课程的核心概念与实践各种知识点，并且获得道馆徽章。教师们可参考 [example-dojo](https://github.com/hust-open-atom-club/example-dojo)，自行编写自己的道馆及挑战关卡。

### 2.1.1 字段解释

#### **Dojo**

道馆平台的顶层对象是 `Dojo`，它由六个属性组成：

- `id`：**必需**。Dojo 的唯一标识符。
- `name`：**必需**。Dojo 的显示名称。
- `type`：**可选**。此字段可以取值 `welcome`、`elementary`、`intermediate`、`advanced`、`course`、`topic`、`example`、`hidden`。`welcome` 将该道馆放在**入门篇**部分，`elementary` 将该道馆放在**初级篇**部分，`intermediate` 将该道馆放在**中级篇**部分，`advanced` 将该道馆放在**高级篇**部分。`course` 将其放在**课程**部分，`topic` 将该道馆放在**主题**部分，`hidden` 意味着道馆不会被列出（但仍然可以访问）。如果省略 `type` 字段或包含除这八个之外的值，则道馆将出现在**更多**部分。
- `password`：**可选**。用户加入道馆需要输入的密码。如果省略，则任何人都可以加入道馆。
- `modules`：**必需**。模块对象的数组，`modules` 的参数，参考 **M****odule** 部分。
- `award`：**可选**。子参数为 `belt`，`emoji`，内容为 svg/png 文件名，`belt` 和 `emoji` 的文件存放路径均为：`/dojo_theme/static/img/dojo/`。

使用样例：

```yaml
id: your_dojo_id
name: your_dojo_name
type: welcome/course/topic/example/hidden/elementary/intermediate/advanced
award:
  belt: PokeBall
  emoji: PokeBall
modules:
  id: your_module_id
  icon: Pikachu
```

#### **Module**

`modules` 数组中的每个 `Module` 对象都包含以下属性：

- `id`：**必需**。模块的唯一标识符。
- `name`：**必需**。模块的显示名称。
- `challenges`：**必需**。`challenge` 对象的数组，具体子参数参考 challenge 部分。
- `resources`：**可选**。`resources` 参考 resources 的部分。
- `icon`：**可选**。关于模块的图片信息。`icon` 的文件存放路径为：`/dojo_theme/static/img/dojo/`。

使用样例

```yaml
name: your_module_name
challenges:
  id: vscode
  name: your_challenge_name
  level: 1
resources:
  name: your_resources_name
  type: lecture
  video: “829819163“
  playlist: “BV1bu4y197Zj“
  
  name: “未包含的功能介绍“
  type: markdown
  content: |
    your_content_text
```

#### **Challenge**

`challenges` 数组的每个 `Challenge` 对象都包含以下属性：

- `id`：**必需**。挑战的唯一标识符。
- `name`：**必需**。挑战的显示名称。
- `icon`: **可选**。关于挑战的图片信息。`icon` 的文件存放路径为：`/dojo_theme/static/img/dojo/`。
- `level`：**可选**。关于 `challenge` 的等级显示。

使用样例：

```yaml
challenges:
  id: level-0-0
  name: your_challenge_name
  level: 1
```

#### **resources**

`resources` 数组中包含以下属性：

- `name`：**必需**。资源的显示名称。
- `type`：**必需**。可选项为 `lecture` / `markdown` `lecture` 则为视频报告内容，`markdown` 则为纯文本内容。
- `video`：**可选**。仅支持 `bilibili`，内容为 `cid`，如果选择 `video`，则需要和 `playlist` 对应使用，`playlist` 为 `BV` 号。
- `playlist`：**可选**。仅支持 `bilibili`，内容为 `BV` 号，如果选择 playlist，则需要和 video 对应使用，video 为 cid。
- `content`：**可选**。内容为显示的文字内容。
- `slides`：**可选**。仅支持 github.io 的 page 页面，关于资源的 pdf 信息。内容为 pdf 的文件名。

使用样例

```yaml
resources:
  name: your_resources_name
  type: lecture
  video: “438064585“
  playlist: “BV1mj411M7NZ“
  slides: “SetUID“
  
  name: your_resources_name
  type: markdown
  content: |
```

## 2.2 道馆添加

1. 点击最上方导航栏中的“道馆”，然后在页面最下方，点击如下所示添加道馆的图标。

![image](static/Z4a7bHIdXotSYzx97NRcFDBCnIb.png)

1. 根据道馆仓库所在的托管平台，选择 Github 或 Gitee，并输入相应的仓库路径，如 hust-open-atom-club/example-dojo。若道馆仓库是开源的，即可点击 Create 按钮，创建道馆及其挑战关卡。反之，则需要在道馆仓库中添加如图所示的部署秘钥，详见 Github 或 Gitee 部署秘钥文档。

![image](static/NESzbol3HoOzZ4xeUysc9uNTnbb.png)

1. 创建成功之后，即可看见下图所示。同时，在道馆列表中看到该道馆。

![image](static/BkzWbyEcjo2XEdxbt8IciqWKnPh.png)

![image](static/WWIJbZTsRoPMPlxEaCycFdh0noc.png)

## 2.3 道馆更新

以管理员账号进入刚创建好的 Example 道馆，并点击进入管理员界面，

![image](static/IlNzbirx7oIlXnxwupFcQud8nah.png)

在管理员界面中，你可以通过“更新”按钮，使用最新的代码仓库。代码仓库可以通过代码提交的方式不断进行更新和迭代。

![image](static/F2sxb3c9BouF61xM1CIccquynWd.png)

![image](static/Bo3xbsbt1oUqpbxnD8ecWRmanKb.png)

## 三、学生手册

欢迎来到[pwn.hust.college](https://pwn.hust.college/) ，一个基于神奇宝贝动画设计的趣味教育平台。为助您获取 flag，成功闯关，下面将介绍道馆的注册、登录、使用细则，以及 vscode 工作空间，图形桌面工作空间，SSH 这三种与挑战关卡互动的方式。

## 3.1 道馆

### 3.1.1 注册以及登录

我们平台接入了智慧华中大统一身份认证,因此并不需要注册账号，可以直接进行登录。

我们点击右上角统一身份认证，跳转到[智慧华中大](https://pass.hust.edu.cn/cas/login)。

![image](static/ABgvbYoMvoOmwWxZKFic2AOynwf.png)

输入自己的账号密码之后，会自动跳转 `DOJO`，即可成功登录平台。

![image](static/WF8tbZs8uoHHHSxYmgxcS8Esnju.png)

![image](static/QtFmb1ZceoOYhmxdRmFczeNenme.png)

### 3.1.2  道馆使用细则

可以看到道馆有入门篇、初级篇、中级篇、高级篇，难度依次递增，只有完成入门篇 8 个关卡，拿到徽章才能进入后续篇章的学习。我们以入门篇为例说明道馆的使用细则：

点击**入门篇**，可以看到道馆简介，道馆奖项，道馆状态，道馆模块以及道馆排名，点击道馆模块。

![image](static/T4mqbgLRnoY6VHxWjfdck3wSnQc.png)

进入道馆模块后可以看到篇章内容简介，课程讲解与资料学习，和挑战关卡。完成每个挑战关卡后都可以获得相应的 flag，全部完成后即可获得徽章。

开始挑战，点击名为工作空间的第一关：

![image](static/Ba3Ybj3vSoxjEmx3UG8czk3Tnvc.png)

点击 Start 按钮，当出现下方蓝色提示时意味着当前挑战关卡已经启动。

![image](static/BPZZb2ybgod2DyxQkAycjuZAnvf.png)

## 3.2 VSCode 工作空间

### 3.2.1 工作空间

根据简介第一关将教你如何让使用 Visual Studio Code 工作空间，点击上方的工作空间或者下方蓝色提示中的 Vscode Workspace 均可进入。

![image](static/RfgAbpzWoo5pGDx2NXkc5yiLnpc.png)

进入工作空间后，根据提示要运行路径为/challenge/solve 的挑战程序。

如果当前处在/home 目录中，请切换文件夹至/challenge 目录中。

![image](static/HwM8bwP0bo1MCdx1owGcIirfnSf.png)

填写/challenge，点击 ok 按钮切换。

![image](static/PrdMbU5NcoViozx7TJucI2vEn9f.png)

切换到/challenge 目录下可以看到 DESCRIPTION 里面的提示以及我们需要运行的程序 solve，右键 solve 打开终端。

![image](static/TwC8b8fV2o0vQIxmqMTcb0Tbnic.png)

输入命令。/solve 运行可执行程序，可以获取 flag，复制 flag。

![image](static/XGnxbIB7JoRBwmxHjmLcA1VsnsA.png)

回到道馆，将 flag 粘贴至浅绿色框内，然后点击右侧 submit 提交，如果出现 correct 提示并且旗帜变成绿色说明 flag 正确，闯关成功。（注意：不同同学、每次挑战的 flag 都不一样）

![image](static/HNvDbIDNJoByrAx86mOcQ8vgn5c.png)

### 3.2.2 读取 flag

运行第四关，打开工作空间，根据提示/flag 文件需要 root 用户才能访问。

![image](static/OcQXb1vLdonYH9xXdCrc5GxGnhe.png)

先运行可执行文件让所有人都能读取 flag，使用命令 cat /flag 读取 flag。

![image](static/EhhgbbIBNozo8WxILaLcVp32nEd.png)

回到道馆，将 flag 粘贴至浅绿色框内，然后点击右侧 submit 提交，如果出现 correct 提示并且旗帜变成绿色说明 flag 正确，闯关成功。

### 3.2.3 使用练习模式

第五关是使用练习模式获取 sudo 权限读取密钥，然后再在正常模式下运行可执行文件输入密钥，获取 flag。点击 practice 练习模式按钮开启第四关，进入 VSCode 工作空间。

![image](static/OZhYbdgIeo5OdPxaU3hcuRMWnJd.png)

用命令 sudo cat 。/secret 来读取密钥

![image](static/M3Npb8Gexo5UhZxcQtYcqFQKn2c.png)

回到道馆，点击 start 正常模式，进入工作空间，运行可执行文件，输入密钥，获取 flag。

![image](static/SXBbbCkRDo5MSaxTI8ScgqQVn0e.png)

回到道馆，将 flag 粘贴至浅绿色框内，然后点击右侧 submit 提交，如果出现 correct 提示并且旗帜变成绿色说明 flag 正确，闯关成功。

### 3.2.4 持久家目录

在本平台中，你的家目录在挑战关卡之间是保持不变的，可以共享的。 这意味着你可以在多个挑战关卡中使用它来积累笔记、参考旧解决方案，或者重新运行在练习模式中完善的解决方案来应对非练习模式中的挑战关卡。

可以通过打开文件夹，选择 home/hacker 到家目录，家目录在挑战关卡中保持不变，可在其中新建文件、文件夹，具体操作可以通过第六关第七关验证。

![image](static/HuvsbDPzko0tdbxn7jMcJVfLnhh.png)

![image](static/EciVbgytqo1beqxB8vecmUeunih.png)

## 3.3 图形桌面工作空间

### 3.3.1 桌面

点击 start 按钮开启第二关，点击上方桌面按钮或蓝色提示上的 GUIDesktop 均可进入桌面环境。

![image](static/XJ7EbRzhrouTzMx5FeQcwfFNnKf.png)

进入桌面环境，可以看到 challenge 目录下的 DESCRIPTION 任务描述以及可执行程序 solve，在 challenge 目录下右键打开终端。

![image](static/KBU7brAEroeQ3YxHyQDc38pLnPe.png)

输入命令。/solve 运行可执行程序可以得到 flag 以及将 flag 从桌面平台粘贴到宿主机系统的方法。

![image](static/J5pgb8WtpoXgolxtN4ZcsQpOntg.png)

根据方法打开屏幕左侧的剪切板，勾选 flag 内容，发现剪切板中显示 flag 内容，在剪切板里面复制 flag 内容。

![image](static/UzUAbt1QzoNL5axiAYCcAXvCn0b.png)

回到道馆，将 flag 粘贴至浅绿色框内，然后点击右侧 submit 提交，如果出现 correct 提示并且旗帜变成绿色说明 flag 正确，闯关成功。

### 3.3.2 桌面拷贝

启动第三关桌面拷贝，复制令牌，在/challenge 目录中打开终端，输入指令。/solve 运行可执行程序，获得能从宿主机拷贝到桌面环境中的方法。

![image](static/HvRjb2I6Ho9sMkxd4UHcWUpUnfh.png)

将令牌粘贴至剪贴簿并且复制。

![image](static/CHOhbqrxNozk90xswSrcmkMBnNn.png)

在终端中输入令牌获取 flag，复制 flag 至宿主机参考 3.3.1 的内容。

![image](static/Zn7HbY55DofT05x4maTci6Ycn7d.png)

回到道馆，将 flag 粘贴至浅绿色框内，然后点击右侧 submit 提交，如果出现 correct 提示并且旗帜变成绿色说明 flag 正确，闯关成功。

## 3.4 SSH

### 3.4.1 SSH

点击 start 按钮开启第八关，通过 SSH，用户可以安全地登录远程计算机，并执行命令、传输文件等操作。下面将演示在 win11 终端通过 ssh 成功获取 flag。

打开终端，通过 cd 进入。ssh 文件夹，输入 ssh-keygen -f key（在 win11 终端中，使用空字符串作为参数可能会引起语法错误或不被接受，-N 去掉后输入密码时直接回车表示无密码），生成 key 和 key.pub 公私钥对，通过 cat key.pub 将公钥内容复制出来。

![image](static/HHM1bqcaSokSk6xiA01cxffOnOc.png)

回到道馆点击右上角设置，点击左侧 SSH 公钥。

![image](static/FDTZbMxHTo9ukJxI17AcbXtUnjd.png)

将复制的公钥填入并且点击 update，出现绿色提示说明公钥成功上传。

![image](static/ZoEPbAYvaowUPkxytfvcqTS5n4g.png)

回到 Win11 终端，ssh -i ～/。ssh/key -p 22223 <hacker@pwn.hust.college>，即可连接到挑战关卡容器，切换到 challenge 目录，然后运行挑战程序，获取 flag。

![image](static/Z73VbWoLSoaWTsxfop4cGdHOnpb.png)

最后回到道馆，将 flag 粘贴至浅绿色框内，然后点击右侧 submit 提交，如果出现 correct 提示并且旗帜变成绿色说明 flag 正确，闯关成功。

## 四、管理员手册

平台创建的时候自动创建管理员用户 admin，密码是 admin，进入后请首先点击设置，修改管理员密码。管理员主要负责平台用户的管理和平台自身的管理。

![image](static/P4rtb0q00oux5TxrRc4cPF5Rnse.png)

接下来，我们进入平台和用户管理的界面，点击右上角的管理面板进入。

![image](static/F86Nb4Wf3o39ZjxD34rcQ2V1ncg.png)

进入到下列界面即代表我们进入 admin 的管理界面。

![image](static/OZzhbYiI9oLZ8MxM79lcioLnnqg.png)

## 4.1 用户管理

平台有两种类型的账户：用户和团队。根据配置使用的用户模式，参与者需要注册账户或注册账户并加入团队。平台有两种 “用户模式“：用户模式和团队模式。用户模式决定了参赛选手的注册方式和计分方式。

### 团队模式

如果您将 CTF 设置为团队模式，每支队伍都需要选择一名队长。队长应注册一个团队，然后与队友共享团队密码。队友就可以使用队名和密码加入队伍。

团队成员获得的所有解答、提交、奖励和提示都将归属于团队和个人用户。打个比方，在篮球比赛中，当有人得分时，团队也会得到分数，但我们仍会记录该球员为团队得到了多少分。本平台也是如此。

**重要说明：**

在团队模式下，每个人都应注册自己的用户账户。然后，每个团队中的一人（队长）应注册一个团队账户，并与其他队友共享团队名称和密码。然后，其他成员应使用这些凭证加入团队。单人玩家仍可在团队模式中进行游戏，但仍需注册一个团队。

### 用户模式

在用户模式下，平台允许参与者使用自己的用户账户独自游戏。多名玩家也可共享同一账户一起游戏，但解题和提交的信息都将归属于同一账户，而不是按玩家分类。本平台默认是使用的用户模式。

### 4.1.1 编辑用户

#### 编辑用户信息

管理员可以编辑其他用户的属性，进入管理面板。点击用户选项卡，然后选择要更改的用户。

![image](static/S6RBbYhr9oh1MkxOuTTcylUrnWd.png)

点击 user 图标进行修改用户的个人信息。

![image](static/EqIdbWULFoPy2ixQ2u9cie3ZnHd.png)

弹出一个表单，允许您编辑用户属性

![image](static/NsWzbi7jFoc7gdx0XRCcerCLnGd.png)

#### 编辑用户权限

要将其他用户提升为管理员（或将管理员降级），管理员需要在其管理面板配置文件中更改用户的角色。

1. 点击用户下拉列表

![image](static/Ob9ubEur5ov3XlxNnezcLURInWf.png)

1. 选择所需的用户角色，然后提交以保存更改

![image](static/Wp7ObEVu3o9PdmxuAQ1cyR8tnR2.png)

### 4.1.2 新增用户

通常情况下，您需要让用户通过公共注册页面自行注册。不过，管理员也可以在管理面板中添加新用户，并通过电子邮件将验证发送给新用户。要手动创建新用户，请使用以下说明：

1. 点击右上角的管理按钮，进入管理面板
2. 点击用户选项卡，然后点击顶部的加号图标

![image](static/DVL4biucioFlIBxmxb4cSUYtnqe.png)

1. 填写新用户的必要信息。必要时更改用户的角色，将其晋升为管理员用户

![image](static/AhuCbBfR2oyZ13xizsTctbnan9c.png)

1. 单击提交按钮创建用户

#### 添加自定义字段

用下拉菜单替换自定义字段输入：

1. 进入至 “自定义字段 “配置，该配置位于 “管理面板“>“配置“>“自定义字段“。
2. 添加所需的自定义字段：

   - 选择文本字段作为字段类型。
   - 确保它是注册时的状态，并且确认普通用户是否可以更改。

![image](static/QPytbgFbOomzuexBFswc1w9znC6.png)

1. 点击 save，即可完成字段添加。

![image](static/SYaubQdHboYMRTxJErLc82BvnAd.png)

## 4.2 平台管理

### 4.2.1 主题管理

#### 切换主题

所有在 CTFd 实例都有预制主题供您使用，或者使用自行编写的主题风格。

1. 首先进入管理界面，点击 config

![image](static/K6GtbXVUYo7Ihxx2BhlcSqQQnRg.png)

1. 选择合适的 Theme，然后点击 Update 即可完成主题更换。

![image](static/ZkFnbeSoqok1cCxFXwLcylhRn5e.png)

### 4.2.2 配置管理

#### 更改 “Powered by “页脚

大多数底部都有一个页脚，显示一个指向 [https://ctfd.io/](https://ctfd.io/) 的链接，并带有 “复刻自 pwn.college，并由 CTFd 提供支持！“字样。

此文本/链接不可直接自定义。不过，如果您确实希望自定义，有两个选项。

1. 您可以创建一个带有特定文本和链接的新主题
2. 使用主题页脚或主题页眉动态更改页脚内容

本教程的其余部分将重点介绍后一种方法

#### 使用主题页脚

CTFd 支持主题页眉/主题页脚配置，允许管理员添加自定义超文本标记语言/JS/CSS 来自定义其 CTFd 实例的外观。

使用主题页脚，我们可以插入一些 JavaScript 来动态替换页脚的文本和链接：

```html
<script>
  document.querySelector(“footer a“).innerText = “Powered by Magic Beans“;
  document
    .querySelector(“footer a“)
    .setAttribute(“href“， “https://example.com“);
</script>
```

上面的片段会将页脚链接的文本更改为“Powered by Magic Beans”，并将链接更改为 example.com。在使用它们之前，请务必适当更改这些值！

#### 完全删除页脚

要删除页脚，我们可以使用放置在“主题页脚”中的以下 CSS 来隐藏页脚内容

```html
<style>
  footer {
    visibility: hidden;
  }
</style>
```

![image](static/NdpYbBa8AowXrVxbBf7cVuGPnJf.png)

#### 导入题目备份实例

要导入 CTFd 实例，您必须是管理员。

1. 点击右上角的管理按钮，进入管理面板。
2. 单击右上角的 “配置 “选项卡
3. 单击 “备份 “选项卡，然后选择 “导入 “面板
4. 上传备份并单击 “导入 “后，页面将重新加载。

![image](static/RWGzbM3U1oBy8jxnFK9cSsGfn7t.png)

#### 重制平台

根据您的选择，这将删除所有用户、团队和提交的内容！重置前请务必小心并备份您的 CTFd 实例！

如果您想重置 CTFd 实例并移除所有用户、团队和提交的内容，请使用以下说明：

![image](static/UtCkbIOowomRBIxBoNzc5Jvxnfb.png)

![image](static/QbmkbawYXoTvqfx5H7bc5Vi3ncf.png)

#### 白名单电子邮件

CTFd 支持电子邮件域白名单。只有管理员才能从账户电子邮件白名单中添加或删除域。

![image](static/TrJLbWnl9oH9y7xiWolcyPUcndb.png)

要将域名添加到白名单：

1. 进入管理面板下的配置页面，选择 “账户 “选项卡。
2. 第一个选项是 “账户电子邮件白名单“，输入所有可用于比赛的域名，用逗号分隔。留空将允许用户使用任何电子邮件注册。

#### Server 邮箱配置

点击 config，然后打开 Email，即可配置相关邮件格式。

![image](static/GqLKblD5jouPAkxIReScX0IGndc.png)

在 Email Server 界面

1. 输入使用邮件的用户名，发送 smtp 的 server 服务器，以及 server port。
2. 选择邮箱的用户名密码，并填充。
3. 选择 TLS/SSL 加密 或者根据情况选择 STARTTLS。
4. 点击 Update 更新即可。

**请注意，公网部署的平台不要使用该功能，避免邮箱密码被泄露！**

![image](static/QmV9bX7mrocUbZx98wcccs2Anic.png)

### 4.2.3 页面管理

该界面可以修改主页，或者新增自己想要的网页。

#### 修改主页

1. 我们点击页面管理，选择 index 路由。

![image](static/GNyBbkPZKoKHALxgKmgcVCHEngJ.png)

1. 将 index 界面修改过后，我们点击 save，主页即可刷新。

![image](static/ZfDtbNBPsoQR9exSlwLcijmRnCh.png)

#### 删除界面

点击红色删除图标，即可删除界面。

![image](static/Rgv3b74LRoC4GvxSNe1czdnDn5b.png)

#### 新增界面

1. 点击界面中间的 pages 添加。

![image](static/Af6ib8ATuox8MIxkSDUcK3OXnih.png)

1. 输入新页面的路由，信息，是否可见，是否需要鉴权等信息，点击 save 即可保存一个新的界面

![image](static/DS1wbGtc2oD0hIx8xwscjxDMnQc.png)

### 4.2.4 道馆管理

点击 道馆，即可管理当前的所有道馆。

![image](static/RIlsbU8P8od90qxW8Mpc8wwqn0e.png)

点击具体的道馆，将跳转到道馆页面进行管理。

![image](static/Jsusbjg6ZoS7sKxJP0acZ0bWndc.png)

### 4.2.5 道馆全局可见

新添加的道馆默认均为个人可见，只有平台管理员才能权限在道馆管理界面中点击 Make This Dojo Official，使所有人可见。其他人是看不到该按钮。

![image](static/KhRsb1i9VomzPDxEH7zcbrkan1d.png)

### 4.2.6 备份导出

CTFd 可将所有实例数据导出为 zip 文件，以便存档。可将此压缩文件导回 CTFd，以恢复导出的实例。在销毁托管 CTFd 实例时，请务必创建导出文件作为备份。

1. 要创建 CTFd 导出，您必须是管理员。
2. 点击右上角的管理员按钮，进入管理面板。
3. 单击右上角的 “配置 “选项卡
4. 单击 “备份 “选项卡

![image](static/BOK9bBZ3Yo5H5dxic28cp0pfn2d.png)

1. 您可以使用 “导出 “选项卡导出整个实例，也可以使用 “下载 CSV “选项卡导出特定数据，包括用户数据和自定义字段，以便进行分析。
2. 单击 “导出“，您将下载实例的 zip 文件。该压缩文件包含实例的 json 文件。

![image](static/U05rbhylMoINapxhsJdcTH5Cnrf.png)
