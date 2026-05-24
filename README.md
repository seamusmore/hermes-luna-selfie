# luna-selfie

通用角色自拍生成器 for Hermes Agent — 基于阿里云百炼 WAN 2.7 图生图 API，通过参考图保持角色形象一致性。

**不绑定任何特定角色风格**，每个 agent 通过 `config.json` 配置自己的角色描述。

## 安装

```bash
git clone https://github.com/seamusmore/hermes-luna-selfie.git \
  ~/.hermes/skills/luna-selfie
```

## 配置

### 1. 角色配置（`config.json`）

从出厂模板拷贝并修改：

```bash
cd ~/.hermes/skills/luna-selfie
cp config.json.example config.json
```

按你的角色编辑 `config.json`：

```json
{
  "reference_image": "~/.hermes/avatars/agent_standard.jpg",
  "character": [
    "24岁，身材苗条，腿型纤细"
  ],
  "style": [
    "摄影风格，自拍视角，高画质"
  ],
  "quality_fixes": [
    "完整的双臂从肩膀到手肘到手指连贯自然"
  ]
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `reference_image` | ✅ | 角色参考图路径，用于面部和身材一致性 |
| `character` | 可选 | 画面主体固定描述（年龄、身材等），每次自动注入 prompt |
| `style` | 出厂自带 | 拍摄风格基线 |
| `quality_fixes` | 出厂自带 | 模型缺陷补偿（WAN 2.7 手臂修复等） |

`config.json` 已在 `.gitignore` 中，不会提交到 Git。

### 2. API Key（`~/.hermes/.env`）

```bash
SELFIE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

## 使用

```bash
cd ~/.hermes/skills/luna-selfie
python3 scripts/generate_selfie.py "场景描述" [--size 720*1280]
```

| 参数 | 说明 |
|------|------|
| `prompt` | 场景描述（必填）：只写场景、穿搭、动作、光线 |
| `--size` | 分辨率，默认 `1280*1280`，自拍推荐 `720*1280` |
| `--output` | 自定义输出路径 |

脚本加载 `config.json` 后，自动将 `character` + `style` + `quality_fixes` 拼接到场景词后调 API，无需手动注入。

## License

MIT
