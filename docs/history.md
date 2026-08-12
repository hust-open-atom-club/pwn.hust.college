# 历史

## 平台起源与发展背景

### 国外开源项目基础

pwn.hust.college 平台的技术原型可追溯至 2018 年美国亚利桑那州立大学（ASU）开发的 pwn.college 项目。当时 ASU 的教学团队面临“如何在一学期内培养百名学生成为实战型网络安全人才”的挑战。基于 CTF 竞赛经验，他们以“边做边学”为理念，开发了首个基于 netcat 的简易交互环境，并注册域名 pwn.college，逐步演进为支持浏览器操作的 DOJO 架构。该项目在 SIGCSE 2024 会议上发表两篇学术论文，奠定了“教育优先的 CTF 挑战”模式的理论基础。

### 国内本土化需求驱动

随着网络空间安全教育在国内的普及，现有平台存在两大痛点：

1. **技术依赖国外**：多数实践平台基于 x86 架构与国外操作系统，缺乏对国产硬件架构（如 ARM）的支持；
2. **教学模式单一**：理论与实践脱节，学生参与度有限。

为此，华中科技大学网络空间安全学院以“未知攻焉知防”“实践出真知”“寓教于乐”为理念，在 pwn.college 开源项目基础上，于 2023 年开发了 pwn.hust.college 平台。平台围绕“攻防实践、闯关进阶、角色沉浸”组织教学路径，并以国产 ARM 架构与 Linux 操作系统适配、pwn.hust.college 实践教育引擎、软件安全 / 系统安全课程和开源实践人才培养体系构成分层支撑，为平台后续发展提供了基础。

## 平台发展关键节点

### 2023 年：初期上线与课程验证

2023 年，平台完成初期建设并进入课程试点阶段，重点验证容器化挑战环境、游戏化道馆设计和本土化适配在教学场景中的可行性。

- **核心功能**：首次实现 Docker 容器化挑战环境，集成 Ghidra、radare2、pwntools 等工具，采用《宝可梦》“道馆”模式设计 87 个基础挑战（如缓冲区溢出、整数溢出），支持 x86 与 ARM 架构。
- **使用文档公开化**：俱乐部编写推文《pwn.hust.college 食用指南》，对 pwn.hust.college 平台访问、账号使用、关卡练习等流程进行了面向新用户的介绍，降低了初学者进入平台的门槛。[^guide]
- **视频教程发布**：2023 年 8 月 15 日，B 站视频《pwn.hust.college 平台使用》发布，通过演示形式介绍平台使用流程，为课程学生和社群学习者提供了更直观的入门材料。[^bilibili-usage]
- **教学应用**：在“软件安全”课程中试点，吸引 200 余名学生参与，验证了游戏化教学的有效性。
- **国产化初探**：初步适配国产 ARM 架构，提供 Gitee 代码托管支持。

### 2024 年：功能升级、规模扩展与公开传播

2024 年，平台在挑战内容、统一认证、课程覆盖、国产化适配和社区传播等方面继续扩展，逐步从课程试点平台走向更稳定的教学与社群实践平台。

- **技术迭代**：
  - 引入 QEMU 技术支持内核漏洞挑战，扩展至 255 个梯度化挑战任务；
  - 接入华中科技大学统一身份认证系统，实现与本科课程的无缝对接。
  - 在 x86 与 ARM 架构支持基础上，引入 LoongArch 支持，并探索以 openEuler 作为挑战环境基底。

- **教学成效**：覆盖“软件安全”（2023 - 2024 学年）与“系统安全”（2024 学年）课程，参与学生超 500 人；平台累计接收学生解题提交 9043 次，总体正确率达 84.08%；2023 学年课程满意度调查显示，77 名学生平均评分 4.5/5 分，64.9% 给出满分；学生提交 PR（代码贡献）43 条，推动平台迭代优化，形成“取之开源，用之开源”的生态。

- **公开传播**：俱乐部发布推文《来 pwn.hust.college 开启一场 CTF 冒险吧！》围绕 CTF 实践、游戏化关卡和网络空间安全学习路径介绍平台，帮助社群成员理解平台的教学定位。[^ctf-adventure]
- **线下社区展示**：WHLUG 相关活动回顾中介绍了 pwn.hust.college 平台，强调其由华中科技大学网络空间安全学院白帽黑客团队创建，采用宝可梦道馆式关卡设计，覆盖平台食用指南、pwntools 使用、缓冲区溢出等内容。[^whlug]

