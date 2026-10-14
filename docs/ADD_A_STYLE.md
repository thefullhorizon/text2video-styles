# 新增一个风格

每个风格是 `plugins/text2video-styles/skills/` 下一个**自包含**的文件夹，互不依赖。

## 1. 目录规范

```
skills/<style-id>/            # 小写英文 + 连字符，如 apple-minimal
├── SKILL.md                  # 必需：触发说明 + 出片步骤 + 固定参数表
├── make_video.py             # 必需：出片入口，一条命令出片（新风格统一用此文件名）
├── template.html / *.py      # 渲染实现（HTML+Playwright 或 Pillow 均可）
├── package.json              # 可选：npm 依赖（如网页字体）
└── assets/                   # 背景、配乐等素材（须有可公开分发的授权）
```

## 2. SKILL.md 要求

- frontmatter：`name` 与文件夹同名；`description` 写清**中文风格名和触发说法**，例如「用户说『用极简苹果风把文案生成视频』时……」。
- 正文三部分：出片步骤（含 spec.json 示例）、固定参数表、文件说明。
- 参数一旦定稿就写死在实现里，SKILL.md 中注明「不要擅自修改」。

## 3. 提交前检查

1. `examples/<style-id>.json` 放一份示例文案，能一条命令跑通。
2. 生成预览动图 `docs/previews/<style-id>.gif`（宽 270px，约 3 秒）：
   `ffmpeg -i out.mp4 -t 3 -vf "fps=12,scale=270:-1" docs/previews/<style-id>.gif`
3. 在 README 的风格一览表里加一行。
4. 素材授权写进 NOTICE.md。
5. 更新 `plugin.json` 与 `marketplace.json` 的 `version`。
