# PA Agent — AI K线分析辅助工具（桌面端）

**交流 QQ 群：922829084**

---

面向主观交易者的 **价格行为（Price Action）** AI 辅助决策工具。从 **币安 Binance / OKX** 的公共 REST 接口读取加密货币现货 K 线，将结构化 K 线数据与预计算特征送入大模型做**两阶段分析**（市场诊断 → 交易决策），**不是**截图识图，**不连接券商、不执行下单**。

---

## 主要功能

- 📈 **双数据源（加密货币）**：币安 Binance、OKX，现货 USDT 交易对，公共行情接口，无需交易所 API Key
- 🧠 **两阶段 AI 分析**：市场诊断 → 策略路由 → 交易决策（限价/突破/市价或不下单）
- 🔄 **增量分析与新K线自动分析**：新增 K 线时复用上次结论；开启「新K线收盘自动分析」后不轮询，只在每根 1h 收盘时获取一次数据，成功后自动提交一轮分析
- ⏱️ **内置计时器**：收盘调度使用程序内的 Qt `QTimer`，不是系统计划任务；关闭窗口即停止并清理后台线程，不留后台进程
- 🌳 **决策树可视化**：Apple Liquid Glass 风格可交互流程图，自动播放闸门→策略路径动画
- 🔮 **未来走势预期**：AI 预测下一根 K 线方向和下一个市场周期位置
- 💬 **分析后自由追问**：完整对话会话管理器，实时推理流 + Token 进度条，对话历史持久化
- 📚 **经验库**：按周期位置检索历史案例供分析参考
- 📝 **完整落盘**：Prompt、原始响应、诊断/决策 JSON、Token 用量、追问记录
- 🛡️ **可配置校验体系**：JSON 校验、一致性检查、语义校验、截断修复、失败自动重试
- 🔒 **API Key** 本地加密存储

---

## 环境要求

| 项目     | 要求                                                                    |
| -------- | ----------------------------------------------------------------------- |
| 操作系统 | Windows 10 / 11                                                          |
| Python   | 3.11+                                                                    |
| 数据源   | 币安 Binance 或 OKX（现货 USDT 交易对，**二选一**，无需 API Key）          |
| 网络     | 可访问币安/OKX 行情接口；OKX 在国内网络通常需要代理；另需可访问 AI API      |

---

## 快速启动（Windows）

```bat
python run.py
```

或直接双击项目根目录的 `启动PA_Agent.bat`（会自动检测本机 7897 代理并注入环境变量）。
首次启动后在「AI 模型设置」里填写 DeepSeek API Key 即可。

## 云电脑 / 新机器部署（Windows）

```bat
git clone https://github.com/tosyazz/PA_Agent.git
cd PA_Agent
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
python run.py
```

首次启动会生成 `config/settings.json`；API Key、飞书 Webhook 等本地配置不会提交到仓库。
若云电脑访问币安/OKX 需要代理，先设置 `HTTP_PROXY` / `HTTPS_PROXY`，或确认本机 7897 端口有代理后再双击 `启动PA_Agent.bat`。

---

## 详细说明

完整操作界面说明见 [`PA_Agent使用文档.md`](PA_Agent使用文档.md)，配置字段说明见 [`config/README.md`](config/README.md)。

---

**免责声明**：本工具仅供学习与研究，不构成投资建议。交易有风险，决策后果自负。

本项目采用 [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE) 发布。

---

## 群友反馈榜单

感谢群友的使用反馈与鼓励，以下为群友评价截图（按时间从早到晚排列）：

<p align="center">
  <img src="qunyou/BD58CB2D6E4F45CC17CF832C506A982C.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/653EC872A0D6883A34B7B37B692C8B1D.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260619-205140.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260619-235505.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260620-150714.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260620-150833.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260620-220824.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260623-125929.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/91003065F07407E92B50964AE7F8A944.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260624-191001.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260628-014043.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260628-213700.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260629-163821.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ20260701-212522.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/BB4AE8110A7011426BD29D5CE8B5F73B.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/F383D366F2254692418DB18AAA617ACE.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/AD48DF6289CB6A9D51FE0B8EE2EC38C2.jpg" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/F61C8DCDB67924B64B33403D20047E0B.png" alt="群友反馈" width="480" />
</p>
<p align="center">
  <img src="qunyou/QQ_1783089951396.png" alt="群友反馈" width="480" />
</p>

---

## 打赏与支持

如果你觉得这个程序对你有帮助的话，可以打赏激励作者继续优化程序，感谢你的支持和鼓励！

（作者会优先解决打赏人的问题，因为人太多了！回复不过来！）

<p align="center">
  <img src="赞助码.jpeg" alt="打赏二维码" width="420" />
</p>
