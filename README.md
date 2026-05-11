# luna-selfie

角色自拍生成技能 for Hermes Agent — 基于阿里云百炼 WAN 2.7 图生图 API，通过参考图保持角色形象一致性。

## 特性

- **角色一致性**：使用参考图保持 agent 角色形象一致
- **异步生成**：支持任务轮询，自动等待完成
- **多分辨率**：支持 720×1280（自拍推荐）、1280×1280 等多种尺寸
- **自拍视角**：优化的自拍视角和摄影风格

## 安装

### 推荐（via Hermes CLI）

```bash
hermes skills install https://github.com/seamusmore/hermes-luna-selfie.git
```

### 手动

```bash
git clone https://github.com/seamusmore/hermes-luna-selfie.git \
  ~/.hermes/skills/luna-selfie
```

## 配置

在 `~/.hermes/.env` 中添加：

```bash
# 阿里云百炼 API Key（用于 WAN 2.7 图生图）
SELFIE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 角色参考图本地路径
REF_IMAGE_PATH=<HOME>/.hermes/avatars/role_standard.png
```

## 使用

```bash
# 竖版自拍（推荐）
python3 scripts/generate_selfie.py "海边日落，白色连衣裙" --size 720*1280

# 正方形
python3 scripts/generate_selfie.py "咖啡厅窗边" --size 1280*1280

# 异步模式
python3 scripts/generate_selfie.py "阳台夜景" --size 720*1280 --async
```

## 输出

默认保存到 `<HOME>/.hermes/selfie/`，文件名格式：`luna_selfie_YYYYMMDD_HHMMSS.png`

## License

MIT
