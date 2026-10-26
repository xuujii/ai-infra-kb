# AI Infra 知识库：文档网站

[在线阅读](https://xuujii.github.io/ai-infra-kb/) · [优化方法总览](https://xuujii.github.io/ai-infra-kb/overview.html) · [GitHub源码](https://github.com/xuujii/ai-infra-kb)

本地入口：[index.html](index.html)；优化地图与技术汇总表：[overview.html](overview.html)。先推理、后训练，各自有模型计算与系统执行两条线；优化入口位于步骤侧边。通信、内存通过标签及技术汇总表筛选提供阅读视角。

维护方式：本地编辑，GitHub保存版本，GitHub Pages提供在线阅读。首次发布与后续更新见 [PUBLISHING.md](PUBLISHING.md)。

点击方法进入 `details/Mxxx.html`。网站共用顶栏、分类目录、站内搜索、右侧本页目录与手机目录。支持 Ctrl+K 或 / 打开搜索，Esc 关闭；搜索方法原理、文章标题和基础概念。每篇文章地址独立，可回到技术表行或具体流程位置。

方法详情统一先放短片，再放文字详解。目前有 4 个中文合成旁白短片：FlashAttention（3 分 11 秒）、分页 KV（1 分 53 秒）、连续批处理（1 分 52 秒）、计算与通信重叠（1 分 51 秒）。均有中文字幕和章节跳转。按当前安排，后续优先补齐文字详解，暂不制作新视频。尚未制作视频的方法明确标注“视频讲解待制作”，不会显示空播放器。基础概念文章仍直接提供文字讲解。

全部网址使用相对路径，支持 `file://` 离线阅读和 GitHub Pages 项目子路径。没有远程脚本、字体、图片或搜索服务依赖。复制网站时可以只复制 `dist` 文件夹；编辑源码时复制整个 `ai-infra-kb` 目录。

## 内容与进度

- 47 个稳定方法编号，全部已完成总览定位、适用范围与代价。
- 47 篇第一版详解：M004 权重与激活量化、M005 KV Cache 量化与压缩、M007 FlashAttention、M013 投机解码、M014 历史 KV 复用、M015 前缀缓存与缓存感知路由、M016 分页 KV、M021 连续批处理、M022 分块 Prefill、M026 通信重叠、M027 MC²、M035 混合精度、M036 ZeRO/FSDP、M037 激活重计算、M024 并行策略与设备映射、M039 梯度累积与同步频率、M040 流水线调度、M009 本地算子融合、M018 图编译与形状专门化、M019 执行图捕获与重放、M020 长度分组/去Padding/Packing、M033 输入预取与异步搬运、M023 CPU与设备异步调度、M017 KV分层/卸载/淘汰、M038 训练状态与激活卸载、M047 缓冲区复用与布局规划、M025 通信算法/协议/拓扑、M028 Prefill/Decode分离、M030 MoE专家布局与负载均衡、M006 矩阵乘法与访存优化、M008 Decode专项内核、M010 MoE计算优化、M002 MQA/GQA/MLA、M003 稀疏计算与滑窗Attention、M011 输出投影与Loss内存优化、M012 采样与约束解码、M034 LoRA/QLoRA微调、M031 多LoRA服务与合并、M041 融合优化器与状态精度、M042 异步检查点与故障恢复、M032 加载/编译缓存与预热、M001 剪枝与知识蒸馏、M044 上下文/模型路由/生成预算、M045 结果缓存、M029 服务调度与资源治理、M043 数据与训练策略、M046 RL外层资源与权重同步。
- 当前47个目录条目的第一版详解均已编写；这表示已有目录覆盖完成，不表示穷尽全部优化研究或硬件实现。
- 教学容量与时间示例明确区分于设备实测；CUDA / 昇腾硬件性能尚未在本地验证。

## 维护来源

- `stages.json`：准备阶段、推理 / 训练两条主线、RL 扩展入口；稳定阶段编号。
- `methods.json`：方法的唯一目录数据源，含 tags / stages / kind / scope / cost / sources / related。
- `article-content.cjs`：独立详解正文，按方法编号组织；不把长正文放回总览。
- `quantization-articles.cjs`：权重/激活量化与KV量化的独立教程，包含PTQ/QAT、方法族定位、尺度交互与内存估算；容量估算与硬件实测分开。
- `inference-articles.cjs`：KV 复用、前缀缓存、分块 Prefill、投机解码四篇独立教程，含具体算例、教学代码、适用边界与实现检查清单；新文章按各自 checked 日期标注资料核查时间。
- `distributed-articles.cjs`：并行策略、梯度累积与流水线调度三篇教程，含两卡 MLP 前后向算例、有效批量与 token 加权、GPipe / 1F1B 时间线；自设例子不代表设备实测。
- `execution-articles.cjs`：本地融合、图编译、图捕获重放三篇教程，含逻辑读写量、编译成本交互、固定地址与新输入的逐步演示；明确区分编译图、执行图和结果缓存。
- `input-articles.cjs`：长度组织/打包、输入流水、CPU与设备调度三篇教程；包含样本隔离mask交互、位置与标签边界、准备/复制/计算时间线及缓冲生命周期。
- `memory-articles.cjs`：KV分层、训练卸载、缓冲复用三篇教程；含活跃/空闲缓存的区分、回迁与重算比较、反向截止时刻、生命周期及stride/view算例。
- `communication-articles.cjs`：通信算法/协议/拓扑、PD分离、MoE布局三篇教程，包含Ring逐轮归约与字节量、分离交接及首/次token时序、逻辑专家与物理副本和负载算例。
- `kernel-articles.cjs`：矩阵乘法分块、Split-KV与Grouped GEMM三篇教程，含逻辑读写量、Softmax统计合并、专家token重排与加权还原；教学容量和CPU验证不代表硬件实测。
- `structure-loss-articles.cjs`：注意力结构、稀疏计算、输出投影与Loss三篇教程；包含头共享、潜在矩阵吸收、可见性/块覆盖、在线词表归一化与分块反向，区别结构质量与执行等价。
- `coordination-articles.cjs`：服务治理、达标训练成本、RL外层协同；含队列/取消依赖、加权数据目标与策略版本。
- `workload-articles.cjs`：剪枝蒸馏、请求预算与结果缓存；含结构改写、软标签梯度、完整任务成本和答案复用合同。
- `lifecycle-articles.cjs`：融合优化器、异步检查点、加载缓存与预热三篇教程；含AdamW多步状态、独立快照与提交、启动就绪边界。
- `adaptation-articles.cjs`：采样与约束、LoRA/QLoRA、多LoRA服务三篇教程；含过滤分布/状态、冻结梯度链、训练状态账本、适配器分组和合并/版本身份。
- `flash-article.cjs`：FlashAttention 的入门到进阶正文；先解释数据流与手算例子，再展开公式。
- `videos.json`：方法视频配置，视频存在时自动置于文章开头。标题与 src 必填；poster / subtitles / transcript / chapters 可选。章节使用 name 和 start（秒），数量自由，不依赖某种固定分镜。
- `site.cjs` / `site.css` / `site.js`：统一文档站外观、首页、分类目录、搜索和视频章节交互。
- `videos/lessons.json` / `videos/narrate-series.ps1` / `videos/render-series.py`：新增三片的分镜、中文本地语音与逐帧绘图源。先生成旁白，运行 `render-series.py --preview` 检查画面，再运行 `render-series.py` 输出 MP4 并登记到视频配置。可用 `--id M016` 等只重建指定短片。
- `export.cjs`：输出 `dist` 静态网站，只包含页面、视频与教学例子；不发布制作中间文件和开发脚本。
- `.github/workflows/pages.yml`：GitHub Pages自动发布工作流，构建并验证链接与CPU教学算例后，仅将`dist`部署到网站。
- `foundations.cjs`：7 篇共享基础文章，以及 47 篇方法的前置概念、简短解释和链接映射。文章开头即可阅读定义，侧栏“基础讲解”可直接查找。
- `sources.json`：官方文档与原始论文，正文按段引用；main / latest 接口须匹配安装版本。
- `build.cjs`：校验引用、构建总览，并调用 `details.cjs` 生成独立页面。
- `style.css` / `app.js`：总览展示与筛选；`article.css` / `article.js`：文章导航与教学交互。
- `examples/`：纯 Python CPU 例子，验证在线 Softmax、分页寻址、两卡部分结果归约、因果 KV 续写/分块/前缀复用、投机采样的单步概率纠偏、整数格点和打包、KV量化对Attention的影响、张量并行 MLP 前后向与数值梯度、不同大小 microbatch 的梯度加权、依赖正确的流水线调度、融合语义与数值梯度、教学编译缓存与分档、固定缓冲重放及异步队列成本、两层打包Attention的边界与位置、输入流水依赖与缓冲就绪；不测试硬件加速。
- `check-pages.cjs`：页面、跨页锚点、筛选、往返导航、交互算例、打印恢复与响应式检查；`check.cjs` 是统一入口。
- `communication.json` / `memory.json`：以前整理的场景与内存对象映射，保留供以后文章使用。
- `extra-views.cjs`：旧版额外阅读章节构建代码，当前不调用；原总览备份在 `../tmp/ai-infra-before-pages/overview.html`。

## 构建与检查

在本目录运行 `node export.cjs`、`node check-release.cjs` 与 `node check-examples.cjs`。Node.js建议22或更新版本；CPU算例需Python 3.10或更新版本。构建与发布检查仅依赖Node内置模块，CPU算例仅依赖Python标准库。

完整页面交互检查另需Playwright：先运行 `npm install --no-save playwright@1.62.1`，Windows有Edge时可直接运行 `node check.cjs`；其他平台先运行 `npx playwright install chromium`。可用 `PLAYWRIGHT_BROWSER_CHANNEL` 选择浏览器，用 `AI_INFRA_QA_DIR` 指定截图目录（默认为忽略提交的 `.qa/`）。`AI_INFRA_PYTHON` 可指定CPU算例使用的Python。每次构建根据正文数据决定文章状态，不手工修改生成的HTML。

发布文件使用 `node export.cjs`，结果在 `dist`。也可用 `npm run build` / `npm run export`。生成后的 `dist/index.html` 可以直接离线打开，或交给任意静态网站服务。

## 发布到 GitHub Pages

1. 将本目录的内容作为一个独立 GitHub 仓库的根目录，保留 `.github` 和 `.nojekyll`。不是把它放在另一个仓库的子目录里。
2. 默认工作流使用 `main` 分支；如果仓库使用其他分支名，修改工作流的 branches。
3. 仓库 Settings → Pages → Build and deployment，将 Source 设置为 GitHub Actions。
4. 推送后，工作流运行 `node export.cjs`，仅将 `dist` 发布到 Pages。以后更新内容会沿用相同的构建和发布流程。

仓库使用`main`分支保存版本，Pages使用GitHub Actions部署；部署状态以仓库Actions中的最新成功记录为准。依据：[GitHub Pages自定义工作流官方说明](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

CPU 例子使用 Python 3 标准库：

```text
python examples/attention_online.py
python examples/paged_kv.py
python examples/tp_reduce.py
python examples/causal_kv.py
python examples/speculative_sampling.py
python examples/quantization_basics.py
python examples/kv_quantization.py
python examples/tp_mlp.py
python examples/gradient_accumulation.py
python examples/pipeline_schedule.py
python examples/local_fusion.py
python examples/compile_guards.py
python examples/graph_replay.py
python examples/packing_boundaries.py
python examples/input_pipeline.py
python examples/kv_tiering.py
python examples/training_offload.py
python examples/memory_planning.py
python examples/ring_collective.py
python examples/pd_handoff.py
python examples/expert_placement.py
python examples/tiled_gemm.py
python examples/split_kv.py
python examples/grouped_moe.py
python examples/attention_structures.py
python examples/sparse_attention.py
python examples/chunked_cross_entropy.py
python examples/sampling_constraints.py
python examples/lora_training.py
python examples/multilora_serving.py
python examples/fused_adamw.py
python examples/async_checkpoint.py
python examples/startup_readiness.py
python examples/pruning_distillation.py
python examples/request_workload.py
python examples/result_cache.py
python examples/service_governance.py
python examples/training_strategy.py
python examples/rl_coordination.py
```

## 新增方法和文章

1. 新方法分配未用过的 Mxxx 编号，标注一个或多个真实流程位置；tag 是可交叉的优化维度。
2. 写清收益、适用条件、代价和资料。`kind` 表示主要定位，不保证单步提速或无质量影响。
3. 在 `article-content.cjs` 为相同编号增加文章：未优化执行 → 机制 → 具体算例 → 实现 → 条件与验证 → 平台对照 → 自查练习。
4. 引用官方资料，给自设算例标注假设。涉及 shape、dtype、通信语义与硬件支持时避免泛化。
5. 构建与检查后，总览入口、状态、目录及关联导航自动更新。

已有编号不改号、不回收。一个方法族需要细分时，保留旧编号作为上层入口，为子方法分配新编号并关联。

## 后续开发顺序

当前47项已完成第一版。后续可做全库内容复核，并按需要为GPTQ/AWQ/SmoothQuant等具体方法、性能分析与平台实现增加深入文章；视频制作仍按当前安排暂缓。新增方法沿用稳定编号、目录和模板。

当前覆盖自回归 LLM 优化的主要方向，未声称穷尽所有论文、框架变体、多模态、扩散或完整RL算法体系。
