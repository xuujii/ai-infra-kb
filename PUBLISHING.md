# 本地维护与 GitHub Pages 发布

源码在本地编辑并通过Git提交；Pages只发布构建产物，不承担编辑或保存未提交草稿的职责。独立仓库应以本项目文件夹为根目录。

- 源码仓库：https://github.com/xuujii/ai-infra-kb
- 阅读网站：https://xuujii.github.io/ai-infra-kb/
- 发布记录：https://github.com/xuujii/ai-infra-kb/actions

## 第一次发布

1. 使用自己的GitHub账号创建公开仓库，源码放在`main`分支。
2. 在仓库的Settings → Pages中，将Source设为GitHub Actions。
3. 推送`main`后，查看Actions中的`Publish documentation site`工作流。
4. 工作流构建`dist/`，检查发布链接并执行CPU教学算例，成功后部署Pages。
5. 用工作流返回的正式网址检查首页、独立文章、搜索和视频。默认项目网址为`https://<账号>.github.io/<仓库>/`。

## 日常更新

修改正文数据和共享样式/脚本，避免直接编辑生成后的`details/*.html`。

```text
node export.cjs
node check-release.cjs
node check-examples.cjs
git status
git add .
git commit -m "更新知识库内容"
git push origin main
```

页面交互或布局有改动时，另外运行`node check.cjs`；安装方式见README。推送成功后，仍需确认Actions部署成功；失败时线上可能继续保留上一次成功版本。

## 文件范围

- Git保存正文、构建脚本、网页、教学代码与已有视频成片及制作源数据。
- `dist/`是本地导出目录，由CI重新构建，不重复提交。
- `.qa/`、音频中间文件、日志、环境变量文件与依赖目录通过`.gitignore`排除。
- 授权凭据由GitHub CLI或Git凭据管理器管理，不写进代码、远程URL或工作流。
- 新增成片后须更新`videos.json`，并运行发布检查确认资源齐全。

已有4个视频会随站点发布；在当前大小下不需要额外视频服务。以后若视频显著增多，再评估仓库体积和播放分发。
