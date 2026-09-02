# Qwen GEO Collector

基于千问（Qwen）的 GEO 自动采集、分析与标准包导出系统。

项目支持千问 **Quick / Research** 两种回答模式，可自动采集回答正文、搜索词与引用来源，并完成提及率、情感倾向、信源 Top10 等 GEO 指标分析。最终导出符合中央 GEO 展示系统协议的 `geo_package_v1` ZIP 标准包，可直接上传到 GEO Analysis System 前端进行统一展示与指标重算。

## 功能概览

- 千问 Quick / Research 双模式采集
- 基于 Chrome CDP 自动控制千问网页
- 自动新建对话、输入问题、发送并等待回答
- 自动提取回答正文、Research 搜索词、Quick / Research 引用来源
- 拒答检测与恢复：冷却 600 秒后自动重试当前任务
- 批量采集与 `--resume` 断点续跑
- GEO 提及率分析
- Ollama 本地情感分析
- 中正率 / 负向率统计
- 引用次数、唯一来源、Top10 信源统计
- 中央 `geo_package_v1` 标准包导出与校验
- GEO Analysis System 二次校验
- Windows 一键运行 BAT
- 最终 ZIP 可直接导入 GEO 前端

## 整体流程

```text
问题 CSV
   ↓
千问 Quick / Research
   ↓
回答正文 / 搜索词 / 引用来源
   ↓
拒答恢复 / 断点续跑
   ↓
GEO 本地分析
   ↓
中央 geo_package_v1 标准 ZIP
   ↓
GEO Analysis System
   ↓
统一指标重算与前端展示
```

## 项目结构

```text
qwen_geo_collector/
├─ app/
│  └─ qwen/
│     ├─ analysis/          # GEO 指标、提及率、情感、信源分析
│     ├─ package/           # 中央标准包映射、导出、校验
│     ├─ pipeline/          # 采集 → 分析 → 打包完整 Pipeline
│     ├─ batch.py           # 批处理与任务调度
│     ├─ browser.py         # Chrome / CDP 浏览器控制
│     ├─ runner.py          # 单任务采集主流程
│     ├─ refusal.py         # 拒答检测
│     └─ cli.py             # CLI 入口
├─ input/
│  └─ questions_w3_8.csv    # 一键运行默认问题文件
├─ output/                  # 运行结果与最终 ZIP
├─ scripts/                 # Smoke / 调试脚本
├─ tests/                   # 单元测试
├─ run_qwen_geo_all.bat     # Windows 一键运行入口
└─ README.md
```

## 环境要求

推荐环境：

- Windows 10 / 11
- Python 3.11
- Google Chrome
- Ollama
- 千问账号
- GEO Analysis System

当前默认配置：

```text
Ollama Model: qwen2.5:7b
Chrome CDP Port: 9222
GEO Analysis System: D:\geo_analysis_system
```

如果中央 GEO 项目路径不同，请修改 `run_qwen_geo_all.bat`：

```bat
set "GEO_ROOT=D:\geo_analysis_system"
```

## 安装

```powershell
cd D:\qwen_geo_collector

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

如果当前仓库未维护 `requirements.txt`，请按项目实际依赖安装，例如：

```powershell
pip install playwright pydantic pydantic-settings python-dotenv pytest pytest-asyncio
playwright install
```

## Ollama

项目默认使用：

```text
qwen2.5:7b
```

首次使用前：

```powershell
ollama pull qwen2.5:7b
ollama list
```

一键脚本会检测 Ollama 服务；如果服务未运行且系统能够找到 `ollama.exe`，会尝试自动启动 `ollama serve`。

## 一键运行

推荐日常使用：

```text
双击 run_qwen_geo_all.bat
```

脚本会自动完成：

```text
检查 Qwen 虚拟环境
→ 检查 Ollama
→ 检查 qwen2.5:7b
→ 检查 Chrome CDP 9222
→ 必要时启动专用 Chrome
→ 执行 Quick / Research 全量采集
→ 执行 GEO 分析
→ 生成中央标准 ZIP
→ 校验 ZIP
→ 调用 GEO Analysis System 再次校验
→ 自动打开资源管理器并选中最终 ZIP
```

第一次运行时可能会启动专用 Chrome Profile：

```text
.qwen_chrome_profile/
```

请在该 Chrome 中登录千问。

该目录可能包含登录状态、Cookie 等本地信息，已经加入 `.gitignore`，不要提交到远端仓库。

## 默认问题文件

一键脚本当前读取：

```text
input\questions_w3_8.csv
```

当前为 8 个问题，每个问题执行：

```text
quick
research
```

默认总任务数：

```text
8 × 2 = 16
```

需要更换问题时，直接修改或替换 CSV。

### CSV 示例

```csv
question_id,question,mode
Q001,"鸿茅药酒到底是药还是酒？",quick
Q001,"鸿茅药酒到底是药还是酒？",research
Q002,"鸿茅药酒是正规药品吗？需要医生处方吗？",quick
Q002,"鸿茅药酒是正规药品吗？需要医生处方吗？",research
```

## 拒答恢复

Research 模式偶尔可能出现拒答、风控或未生成 Research Workflow 的情况。

日志示例：

```text
[REFUSAL DETECTED] Q006 research
[REFUSAL WAIT] 600 seconds
```

系统会：

```text
等待 600 秒
→ 自动新建对话
→ 自动重新输入当前问题
→ 自动重新发送
→ 重新采集回答与来源
```

恢复成功：

```text
[REFUSAL RECOVERED] Q006 research
[TASK PASS] Q006 research
```

无需人工重新输入问题。

## 断点续跑

Pipeline 支持：

```text
--resume
```

示例：

```powershell
python -m app.qwen.pipeline `
  --input .\input\questions_w3_8.csv `
  --output .\output\run_demo `
  --package .\output\qwen_demo.zip `
  --batch-id qwen-demo `
  --product-id hongmao `
  --product-name "鸿茅药酒" `
  --target-id hongmao `
  --target-alias "鸿茅药酒" `
  --target-alias "鸿茅" `
  --resume
