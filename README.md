# 真实交易成长记录流水线系统

这是一个本地运行的个人交易复盘与系统验证工具。它用于结构化记录交易、用 R 值统计交易结果、生成周报/月报，并把私密交易记录转成适合公开发布的脱敏复盘内容。

重要边界：

- 本项目仅用于个人交易复盘和系统验证。
- 不构成任何投资建议。
- 不承诺收益。
- 不鼓励高频交易。
- 不鼓励高杠杆。
- 不提供实时买卖点。
- 公开内容应优先展示风控、执行和复盘，而不是炫耀收益。

## 功能

- SQLite 本地保存交易记录。
- Streamlit 本地 Web UI。
- 交易录入、列表筛选、详情编辑、删除确认。
- 统计总 R、平均 R、胜率、盈亏比、期望值、最大回撤、连续亏损、计划内比例、A/B/C 级统计。
- 图表展示累计 R 曲线、回撤曲线、月度 R、等级收益、计划内/计划外收益、情绪分数关系、追单趋势。
- 生成每日复盘、周报、月报 Markdown。
- 根据私密交易生成公开脱敏内容。
- 检查公开内容中的导流、喊单、收益诱导和高风险词，并提供替换建议。
- 支持上传截图到本地 `screenshots/` 目录。

## 项目结构

```text
trade-journal-pipeline/
├── README.md
├── requirements.txt
├── app.py
├── config.yaml
├── data/
│   ├── trades.db
│   └── exports/
├── screenshots/
│   ├── private/
│   └── public/
├── templates/
│   ├── daily_review.md.j2
│   ├── weekly_report.md.j2
│   ├── monthly_report.md.j2
│   └── public_post.md.j2
├── src/
│   ├── database.py
│   ├── models.py
│   ├── analytics.py
│   ├── reports.py
│   ├── sanitizer.py
│   ├── validators.py
│   └── utils.py
└── tests/
    └── test_analytics.py
```

`data/trades.db` 会在首次启动或点击“初始化数据库”时自动创建。

## 安装

进入项目目录：

```bash
cd trade-journal-pipeline
```

创建虚拟环境：

```bash
python -m venv .venv
```

Windows PowerShell 激活：

```bash
.\.venv\Scripts\Activate.ps1
```

macOS/Linux 激活：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 初始化数据库

启动应用后会自动初始化 SQLite 数据库。也可以在首页侧边栏点击“初始化数据库”。

如果想导入示例交易数据，在首页没有交易记录时点击“导入示例交易数据”。

## 启动

```bash
streamlit run app.py
```

浏览器打开 Streamlit 提示的本地地址，一般是：

```text
http://localhost:8501
```

## 部署

### 不推荐直接部署到 Vercel

Vercel 更适合 Next.js、静态站点和 Serverless API。它的 Python 运行时面向 ASGI/WSGI 应用，而本项目是 Streamlit 长运行 Web 应用，并且依赖 SQLite、Markdown 导出和截图文件持久化。

如果一定要上 Vercel，需要把前端重写成 Next.js，把后端改成 API Route，并把 SQLite 改成云数据库。这已经不是当前 Streamlit MVP 的直接部署了。

### 推荐方案：Render

本项目已提供：

- `Dockerfile`
- `render.yaml`
- `APP_DATA_DIR` 持久化数据目录支持

Render 部署步骤：

1. 把项目推送到 GitHub 仓库。
2. 在 Render 新建 Blueprint，选择该仓库。
3. Render 会读取 `render.yaml`，用 Docker 部署 Web Service。
4. `render.yaml` 会把持久磁盘挂载到 `/app/data`。
5. SQLite 数据库、导出报告、截图都会保存在 `/app/data` 下。

部署后的数据位置：

```text
/app/data/trades.db
/app/data/exports/
/app/data/screenshots/private/
/app/data/screenshots/public/
```

也可以手动创建 Render Web Service：

- Environment：Docker
- Dockerfile：`Dockerfile`
- Disk mount path：`/app/data`
- Environment Variable：`APP_DATA_DIR=/app/data`

### 其他可选平台

- Railway：适合 Docker 部署，但需要配置持久卷。
- Fly.io：适合 Docker 部署，也需要配置 volume。
- Streamlit Community Cloud：启动简单，但更适合演示；涉及私密交易数据和持久文件时要谨慎。

## 配置

配置文件在 `config.yaml`：

```yaml
risk:
  max_single_trade_r: 1
  max_daily_loss_r: 1.5
  max_weekly_loss_r: 3
  max_monthly_loss_r: 5
  pause_after_consecutive_losses: 3

content:
  add_disclaimer: true
  public_symbol_default: "品种A"
  forbidden_words_check: true

project:
  name: "180天真实交易系统验证"
  main_timeframe: "1H"
  entry_timeframe: "5M"
  allow_1m_signal: false
```

首页会根据风控配置提示今日、本周、本月和连续亏损状态。

## 如何使用

1. 打开“录入交易”，填写交易基础信息、R 结果、执行信息、心理纪律信息和截图。
2. 打开“交易列表”，按日期、品种、策略、等级、计划内状态筛选，查看、编辑或删除交易。
3. 打开“统计图表”，查看累计 R 曲线、回撤和分组统计。
4. 打开“报告导出”，生成每日复盘、周报或月报 Markdown，可下载或保存到 `data/exports/`。
5. 打开“公开内容”，选择一笔交易生成脱敏公开复盘，并自动做敏感词检查。

## 数据位置

- SQLite 数据库：`data/trades.db`
- Markdown 导出：`data/exports/`
- 私密截图：`screenshots/private/`
- 公开截图：`screenshots/public/`

## 备份

定期复制以下目录即可完成核心数据备份：

```text
data/
screenshots/
config.yaml
```

建议把备份保存到外置硬盘或你信任的私有云盘中。公开发布内容前，请再次人工检查是否包含真实账户、具体平台、链接、返佣、喊单或诱导表述。

## 测试

```bash
pytest
```

当前测试覆盖：

- 总 R 计算
- 胜率计算
- 平均盈利 R
- 平均亏损 R
- 最大回撤
- 最大连续亏损
- 计划内比例
- A/B/C 级统计

## 后续扩展建议

- 增加标签系统和多账户管理。
- 增加 HTML 报告导出。
- 增加更细的截图管理和图片预览。
- 增加数据加密和一键备份。
- 增加从成交记录 CSV 导入，但默认关闭交易所 API 接入。
