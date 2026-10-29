# QiVision 望衡

> **以智能望诊,洞察体质平衡**

QiVision 是由 **Qixiangli Health Technology** 自主研发的智能舌诊与中医辨证 Agent。以 AI 视觉为核心,结合中医望诊理论,帮助用户通过舌象图像完成体质识别与辨证分析,并匹配个性化调理方案与自研产品,形成 **识别 → 方案 → 产品 → 反馈** 的完整闭环。

**核心价值:** 客观识别 · 专业辨证 · 精准匹配 · 持续追踪

> ⚠️ QiVision 是健康管理与中医调理场景下的辅助决策工具,**不提供医疗诊断**,结果不能替代执业医师意见。

## 架构:多 Agent 协作

```
用户 ─► 采集引导 Agent ─► 舌象分析 Agent ─► 辨证与方案 Agent ─► 产品匹配 Agent ─► 反馈与追踪 Agent
         质量检查/重拍      结构化舌象特征      规则+证据可追溯      禁忌/过敏/药物检查     复拍对比/趋势/调整
                                                    │
                                        红旗症状 ─► 建议就医(不推荐产品)
```

| Agent | 文件 | 职责 | 技术 |
|---|---|---|---|
| 采集引导 | `agents/capture.py` | 拍摄指引、模糊/光线/舌体占比检查 | OpenCV |
| 舌象分析 | `agents/tongue_vision.py` | 输出舌质/苔色/苔厚/津液/舌形/齿痕/裂纹 | OpenCV 基线 或 Qwen-VL |
| 辨证与方案 | `agents/syndrome.py` | 8 种体质打分、依据追溯、调理方案、LLM 受约束解释 | 规则库 + Qwen |
| 产品匹配 | `agents/product.py` | 体质→产品打分;孕期/年龄/过敏/药物相互作用检查;给出匹配与排除理由 | 产品知识库 |
| 反馈追踪 | `agents/feedback.py` | 使用反馈→继续/调整/停用就医/复拍;平衡指数趋势 | 纵向对比 |

编排层 `orchestrator.py` 记录每个 Agent 的执行轨迹(`trace`),保证可追溯。

## 快速开始

```bash
git clone <your-repo-url> && cd QiVision
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # 可选:填入 DASHSCOPE_API_KEY 启用通义千问
qivision serve              # 打开 http://127.0.0.1:8000
pytest -q                   # 运行测试
```

命令行分析:

```bash
qivision analyze --image tongue.jpg --symptoms fatigue,cold_limbs --medications 华法林
```

Docker:

```bash
docker build -t qivision . && docker run -p 8000:8000 -v qivision-data:/data qivision
```

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/v1/capture-guide` | 拍摄指引 |
| GET | `/v1/symptoms` | 症状字典与红旗症状 |
| POST | `/v1/sessions/analyze` | 上传舌象 + 问诊 → 辨证/方案/产品 |
| POST | `/v1/sessions/{id}/feedback` | 提交使用反馈 |
| POST | `/v1/sessions/{id}/ask` | 基于本次结果的追问 |
| GET | `/v1/users/{uid}/trend` | 纵向趋势 |

交互文档:`/docs`(Swagger)。

## 运行模式

- `QIVISION_ANALYZER=heuristic`(默认):本地 OpenCV 基线,无需密钥,**仅用于 MVP 演示**。
- `QIVISION_ANALYZER=vlm`:调用通义千问视觉模型提取舌象特征,失败自动回退基线。
- 未配置 `DASHSCOPE_API_KEY` 时,解释与追问使用模板,系统依然可运行。

## 上线前必须完成(重要)

1. **舌象模型**:基线阈值只是启发式,请用标注数据训练舌体分割 + 多标签分类模型,实现 `TongueAnalyzer` 接口替换。
2. **规则库审定**:`knowledge/syndromes.py` 的权重需由中医师审定并用临床数据校准。
3. **产品库**:`knowledge/products.json` 为演示占位,请替换为自研产品真实成分、禁忌、适用人群,并经合规审核。
4. **合规**:舌诊 AI 可能被监管认定为医疗器械软件(如中国 NMPA、新加坡 HSA 等),产品宣传与功能边界需先咨询法务/注册顾问。
5. **隐私**:舌象与健康信息属敏感个人数据。当前默认不保存原图;上线需加用户同意、加密、访问控制与数据留存策略(如 PDPA / 个保法)。
6. **鉴权与限流**:API 目前无认证,部署前请加入。

## 路线图

- [ ] 自研舌象分割与分类模型、舌象数据集与标注规范
- [ ] 面诊 / 脉诊多模态输入
- [ ] 知识图谱替代规则表,24 节气方案
- [ ] 复拍自动对齐与舌象变化可视化
- [ ] 小程序 / App 前端

© 2026 Qixiangli Health Technology
