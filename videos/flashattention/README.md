# FlashAttention 动画微课

独立样片，没有改动知识库总览和方法文章。

- `flashattention.mp4`：720p、20 fps、H.264/AAC，含中文合成旁白和画面字幕。
- `index.html`：本地播放器，包含章节跳转和文章链接。
- `story.json`：分镜和旁白内容。
- `讲解稿.md`：附时间点的文字稿。
- `flashattention.srt` / `.vtt`：独立字幕。
- `narrate.ps1`：使用 Windows 本机 Microsoft Huihui SAPI 中文语音；无远程语音服务。
- `render.py`：用 Pillow 逐帧绘图，通过 ffmpeg 导出成片。

技术依据：https://arxiv.org/abs/2205.14135

制作环境的 Python 需要 Pillow 和 imageio-ffmpeg。当前 imageio-ffmpeg 安装在 `D:/career/tmp/flash-video-tools`，没有更改全局 Python 依赖。重建时先执行 `narrate.ps1`，再执行 `render.py`；`render.py --preview` 只生成预览。

影片中的中间矩阵容量与数据流是教学示意，没有提供硬件实测加速倍数。数学定义等价不代表不同浮点执行顺序逐 bit 一致。
