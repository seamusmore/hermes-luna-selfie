---
name: luna-selfie
description: 角色专属自拍技能，基于阿里云百炼 WAN 2.7 图生图 API，支持角色一致性保持。
author: 露娜
version: 1.3.0
triggers:
  - "自拍"
  - "让我看看你"
  - "自拍照"
  - "拍照"
  - "luna 自拍"
---

# 角色自拍生成器 (luna-selfie)

agent 角色的专属自拍技能，基于阿里云百炼 WAN 2.7 图生图 API，支持角色一致性保持。

## 特性

- **角色一致性**：使用参考图保持 agent 角色形象一致
- **异步生成**：支持任务轮询，自动等待完成
- **多分辨率**：支持多种尺寸选择
- **自拍视角**：优化的自拍视角和摄影风格

## 安装

### 推荐（via Hermes CLI）

```bash
hermes skills install https://github.com/seamusmore/hermes-luna-selfie.git
```

Then restart the gateway for the skill to take effect.

### 手动

```bash
git clone https://github.com/seamusmore/hermes-luna-selfie.git \
  ~/.hermes/skills/luna-selfie
```

## 配置

### API Key

在 `~/.hermes/.env` 中添加阿里云百炼 API Key（用于 WAN 2.7 图生图）：

```bash
SELFIE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 角色参考图

在 `~/.hermes/.env` 中配置角色参考图本地路径：

```bash
REF_IMAGE_PATH=<HOME>/.hermes/avatars/role_standard.png
```

### 默认输出目录

```
<HOME>/.hermes/selfie/
```

文件名格式：`luna_selfie_YYYYMMDD_HHMMSS.png`

## 命令

### 基础用法

```bash
cd ~/.hermes/skills/openclaw-imports/luna-selfie
python3 scripts/generate_selfie.py "咖啡厅窗边，手捧咖啡，文艺氛围"
```

### 指定分辨率

```bash
# 竖版自拍（推荐）
python3 scripts/generate_selfie.py "阳台夜景" --size 720*1280

# 正方形（默认）
python3 scripts/generate_selfie.py "办公室" --size 1280*1280

# 全高清竖版
python3 scripts/generate_selfie.py "咖啡厅" --size 1080*1920
```

### 异步模式

```bash
python3 scripts/generate_selfie.py "海边日落" --size 720*1280 --async
```

## 支持的分辨率

| 分辨率 | 比例 | 适用场景 |
|--------|------|----------|
| 1280*1280 | 1:1 | 通用、头像（默认） |
| 720*1280 | 9:16 | 自拍、全身照、手机壁纸（推荐） |
| 853*1280 | 2:3 | 半身照、竖版构图 |
| 1024*1536 | 2:3 | 竖版人像 |
| 1080*1920 | 9:16 | 全高清竖版、手机壁纸 |
| 1280*720 | 16:9 | 横版场景、电脑壁纸 |
| 1280*853 | 3:2 | 横版人像 |
| 1536*1024 | 3:2 | 横版场景 |
| 1920*1080 | 16:9 | 全高清横版、电脑壁纸 |
| 2048*2048 | 1:1 | 超高清正方形 |

**注意**：所有分辨率都是 16 的倍数，符合百炼 API 要求。

## 输出格式

```markdown
✅ 生成成功！
⏱️  耗时：{time}秒
📁 保存：{path}
```

## 参考

- `references/luna-selfie.md` — 完整工作流、提示词模板、风格偏好
- `references/wan27-arm-hand-connection-issue.md` — WAN 2.7 手臂/手部连接缺陷与缓解策略

## 脚本位置

`{baseDir}/scripts/generate_selfie.py`

## License

MIT
