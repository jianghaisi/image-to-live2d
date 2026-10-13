# PSD2Live 自动化及故障恢复

## 定位版本

先查用户指定路径、现有工具目录与系统程序路径，避免全盘扫描。之前使用的是 PSD2Live 0.6.0 Windows 便携版；优先复用本机已有安装，并核对实际版本。

对应版本的源码中，`Main.kt`、用户指南和 MCP 工具 schema 可帮助核对安装行为。不要把旧电脑的路径写死进命令。如果确实需要获取程序，使用[官方项目发布](https://github.com/tsunehimatoi/psd2live/releases)，核对版本与发布的校验值。

## CLI 与 GUI 的区别

历史版本无参数启动 GUI，并启动本机 MCP；带 `--input/--output` 时执行批处理导出。因此 CLI 成功不会证明 MCP 正常，也不会加载/更新另一个 GUI 工程。

之前 CLI 支持 `--input`、`--output`、`--lang`、`--atlas`、`--mesh-spacing`、`--head-strength`、`--body-strength` 及禁用物理/工程/模型/动作等开关。读取实际版本的 `--help` 后再执行。候选输出目录使用新版本名；等进程和文件写入完成后再验证，不以单个文件出现作为全包完成。

读取 `<stem>.psd2live.json`：检查画布、参数配置、图层语义、summary 和 warnings。中性姿态偏移警告必须对照图像核验。纹理图集尺寸与网格间距根据原图、性能与细节选择，不因历史用了 4096 便一律放大。

## MCP 连接

默认历史端点为 `http://127.0.0.1:23871/mcp`，以当前连接面板显示的地址为准。使用原生 MCP 工具连接优先；如宿主未暴露工具，可在用户已授权的范围内使用现有 Streamable HTTP 客户端。只有 Stdio 宿主才需要上游的 `mcp_proxy.py`。

凭据从用户配置或进程环境读取，不把 token 写入技能、脚本示例、命令输出或日志。不要全量打印注册表、配置文件、请求头或旧会话工具调用。新建技能不自动授权修改宿主 MCP 设置。

连接时做以下实际验证：

1. 进程存活，TCP 端口确实监听；连接面板的“ONLINE”不能替代探测。
2. JSON-RPC `initialize` 协商协议；遵循服务器的 session header 与初始化通知要求。
3. `tools/list` 获取当前名称与 schema，再调用 `project_get_state`。
4. 若工程为空，检查工具是否有导入能力。历史版本第一次打开 PSD 需在 PSD2Live 导入一次；不要调用想象出来的 import 工具，也不要把 CLI 输出当作当前工程已加载。

写入前读取真实层/对象/参数 ID 和历史 HEAD；不要沿用之前角色的 ID。遵循 `expected_history_head_node_id` 的并发检查。长工作可用已存在的 `task_start/task_update/task_get` 保存检查点；它们记录建模任务，不是作者批准接口。

## 局部素材与参数

使用 `view_render_layer/view_render_context/view_render_model` 读取模型 View、revision 与空间映射。新增透明素材用当前工具的 `spatial_reference_id`；裁剪返回时按 schema 提供 `source_pixel_rect`。遵循实际 PNG 尺寸、画布单位及映射，避免按屏幕像素比例猜位置。

支持的 parameter/keyform/object 编辑应逐项通过 schema 调用。每步验收目标对象和完整模型，成功后再写下一步。导出前 `project_save` 并检查保存状态，随后用实际导出工具/流程输出运行包；先读工具清单确认名称和路径。

模型的 mouth 参数不等于已经接好语音口型，道具显隐参数不等于已有应用点击逻辑。动作采用模型实际支持的参数；保存 source project 与运行包都需要完成。

## 历史故障

### ONLINE，但端口没有监听

之前 Java 在 Windows 默认临时目录建立内部通道失败。读取该进程日志后，换用短的 ASCII 临时路径才真正握手成功。先验证故障证据，不为所有环境一律换 JDK 或改系统临时目录。

需要时为这次启动设置进程级 JVM 临时目录（如 `-Djava.io.tmpdir=<短路径>`），使用与安装匹配的启动配置，保留恢复方法；不要全局改 `TEMP/TMP/JAVA_HOME`，不要盲目杀死其他 Java 程序。后台日志辅助进程使用隐藏窗口；用户明确需要操作编辑器时才打开可见窗口。

### 保存时 EFS/跨卷/临时目录错误

之前工作区文件带 EFS 加密属性，新短临时目录的属性与目标不一致，导致保存失败。先检查日志、目标路径、临时路径、卷和加密属性。保留内存工程及历史，备份工作区后选择兼容的保存路径/临时目录；不要全盘改变加密属性、自动解密原件或直接重启。

### 超时后重复导出/写入

先看项目状态、历史和目标文件是否已经提交，再重试。只读发现可以有限重试；写入必须消除结果未知状态。导出可能仍使用应用记住的旧目录，核对返回路径、修改时间和哈希。

### CMO3 能打开，但源链缺失

历史诊断明确标记 `.cmo3` 由纹理重建可编辑层，未保留原 PSD 编辑链。保留 PSD 和 `.psd2live`，交付时说明，不把“可编辑”误写成无损往返。

## 运行时验证

实际加载目标 `.model3.json`，核对 Cubism Core 与 MOC3 版本兼容性。若已有应用渲染器优先复用；历史使用 `pixi-live2d-display` 与官方 Cubism Core，不因此擅自给其他项目新增依赖。保留实际加载错误与视觉证据，检查 copied assets 的哈希一致。

继续调整或接入时读取当前上游资料：[用户指南](https://github.com/tsunehimatoi/psd2live/blob/main/docs/zh/USER_GUIDE.md)、[MCP 设计与工具契约](https://github.com/tsunehimatoi/psd2live/blob/main/docs/zh/AGENT_ARCHITECTURE.md)。优先使用对应安装版本源码和工具返回值，避免把主分支新功能套到旧版。
