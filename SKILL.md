---
name: luna-selfie
description: 角色一致性自拍生成器，基于阿里云百炼 WAN 2.7 图生图 API，通过参考图保持角色形象一致。
author: Luna
version: 2.0.0
triggers:
  - "自拍"
  - "让我看看你"
  - "自拍照"
  - "拍照"
  - "selfie"
---

# luna-selfie

通用角色自拍生成器。安装后配置 `config.json` 即可使用，**不绑定任何特定角色风格，需要手动配置**。

## 安装

技能目录结构：
```
config.json          ← 角色配置（必须配置）
scripts/
  generate_selfie.py ← 生成脚本
references/
  luna-selfie.md     ← 提示词技巧、故障排除
  wan27-arm-hand-connection-issue.md
```

## 配置

### 1. 初始化配置

技能根目录下有 `config.json.example`（出厂默认值），安装时拷贝为 `config.json` 并修改：

```bash
cp config.json.example config.json
```

按你的角色修改 `config.json` 中的字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `reference_image` | ✅ | 角色参考图路径，用于保持面部和身材一致性 |
| `character` | 可选 | 数组。画面主体固定描述（年龄、身材、面部特征等），每次生成自动注入 prompt |
| `style` | 出厂自带 | 数组。拍摄风格基线，默认含摄影风格、自拍视角、高画质 |
| `quality_fixes` | 出厂自带 | 数组。模型缺陷补偿，默认含 WAN 2.7 手臂完整性修复 |

**`config.json` 已在 `.gitignore` 中**，不会提交到 Git。`config.json.example` 随技能升级，新字段自动继承。

### 2. API Key（`~/.hermes/.env`）

```bash
SELFIE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

## 工作流（给 agent 看）

1. **自由构思**今天的场景、穿搭、饰品、动作、光线
2. **去重检查**：查 `~/.hermes/selfie/history.json` 最近 7 天，不要重复场景/穿搭/饰品
3. **生成**：调用 `generate_selfie.py`，只传入你构思的场景词
4. **交付**：用 `MEDIA:` 标签发给用户
5. **记录**：追加本次的场景、穿搭、饰品到 `~/.hermes/selfie/history.json`，格式见参考文档

**脚本自动做**：加载 `config.json` → 读取 `character` + `style` + `quality_fixes` → 按序拼接 → 调 API → 保存图片。

```
agent 传入:  "海边日落，白色连衣裙，回眸一笑"
脚本拼接:   "24岁，身材苗条，腿型纤细。海边日落，白色连衣裙，回眸一笑。摄影风格，自拍视角，高画质。完整的双臂从肩膀到手肘到手指连贯自然"
```

## 使用

```bash
cd path/to/skill
python3 scripts/generate_selfie.py "场景描述" [--size 720*1280]
```

| 参数 | 说明 |
|------|------|
| `prompt` | 场景描述（必填）：只写场景、穿搭、动作、光线 |
| `--size` | 分辨率，默认 `1280*1280`，自拍推荐 `720*1280` |
| `--output` | 自定义输出路径 |

## 约束

- 每次只生成 **1 张**
- API 失败（429/500/额度不足）**立即停止**，不重试
- 必须用 `MEDIA:` 标签交付
- 参考图建议用清晰的正面或半侧面人像
- 生成后人工肉眼确认手臂完整性

详情参考 `references/luna-selfie.md`。
