# 开发

## 一、开发准备
在开始pwn.hust.college平台的开发工作前，请务必阅读[架构文档](./architecture.md)和[部署文档](./deployment.md)，以全面了解平台的技术架构、部署流程以及国产化特色等关键信息，为后续开发工作奠定基础。

## 1.1 快速开发环境搭建
为快速搭建适用于pwn.hust.college平台的开发环境，可执行以下命令，这些命令将构建平台镜像并在一个独立的容器中运行，同时兼顾平台的国产化技术特性：
```sh
BRANCH="master"  # 若为PR，可使用"pull/N/head"
TAG="dev-$(printf '%s' "$BRANCH" | tr '/' '-' | tr -c '[:alnum:]' '-')"
# 构建镜像时可指定国产基础镜像，如openEuler
docker build --build-arg BASE_IMAGE=openeuler/openeuler:22.03-lts \
             --build-arg BUILDKIT_CONTEXT_KEEP_GIT_DIR=1 \
             -t "pwn.hust.college/dojo:$TAG" "https://gitee.com/hust-cse/pwn.hust.college.git#$BRANCH"
# 运行容器，挂载国产化相关配置目录
docker run --privileged --name "dojo-$TAG" \
           -v ./local_config:/data/config \
           -v ./loongarch_tools:/opt/loongarch_tools \
           -d "pwn.hust.college/dojo:$TAG"
```

通过以下命令启动一个VSCode隧道（使用你的GitHub或Gitee账号认证）连接到该容器，以便进行代码编写和调试：
```sh
docker exec -i "dojo-$TAG" dojo vscode
```

## 1.2 测试
可使用`test/local-tester.sh`脚本在本地运行pwn.hust.college平台的CI测试用例。该测试用例已针对平台的国产化特性进行适配，包括对LoongArch架构下挑战任务的测试、openEuler操作系统环境兼容性测试等。执行测试命令如下：
```sh
# 运行包含国产化特性的测试用例
test/local-tester.sh --enable-loongarch-tests --enable-openeuler-tests
```

## 1.3 添加配置项
若要为平台添加新的配置项，需遵循以下步骤，以确保配置项能适配平台的国产化架构和功能：
1. 在`dojo/dojo-init`中添加配置项，并设置合理的默认值，对于与国产化相关的配置（如LoongArch工具链路径），默认值应指向国产环境对应的路径。
2. 在`docker-compose.sh`中将配置项传播到相关容器（通常是`ctfd`容器），同时确保在国产操作系统容器中能正确接收和应用该配置。
3. 在`dojo_plugin/config.py`中将配置项加载到全局变量中，方便在平台代码的各个模块中引用，对于涉及国产代码托管平台Gitee的配置，需单独进行适配处理。
4. 在平台代码中根据需要正确导入并使用该配置项，例如在处理Gitee仓库的PR提交功能时，需使用对应的配置项进行相关参数设置。

## 二、国产化功能开发注意事项
1. **架构适配**：在开发新的挑战任务或工具时，需考虑对LoongArch等国产架构的支持，确保代码能在该架构下正常编译和运行，可参考平台已有的LoongArch适配案例进行开发。
2. **操作系统兼容**：由于平台采用openEuler作为挑战环境的基底，开发过程中需确保新增功能和工具在openEuler系统上的兼容性，避免使用该系统不支持的依赖库或命令。
3. **代码托管适配**：对于涉及代码仓库交互的功能，需同时支持GitHub和Gitee两个平台，在开发相关API和接口时，要考虑两个平台的差异，进行针对性处理。
4. **开源贡献流程**：遵循平台"取之开源，用之开源"的宗旨，开发的代码需符合BSD 2-Clause许可证要求，便于学生和其他开发者参与到平台的开源仓库建设中，同时在代码中添加清晰的注释，方便他人理解和修改。

通过以上开发流程和注意事项，可确保新开发的功能符合pwn.hust.college平台的特性，同时更好地支持国产化技术和开源教育理念。