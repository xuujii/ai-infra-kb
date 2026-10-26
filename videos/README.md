# AI Infra 动画微课

四个成片均为 1280×720、20 fps、H.264/AAC，包含中文合成旁白和画面字幕。详解页位于 `../details/`，页面开头可以直接播放与按章跳转。

| 方法 | 目录 | 核心演示 |
| --- | --- | --- |
| M007 FlashAttention | flashattention | 分块、在线 Softmax、反向重计算 |
| M016 PagedAttention / 分页 KV | paged-kv | 最大长度预留、块表寻址、增长与回收 |
| M021 连续批处理 | continuous-batching | 固定批次和逐轮重排的请求时间线 |
| M026 计算与通信重叠 | compute-communication-overlap | 梯度分桶、理想重叠与通信长尾 |

每个目录包含 MP4、字幕、海报、带时间点的讲解稿与独立播放器。讲解稿提供原始资料和教学假设；容量和时间线不是硬件实测。

后三片的源数据集中于 `lessons.json`。制作需要 Pillow 和 imageio-ffmpeg；后者当前安装于 `D:/career/tmp/flash-video-tools`。Windows 中文旁白使用本机 Huihui SAPI 语音，不调用远程服务。共用 `flashattention/render.py` 中的绘图工具，因此制作时应保留完整 videos 源码目录。

```text
powershell -NoProfile -ExecutionPolicy Bypass -File narrate-series.ps1
python render-series.py --preview
python render-series.py
node ../export.cjs
```

render-series 会在成片导出成功后更新 `../videos.json`。未成功导出的视频不会注册到知识库。字体使用 Windows 微软雅黑；跨平台制作需更换字体与语音步骤。阅读和网站发布不依赖这些制作工具。
