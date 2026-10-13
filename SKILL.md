---
name: image-to-live2d
description: "将角色 PNG 或分层 PSD 制作成真正可运行的 Live2D Cubism 模型包，优先使用 PSD2Live CLI 自动导出、MCP 调整参数与图层，并验证动作和运行时效果。适用于图片转 Live2D、立绘自动绑定、PSD2Live 建模及既有模型修正；不用于普通 GIF、透明视频或 ChatGPT Pets 精灵图。"
---

# 图片转 Live2D

将作者提供的角色图变成可复用的模型资产：保留原画与分层源文件，导出 `.moc3 + .model3.json + textures`，按实际能力附带物理、动作及可编辑工程。优先复用已有 PSD，使用 PSD2Live 自动建模；参数和局部修正走 MCP，避免逐点操作 Cubism。

本技能来自一次实际的 PNG → See-Through PSD → 图层修正 → PSD2Live 0.6.0 → Web 运行验证。经验与证据索引见 [references/prior-work.md](references/prior-work.md)；旧角色的动作和页面决定不自动成为新任务的要求。

## 判断输入与交付

- 已有 `.model3.json`：先检查并加载现有模型，修复或补动作通常无需重建。
- 已有 PSD：检查透明度、合成外观、部件和命名，合格后直接生成。
- 只有 PNG：先检查同目录是否已有分层源文件。没有时才做拆层与遮挡补全；单图不能无损直接变成模型。
- 以用户明确要求的动作和交付格式为范围。未指定时先交付中性姿态、眨眼、呼吸及轻微头发物理；视线、口型、表情、道具显隐和手臂动作按模型实测能力添加。

默认使用独立的版本目录保存源文件、候选模型和验收预览。生成模型不自动包含接入应用、修改全局 MCP 配置或外部上传素材的授权。若用户要求接入产品，遵循目标仓库当前门禁与任务范围。

## 素材准备

准备 PSD 时读取 [references/psd-preparation.md](references/psd-preparation.md)。先逐层检查，再比较完整合成图；不能仅凭图层数量宣布素材可用。

需要新像素、闭眼/口型差分、遮挡补画或重绘时，使用宿主实际可调用的图像生成/编辑工具；在 Codex 中遵循 `imagegen` 的编辑流程。锁定角色身份、画布、构图和无需修改的部件，只回填目标区域。使用在线拆层服务前确认上传符合用户授权；没有可用工具时，说明缺少的能力，不把单层 PNG 包装成“分层 PSD”。

只读分析、图层元数据检查与模型包校验可以用脚本。像素拆分/重组只有在用户明确要求这种确定性处理时采用，需保留原件并校验重新合成结果。历史中的连通域分层脚本只适合互不连通的左右部件，不能自动修复遮挡。

## 自动生成

首次使用或迁移环境时读取 [references/psd2live-automation.md](references/psd2live-automation.md)。先定位已安装的 PSD2Live，并读取其 `--help` 或对应版本的源码/文档；历史参数不是所有版本的保证。优先使用现有便携版及其自带运行时。

下面是历史中实际跑通的 PowerShell 命令形态；替换为当前真实路径，输出目录必须是新目录：

```powershell
$psd2liveExe = 'D:\tools\PSD2Live\PSD2Live.exe'
$sourcePsd = 'D:\assets\character-rig.psd'
$modelOutput = 'D:\assets\character-model-v1'
if (Test-Path -LiteralPath $modelOutput) { throw '输出目录已存在，请选择新版本目录' }
& $psd2liveExe --input $sourcePsd --output $modelOutput --lang zh --atlas 4096 --mesh-spacing 48 --head-strength 0.65 --body-strength 1.0
```

`4096 / 48 / 0.65 / 1.0` 是之前偏侧脸角色的起始配置，不能据此承诺任意角色都正常。检查 `.psd2live.json` 的语义映射、警告、中性姿态偏差和导出结果，再根据预览调整。头部强度值不是最终角度的精确换算。

CLI 批处理导出不等于在正在运行的 GUI 工程里编辑，也不等于 MCP 已连接。用户指定 MCP 时，先握手、列工具并读取工程，不能暗中改用桌面点按。

## MCP 编辑

使用实际 `tools/list` 返回的名称与 schema。历史可用工具包括 `project_get_state`、`project_list_layers`、`project_list_parameters`、`object_get`、`view_render_model`、`parameter_create`、`keyform_set`、`asset_import_png`、`layer_add_from_asset`、`project_save` 和历史/任务工具。

先读取当前工程与真实对象 ID。每次推进历史 HEAD 的修改，携带最新 `expected_history_head_node_id`；成功后使用返回的新 HEAD。超时或断线后先检查工程、历史和对象，确认前次操作是否提交，再决定重试。用模型 View 的像素↔画布映射和空间引用放置部件，不用旧截图坐标猜测位置。

图层显隐、表情和动作必须有模型中的参数/K 帧支持；仅写一份 motion JSON 不会凭空增加网格绑定。修改后同时保存 `.psd2live` 工作工程和运行时包，核对实际输出目录。若未保存工程，避免重启进程丢失内存修改。

## 验收与交付

先运行技能自带的只读结构校验器（Python 3.11+，仅标准库）：

```powershell
python '<技能目录>\scripts\validate_model.py' '<模型目录>\character.model3.json'
```

它检查必需文件、引用路径、JSON、MOC3 文件头及 SHA-256；退出码 0 只表示结构通过，不证明模型能被运行时解码或动作合格。

随后用目标 Cubism 运行时实际加载 `.model3.json`，检查加载错误和参数范围，并保留预览证据：

1. 中性姿态：对照 PSD，检查脸、眼、嘴、服装、道具、透明边缘及层级。
2. 单参数与组合：眨眼开/闭、嘴开/闭、视线、头部左右上下、物理摆动；只验证实际要求启用的能力，并检查极值及中间值。
3. 动作时间序列：开始、中段、峰值、结束及循环接缝。确认身体连接、遮挡、穿模和复位；“触发成功”不足以验收。
4. 若接入应用：核对源模型与运行目录哈希，确认实际加载了该版本，去掉旧 PNG 五官覆盖层或重复肢体层，检查缩放与点击命中。

过去的挥手实验因整袖刚性旋转导致肩部断裂、袖摆穿过头发，最终取消。遇到同类问题先降低范围或撤下异常动作，不将无限修网格/反复生图变成默认流程。除非新任务明确要求并通过视觉验收，不恢复旧挥手。

Cubism 可用于核验 `.cmo3`，但用户不想进入 Cubism 时，用运行时/MCP 验收，不要求作者手工绑点。分清 `.cmo3` 可编辑工程、`.psd2live` 工作工程和运行文件；可编辑工程未必保留原 PSD 的完整编辑链。

交付说明应列出源文件、工程、模型入口、预览、实际通过的检查、已验证动作及未解决的限制。没有完成运行时加载时，明确标注为候选模型。
