# 加密货币聪明钱监控系统 🚀

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![Language](https://img.shields.io/badge/language-中文%20%7C%20English-yellow.svg)]()

> 实时加密货币市场监控系统，追踪 Hyperliquid 大户持仓并可视化 OKX 永续合约数据。使用 **AI 辅助开发**在数天内完成，展示快速原型开发和多数据源集成能力。

**👨‍💻 作者**: Howard Zeng
[English](README_EN.md) | 中文

---

## 📌 项目亮点

- **🤖 AI 辅助开发**: 利用 Claude Code 在数天内快速构建生产级应用
- **📊 多数据源集成**: 结合 Hyperliquid 大户追踪 + OKX 实时市场数据
- **🎨 专业 UI/UX**: 深色 DeFi 风格界面，实时数据可视化
- **🌐 双语支持**: 完整的中英文界面切换，95%+ UI 覆盖率
- **🔄 实时监控**: 可自定义间隔的自动刷新市场数据
- **📈 高级可视化**: 热力图、情绪分析和涨跌榜仪表板

---

## 🎯 核心功能

### 🐋 Hyperliquid 大户追踪
- 通过网页爬虫（Selenium）监控 Hyperliquid 平台大户持仓
- 一键数据刷新和 Excel 导出
- 多维度筛选（币种、时间、金额）
- 清晰的表格视图展示持仓详情
- 双击查看大户详细信息（盈亏统计、持仓明细、交易历史）

### 📊 OKX 市场分析
- **实时数据表格**: TOP 50 永续合约，自动刷新（10秒间隔）
- **市值热力图**: TOP 20 代币，按交易量和价格变化可视化
- **情绪分析**: 市场概览，多空统计
- **涨跌榜**: 涨幅和跌幅排行榜（TOP 10）

### 🌐 多语言界面
- **中英文切换**: 一键切换界面语言，无需重启
- **95%+ 覆盖率**: 几乎所有 UI 元素都支持翻译
- **实时更新**: 包括主界面、筛选面板、表格列、详情窗口等
- **专业术语**: 金融术语准确翻译

### 🎨 用户界面
- 专业深色主题（DeFi 风格设计）
- 响应式布局，选项卡导航
- 盈亏颜色编码指示器
- 针对高频数据更新优化

---

## 🛠️ 技术栈

| 类别 | 技术 |
|----------|-------------|
| **语言** | Python 3.8+ |
| **GUI 框架** | Tkinter + ttk（现代主题组件） |
| **网页爬虫** | Selenium WebDriver + ChromeDriver |
| **API 集成** | OKX 公开 API (REST) |
| **数据可视化** | Matplotlib + Squarify（树状图） |
| **数据处理** | NumPy，类 Pandas 操作 |
| **HTTP 客户端** | Requests 库 |
| **国际化** | 自定义语言管理系统（观察者模式） |

---

## 🚀 快速开始

### 前置要求
- Python 3.8 或更高版本
- 互联网连接（用于 API 访问）
- Chrome 浏览器（用于网页爬虫）
- Windows/Linux/macOS

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/zengh430/crypto-smart-money-monitor.git
cd crypto-smart-money-monitor
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

或使用提供的批处理脚本（Windows）：
```bash
安装依赖.bat
```

3. **运行应用程序**
```bash
python hyperliquid_monitor.py
```

或使用快速启动脚本（Windows）：
```bash
快速启动.bat
```

---

## 📖 使用指南

### Hyperliquid 监控
1. 启动应用并切换到 **"原始数据"** 或 **"持仓数据"** 标签页
2. 点击 **"刷新数据"** 获取最新的大户持仓
3. 使用左侧筛选器按币种/时间/金额筛选
4. **双击任意行**查看大户详细信息：
   - 总盈亏、24h/48h/7天/30天盈亏统计
   - 盈亏趋势图表
   - 当前持仓明细
   - 历史交易记录
   - 充值提现记录
5. 导出数据到 Excel 进行进一步分析

### OKX 市场监控
1. **数据表格标签页**:
   - 点击"刷新"获取 TOP 50 代币实时行情
   - 启用"自动刷新"实现 10 秒自动更新
   - 按交易量、价格变化或市值排序

2. **热力图标签页**:
   - 将 TOP 20 代币可视化为树状图
   - 方块大小 = 交易量
   - 颜色 = 价格变化（绿色=涨，红色=跌）

3. **市场分析标签页**:
   - 查看整体市场情绪
   - 查看 TOP 10 涨幅和跌幅榜
   - 监控多空分布

### 语言切换
- 点击右上角的 **🌐 English** 按钮切换到英文
- 点击 **🌐 中文** 按钮切换回中文
- 所有界面元素实时更新，无需重启

---

## 🏗️ 项目结构

```
crypto-smart-money-monitor/
├── hyperliquid_monitor.py    # 主应用程序（GUI + Hyperliquid 爬虫）
├── language_config.py         # 语言配置和管理模块
├── okx_trader.py              # OKX API 客户端模块
├── config_example.py          # 配置模板
├── okx_config.example.json    # OKX 配置示例
├── requirements.txt           # Python 依赖
├── .gitignore                 # Git 忽略规则
├── README.md                  # 中文文档（本文件）
├── README_EN.md               # 英文文档
├── 安装依赖.bat                # Windows 依赖安装脚本
└── 快速启动.bat                # Windows 快速启动脚本
```

---

## ⚙️ 配置说明

复制 `config_example.py` 为 `config.py` 并自定义：

```python
# 刷新间隔
OKX_AUTO_REFRESH_INTERVAL = 10  # 秒
HYPERLIQUID_REFRESH_INTERVAL = 30  # 秒

# 主题颜色
THEME = "dark"  # "dark" 或 "light"

# 监控币种
MONITORED_COINS = ["BTC", "ETH", "SOL", ...]  # 自定义监控列表

# 默认语言
DEFAULT_LANGUAGE = "zh"  # "zh" 为中文, "en" 为英文
```

**OKX API 配置**（可选）:
- 复制 `okx_config.example.json` 为 `okx_config.json`
- 如果需要私有 API 功能，填入你的 API 密钥
- 公开数据功能无需 API 密钥

---

## 🔧 API 参考

### OKX 公开 API
- **基础 URL**: `https://www.okx.com`
- **速率限制**: 20 次请求 / 2 秒
- **无需 API 密钥**（公开端点）
- **文档**: [OKX API Docs](https://www.okx.com/docs-v5/en/)

### Hyperliquid 数据
- **来源**: CoinGlass 通过 Selenium 网页爬虫
- **更新频率**: 手动或计划刷新
- **数据点**: 持仓大小、入场价格、盈亏、时间戳、交易历史

---

## 🌟 核心技术成就

### 1. **AI 辅助快速开发**
- 使用 AI 辅助编程（Claude Code）在**数天内**完成生产级应用
- 展示 10 倍以上的生产力提升
- 快速原型到生产级代码的转换

### 2. **多数据源集成**
- 无缝结合网页爬虫（Hyperliquid）和 REST API（OKX）
- 处理异步数据更新和速率限制
- 智能错误处理和自动重试机制

### 3. **实时数据可视化**
- 自定义 Matplotlib 与 Tkinter 集成
- 高效重绘实现流畅更新
- 响应式热力图生成

### 4. **国际化架构**
- 观察者模式实现语言切换
- 150+ UI 元素的完整翻译
- 实时界面更新，无需重启

### 5. **健壮的错误处理**
- 优雅的 API 故障恢复
- 用户友好的错误消息
- 自动重试机制

---

## 🎓 学习成果

本项目展示了以下能力：

- **网页爬虫**: Selenium 自动化，动态内容处理，反爬虫技术
- **API 集成**: RESTful API 调用，速率限制，错误处理
- **GUI 开发**: Tkinter 事件循环，多线程，响应式设计
- **数据可视化**: Matplotlib 自定义，实时图表更新
- **软件架构**: MVC 模式，观察者模式，单例模式
- **国际化**: i18n 实现，语言管理系统
- **金融科技**: 加密货币市场数据，交易指标
- **软件工程**: 代码组织，配置管理，文档

---

## 🚀 未来增强

- [ ] 添加更多交易所（Binance、Bybit 等）
- [ ] 实现自定义警报和通知
- [ ] 投资组合跟踪和性能分析
- [ ] 导出到多种格式（CSV、JSON、SQL）
- [ ] 添加交易策略回测模块
- [ ] 更多语言支持（日语、韩语等）
- [ ] 暗色/亮色主题切换
- [ ] Web 仪表板（Flask/FastAPI + React）
- [ ] Docker 部署支持
- [ ] 单元测试和 CI/CD 流程

---

## 🤝 贡献指南

欢迎贡献！请遵循以下准则：

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- **OKX** 提供公开 API 访问
- **Hyperliquid** 提供市场数据
- **CoinGlass** 提供数据聚合服务
- **Claude Code** (Anthropic) 用于 AI 辅助开发
- 开源社区提供的库和工具

---

## 📬 联系方式

- **作者**: Howard Zeng
- **GitHub**: [@zengh430](https://github.com/zengh430)
- **LinkedIn**: [Howard Zeng](https://linkedin.com/in/yourprofile)
- **Email**: zengh430@gmai.com

---

## ⚠️ 免责声明

本软件**仅供教育和研究目的**。这不是金融建议。加密货币交易涉及重大风险。在做出投资决策之前，请务必自行研究（DYOR）并咨询金融专业人士。

作者不对因使用本软件而导致的任何损失负责。

---

<p align="center">
  <strong>使用 AI 辅助开发 ❤️ | 数天而非数月构建</strong><br>
  <em>Built with Claude Code by Howard Zeng</em>
</p>