### 2025 年：论文发表、成果申报与项目沉淀

进入 2025 年后，pwn.hust.college 的发展重点从单一平台建设转向持续运营、课程材料沉淀、论文发表和开源项目化维护：

- **道馆内容沉淀**：围绕 `welcome-dojo`、`pwntools-dojo`、`example-dojo`、`official-dojos` 等仓库，平台逐步形成可复用的官方道馆、样例道馆和课程道馆体系。
- **论文与材料沉淀**：论文《pwn.hust.college：基于游戏通关模式的开源安全教育平台》系统梳理了平台基于 Docker 与 QEMU 的挑战环境、浏览器 / SSH / VNC 访问方式、Ghidra、radare2、pwntools 工具链、KOOK 交流渠道和自动评分反馈等平台设计。[^platform-paper]
- **开源共建深化**：成果申报材料显示，平台通过“使用-贡献-共建”机制累计接收 PR 提交 59 次、合并 47 次，其中 36 次来自开源实习项目，并推动累计新增 114 个实战挑战关卡。
- **新版教程发布**：2025 年 7 月 23 日，B 站视频《最新版 pwn.hust.college 平台使用说明》发布，对平台使用流程进行更新说明，反映平台在课程和社群使用中的持续迭代。[^bilibili-usage-2025]

### 2026 年：智能体工具与持续维护

截至 2026 年，pwn.hust.college 已经进入独立维护和生态延伸阶段：

- **智能体工具延伸**：围绕 pwn.hust.college 的辅助工具和智能体能力开始开源化，平台生态从课程平台扩展到学习辅助工具。[^pwnhustcollege-skill]
- **教学成果认可**：俱乐部发布推文《喜报 | 基于俱乐部项目 pwn.hust.college 开发的教育平台获华中科技大学教学成果二等奖》记录了平台从课程工具进一步沉淀为教学成果的阶段性认可。[^teaching-award]
- **平台工程维护**：继续围绕 HUST SSO、KOOK/Discord 集成、Prometheus/Grafana 监控、课程与成绩功能、智能体辅助工具和 Open WebUI 移除等方向迭代，逐步形成面向华科教学与开源俱乐部运营的独立维护版本。
- **持续建设方向**：后续平台建设应继续围绕课程稳定性、挑战环境可维护性、道馆内容复用、教学数据反馈和智能体辅助学习展开，使 pwn.hust.college 从课程支撑平台进一步发展为网络空间安全实践教学基础设施。

从 2023 年课程试点，到 2024 年公开传播和规模化课程应用，再到 2025 年论文发表、成果申报与 2026 年智能体工具延伸和教学成果认可，pwn.hust.college 的发展路径已经从“课程内实验平台”逐步扩展为“课程教学、开源协作、社区传播和工具生态”共同驱动的实践平台。

## References

[^ctf-adventure]: [来 pwn.hust.college 开启一场 CTF 冒险吧！](https://mp.weixin.qq.com/s?__biz=MzkxMzUzMzIxMw==&mid=2247484179&idx=1&sn=e0002ce4ac3f0fac1a4c9b6168a4f819&scene=27#wechat_redirect)
[^guide]: [pwn.hust.college 食用指南](https://mp.weixin.qq.com/s/jasbF0Ml1xzhVutoUlC53Q)
[^bilibili-usage]: [pwn.hust.college 平台使用](https://www.bilibili.com/video/BV1bu4y197Zj/)
[^whlug]: [武汉 LUG 活动回顾 | 4 大技术分享！干货满满，热闹非凡！](https://www.oschina.net/comment/news/294652)
[^platform-paper]: [pwn.hust.college：基于游戏通关模式的开源安全教育平台](pwn-hust-college-security-education-platform.pdf)
[^teaching-award]: [喜报 | 基于俱乐部项目 pwn.hust.college 开发的教育平台获华中科技大学教学成果二等奖](https://mp.weixin.qq.com/s/lhl-2_8ntuztbd_G66knPw)
[^bilibili-usage-2025]: [最新版 pwn.hust.college 平台使用说明](https://www.bilibili.com/video/BV1wD8czAEqP/)
[^pwnhustcollege-skill]: [新项目上线｜让 AI 帮你打 pwn 关卡：pwnhustcollege_skill 开源啦](https://mp.weixin.qq.com/s/6M9yTLo2uotx-0__84Z6RA)
