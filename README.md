<div align="center">

# QiVision 望衡

**以智能望诊,洞察体质平衡**
*Intelligent tongue inspection for insight into constitutional balance*

[English](#english) · [中文](#中文)

</div>

---

<a id="english"></a>
# English

## Overview

**QiVision** is an intelligent tongue-diagnosis and TCM (Traditional Chinese Medicine) pattern-differentiation Agent developed by **Qixiangli Health Technology**. Built on AI vision and classical TCM inspection theory, it helps users identify their body constitution from a tongue photo, explains the reasoning behind the result, and matches personalized wellness plans and in-house products, forming a complete closed loop:

**Identify → Plan → Product → Feedback**

QiVision is more than a one-off report. It guides standardized photo capture, outputs structured tongue features, explains the evidence behind each conclusion, and tracks changes over time based on user feedback, so the whole wellness process is clear, quantifiable and traceable.

- **Positioning:** an assistive decision-support tool for personal health management and TCM wellness.
- **Core values:** Objective identification · Professional differentiation · Precise matching · Continuous tracking.

> ⚠️ **Disclaimer:** QiVision is a wellness-support tool. It does **not** provide medical diagnosis or treatment, and its output cannot replace the advice of a licensed physician.

## Features

- **Guided capture** – shooting guidelines plus automatic checks for blur, lighting and tongue coverage, with retake prompts.
- **Structured tongue analysis** – body color, coating color/thickness, moisture, shape, teeth marks, cracks, with a confidence score.
- **Traceable differentiation** – scoring across 8 constitution types (Balanced, Qi-deficiency, Yang-deficiency, Yin-deficiency, Phlegm-dampness, Damp-heat, Blood-stasis, Qi-stagnation). Every conclusion lists its supporting evidence.
- **Personalized plan** – diet, lifestyle, exercise and things to avoid.
- **Safe product matching** – checks pregnancy, age, allergies and drug interactions; explains why each product is matched or excluded.
- **Feedback loop** – continue / adjust / stop-and-consult / recapture decisions, plus a balance-index trend across sessions.
- **Safety first** – red-flag symptoms (e.g. hemoptysis, blood in stool) trigger a medical-referral response with no product recommendation.
- **Follow-up Q&A** – ask questions about your result (Qwen LLM; falls back to templates without an API key).
- **Auditable** – every Agent step is recorded in a `trace`.

## Architecture

```
User ─► Capture Agent ─► Tongue Vision Agent ─► Syndrome Agent ─► Product Agent ─► Feedback Agent
         quality check     structured features    rules + evidence   safety check      trend & adjust
                                                        │
                                       red-flag ─► refer to a doctor (no product)
```

| Agent | File | Responsibility |
|---|---|---|
| Capture | `agents/capture.py` | Guidance, image-quality checks, tongue segmentation |
| Tongue Vision | `agents/tongue_vision.py` | Structured features via OpenCV baseline or Qwen-VL |
| Syndrome | `agents/syndrome.py` | Constitution scoring, evidence, regimen, LLM explanation |
| Product | `agents/product.py` | Product matching and contraindication checks |
| Feedback | `agents/feedback.py` | Feedback handling and longitudinal trend |

The orchestrator (`orchestrator.py`) chains these agents and persists results to SQLite. Raw tongue images are **not stored** by default.

## Quick Start

```bash
git clone <your-repo-url> && cd QiVision
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # optional: add DASHSCOPE_API_KEY to enable Qwen
qivision serve                # open http://127.0.0.1:8000
pytest -q                     # run tests
```

CLI:

```bash
qivision analyze --image tongue.jpg --symptoms fatigue,cold_limbs --medications warfarin
```

Docker:

```bash
docker build -t qivision .
docker run -p 8000:8000 -v qivision-data:/data qivision
```

## Configuration

Copy `.env.example` to `.env`:

| Variable | Default | Description |
|---|---|---|
| `QIVISION_ANALYZER` | `heuristic` | `heuristic` (local OpenCV) or `vlm` (Qwen-VL) |
| `DASHSCOPE_API_KEY` | – | Alibaba DashScope key; leave empty to disable LLM |
| `QIVISION_BASE_URL` | intl endpoint | Use `dashscope.aliyuncs.com` for mainland China, `dashscope-intl.aliyuncs.com` for international |
| `QIVISION_LLM_MODEL` | `qwen-plus` | Text model |
| `QIVISION_VLM_MODEL` | `qwen-vl-max` | Vision model |
| `QIVISION_DB_PATH` | `./data/qivision.db` | SQLite path |
| `QIVISION_MIN_BLUR` | `60` | Minimum sharpness threshold |

## API

Interactive docs are available at `/docs` (Swagger).

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/v1/capture-guide` | Photo-capture guidelines |
| GET | `/v1/symptoms` | Symptom dictionary and red flags |
| POST | `/v1/sessions/analyze` | Upload tongue image + questionnaire → full result |
| POST | `/v1/sessions/{id}/feedback` | Submit usage feedback |
| POST | `/v1/sessions/{id}/ask` | Follow-up question on a result |
| GET | `/v1/users/{uid}/trend` | Longitudinal trend |

```bash
curl -X POST http://127.0.0.1:8000/v1/sessions/analyze \
  -F image=@tongue.jpg -F user_id=u1 -F symptoms=fatigue,cold_limbs -F age=35
```

## Project Structure

```
QiVision/
├── src/qivision/
│   ├── agents/          # capture, tongue_vision, syndrome, product, feedback
│   ├── knowledge/       # syndrome rules, symptoms, products.json
│   ├── web/index.html   # demo web UI
│   ├── orchestrator.py  # multi-agent pipeline
│   ├── api.py  cli.py  llm.py  storage.py  schemas.py  config.py
├── tests/
├── Dockerfile  pyproject.toml  .env.example
└── .github/workflows/ci.yml
```

## Before Production

1. **Tongue model** – the bundled OpenCV analyzer is a heuristic baseline for demos. Train a segmentation + multi-label classification model on labeled data and implement the `TongueAnalyzer` interface.
2. **Rule review** – constitution weights in `knowledge/syndromes.py` must be reviewed by licensed TCM practitioners and calibrated with clinical data.
3. **Product catalog** – `knowledge/products.json` contains placeholder items; replace them with real ingredients, contraindications and target groups, and complete compliance review.
4. **Regulation** – tongue-diagnosis AI may be classed as medical-device software (e.g. NMPA in China, HSA in Singapore). Consult legal/regulatory advisors before launch and marketing.
5. **Privacy** – tongue images and health data are sensitive. Add user consent, encryption, access control and retention policies (e.g. PDPA).
6. **Security** – the API has no authentication or rate limiting yet; add both before deployment.

## Roadmap

- [ ] In-house tongue segmentation/classification models and annotated dataset
- [ ] Face and pulse diagnosis inputs (multimodal)
- [ ] Knowledge graph replacing rule table; 24 solar-term plans
- [ ] Automatic image alignment and visual comparison across retakes
- [ ] Mini-program / mobile app front end

---

<a id="中文"></a>
# 中文

## 项目简介

**QiVision 望衡** 是由 **Qixiangli Health Technology(七巷礼健康科技)** 自主研发的智能舌诊与中医辨证 Agent。它以 AI 视觉技术为核心,结合中医望诊理论,帮助用户通过舌象图像完成体质识别与辨证分析,并匹配个性化调理方案与自研产品,形成完整闭环:

**识别 → 方案 → 产品 → 反馈**

QiVision 不只是一次性给出结果:它会引导规范拍摄、输出结构化舌象特征、解释辨证依据,并根据用户后续反馈持续追踪变化,让调理过程更清晰、可量化、可追溯。

- **定位:** 智能舌诊辅助决策工具,服务于个人健康管理与中医调理场景。
- **核心价值:** 客观识别 · 专业辨证 · 精准匹配 · 持续追踪。

> ⚠️ **免责声明:** QiVision 为健康管理辅助工具,**不提供医疗诊断或治疗**,结果不能替代执业医师意见。

## 功能特性

- **采集引导**:拍摄指引,自动检查模糊、光线、舌体占比,不合格则提示重拍。
- **结构化舌象分析**:舌质颜色、苔色、苔厚、津液、舌形、齿痕、裂纹,并给出置信度。
- **可追溯辨证**:对 8 种体质(平和、气虚、阳虚、阴虚、痰湿、湿热、血瘀、气郁)打分,每个结论都附带依据。
- **个性化方案**:饮食、起居、运动与宜避事项。
- **安全的产品匹配**:检查孕期、年龄、过敏与药物相互作用,并说明匹配或排除的理由。
- **反馈闭环**:判断继续 / 调整 / 停用就医 / 复拍,并跟踪多次评估的平衡指数趋势。
- **安全优先**:出现咳血、便血等红旗症状时,只建议就医,不推荐产品。
- **追问问答**:可就结果继续提问(接入通义千问;未配置密钥时使用模板回复)。
- **全程可审计**:每个 Agent 的执行步骤都记录在 `trace` 中。

## 系统架构

```
用户 ─► 采集引导 Agent ─► 舌象分析 Agent ─► 辨证与方案 Agent ─► 产品匹配 Agent ─► 反馈追踪 Agent
         质量检查/重拍      结构化舌象特征      规则+依据可追溯      禁忌/过敏/药物检查    趋势分析/方案调整
                                                    │
                                      红旗症状 ─► 建议就医(不推荐产品)
```

| Agent | 文件 | 职责 |
|---|---|---|
| 采集引导 | `agents/capture.py` | 拍摄指引、图像质量检查、舌体分割 |
| 舌象分析 | `agents/tongue_vision.py` | OpenCV 基线或通义千问视觉模型提取结构化特征 |
| 辨证与方案 | `agents/syndrome.py` | 体质打分、依据追溯、调理方案、LLM 受约束解释 |
| 产品匹配 | `agents/product.py` | 产品匹配与禁忌检查 |
| 反馈追踪 | `agents/feedback.py` | 反馈处理与纵向趋势 |

编排层 `orchestrator.py` 负责串联各 Agent,并将结果存入 SQLite。默认**不保存**原始舌象图片。

## 快速开始

```bash
git clone <你的仓库地址> && cd QiVision
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # 可选:填入 DASHSCOPE_API_KEY 启用通义千问
qivision serve                # 浏览器打开 http://127.0.0.1:8000
pytest -q                     # 运行测试
```

命令行:

```bash
qivision analyze --image tongue.jpg --symptoms fatigue,cold_limbs --medications 华法林
```

Docker:

```bash
docker build -t qivision .
docker run -p 8000:8000 -v qivision-data:/data qivision
```

## 配置说明

复制 `.env.example` 为 `.env`:

| 变量 | 默认值 | 说明 |
|---|---|---|
| `QIVISION_ANALYZER` | `heuristic` | `heuristic`(本地 OpenCV)或 `vlm`(通义千问视觉模型) |
| `DASHSCOPE_API_KEY` | 空 | 阿里云 DashScope 密钥;留空则不启用大模型 |
| `QIVISION_BASE_URL` | 国际站 | 中国大陆用 `dashscope.aliyuncs.com`,国际站用 `dashscope-intl.aliyuncs.com` |
| `QIVISION_LLM_MODEL` | `qwen-plus` | 文本模型 |
| `QIVISION_VLM_MODEL` | `qwen-vl-max` | 视觉模型 |
| `QIVISION_DB_PATH` | `./data/qivision.db` | SQLite 路径 |
| `QIVISION_MIN_BLUR` | `60` | 清晰度最低阈值 |

## API 接口

交互式文档见 `/docs`(Swagger)。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/v1/capture-guide` | 拍摄指引 |
| GET | `/v1/symptoms` | 症状字典与红旗症状 |
| POST | `/v1/sessions/analyze` | 上传舌象 + 问诊,返回完整结果 |
| POST | `/v1/sessions/{id}/feedback` | 提交使用反馈 |
| POST | `/v1/sessions/{id}/ask` | 就结果追问 |
| GET | `/v1/users/{uid}/trend` | 纵向趋势 |

```bash
curl -X POST http://127.0.0.1:8000/v1/sessions/analyze \
  -F image=@tongue.jpg -F user_id=u1 -F symptoms=fatigue,cold_limbs -F age=35
```

## 目录结构

```
QiVision/
├── src/qivision/
│   ├── agents/          # 采集、舌象、辨证、产品、反馈
│   ├── knowledge/       # 辨证规则、症状字典、products.json
│   ├── web/index.html   # 演示网页
│   ├── orchestrator.py  # 多 Agent 编排
│   ├── api.py  cli.py  llm.py  storage.py  schemas.py  config.py
├── tests/
├── Dockerfile  pyproject.toml  .env.example
└── .github/workflows/ci.yml
```

## 上线前必须完成

1. **舌象模型**:内置 OpenCV 分析器只是演示用的启发式基线。请用标注数据训练舌体分割与多标签分类模型,并实现 `TongueAnalyzer` 接口替换。
2. **规则审定**:`knowledge/syndromes.py` 中的体质权重需由中医师审定,并用临床数据校准。
3. **产品库**:`knowledge/products.json` 为占位示例,请替换为真实成分、禁忌与适用人群,并完成合规审核。
4. **监管合规**:舌诊 AI 可能被认定为医疗器械软件(如中国 NMPA、新加坡 HSA)。上线与宣传前请咨询法务或注册顾问。
5. **隐私保护**:舌象与健康信息属敏感数据,需加入用户同意、加密、访问控制与留存策略(如 PDPA、个人信息保护法)。
6. **接口安全**:API 目前没有鉴权与限流,部署前请补上。

## 路线图

- [ ] 自研舌象分割/分类模型与标注数据集
- [ ] 面诊、脉诊多模态输入
- [ ] 用知识图谱替代规则表,加入 24 节气方案
- [ ] 复拍自动对齐与舌象变化可视化
- [ ] 小程序 / App 前端

---

© 2026 Qixiangli Health Technology. All rights reserved.