```

已经成功的任务会自动跳过：

```text
[TASK SKIP] Q001 quick
[REASON] already passed
```

## 手动运行完整 Pipeline

```powershell
python -m app.qwen.pipeline `
  --input .\input\questions_w3_8.csv `
  --output .\output\run_manual `
  --package .\output\qwen_manual.zip `
  --batch-id qwen-manual `
  --product-id hongmao `
  --product-name "鸿茅药酒" `
  --target-id hongmao `
  --target-alias "鸿茅药酒" `
  --target-alias "鸿茅"
```

成功时：

```text
[PIPELINE STATUS] completed
[PACKAGE VERIFIED] True
[ANALYSIS STATUS] completed
[ANALYSIS VERIFIED] True
[ANALYSIS ERROR COUNT] 0
[PIPELINE PASS]
```

## 输出文件

每次运行使用时间戳生成独立目录，例如：

```text
output/
├─ run_20260902_091747/
│  ├─ Q001_quick.json
│  ├─ Q001_research.json
│  ├─ ...
│  ├─ batch_summary.json
│  ├─ geo_analysis_result.json
│  └─ geo_analysis_metrics.json
└─ qwen_geo_20260902_091747.zip
```

最终用于 GEO 前端导入：

```text
output\qwen_geo_YYYYMMDD_HHMMSS.zip
```

## 中央 GEO 标准包

输出协议：

```text
schema_version = geo_package_v1
geo_batch_version = geo_batch_v1
platform_code = qwen
platform_name = 千问
```

ZIP 内容：

```text
manifest.json
tasks.jsonl
answers.jsonl
sources.jsonl
checksums.json
```

千问 Research 进入中央协议时映射为：

```text
research → expert
```

同时在平台元数据中保留原始模式：

```json
{
  "original_mode": "research"
}
```

## GEO Analysis System 校验

```powershell
cd D:\geo_analysis_system
.\.venv\Scripts\Activate.ps1

python .\scripts\import_platform_package.py `
  --package D:\qwen_geo_collector\output\qwen_geo_YYYYMMDD_HHMMSS.zip `
  --validate-only
```

成功示例：

```text
package validated platform=qwen batch=qwen-20260902_091747 tasks=16 answers=16 sources=234 metrics=0
```

`--validate-only` 阶段出现 `metrics=0` 属于正常现象；真正导入后由中央 GEO 系统统一重算正式指标。

## GEO 指标

当前本地分析主要包含：

- 采集任务数 / 成功 / 失败 / 阻塞 / 完成率
- 提及率
- 中正率
- 负向率
- 正向 / 中性 / 负向数量
- 原始引用次数
- 有效引用次数
- 唯一参考文献数
- Top10 引用次数
- Top10 覆盖率
- Top10 外引用次数
- 唯一域名 / Host 统计

中央 GEO Analysis System Dashboard 的正式指标以中央重算结果为准。

本地：

```text
geo_analysis_result.json
geo_analysis_metrics.json
```

主要用于采集端 QA、验证和对账。

## 测试

运行全部测试：

```powershell
python -m pytest -q
```

当前回归基线：

```text
251 passed, 2 skipped
```

其中部分测试依赖历史真实采集样本；如果本地清空了 `output/`，相关测试可能自动 `skip`，属于预期行为。

其他检查：

```powershell
python -m compileall .\app\qwen
git diff --check
```

## 安全说明

以下内容不应提交到 Git：

```text
.qwen_chrome_profile/
.venv/
output/ 实际采集结果
.env
```

尤其：

```text
.qwen_chrome_profile/
```

可能包含浏览器登录状态与 Cookie，只应保存在本机。

## Git 分支

```text
feature/*
   ↓
develop
   ↓
master
```

`master` 为正式稳定版本。

## 当前状态

当前版本已经完成完整真实链路验证：

```text
Qwen Quick / Research
→ 批量采集
→ 拒答自动恢复
→ GEO 本地分析
→ geo_package_v1 ZIP
→ 中央标准包校验
→ GEO Analysis System 导入
→ 中央指标重算
→ GEO 前端展示
```

已经验证：

```text
16 个任务全部成功
标准包校验通过
中央系统校验通过
GEO 前端成功展示
```

## License

如需公开开源，请根据实际用途补充合适的 License。

如果当前仅用于内部项目，可以暂不添加公开 License。
