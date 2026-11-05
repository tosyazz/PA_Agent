# PA Agent 智能体安装说明

> 把本文件完整交给负责安装的智能体。目标是：在 **Windows 10/11 云电脑或本机** 上把 PA Agent 跑起来，并验证行情与界面正常。
>
> 项目是 **PyQt6 桌面程序**，不是 Web 服务；需要可交互的 Windows 桌面会话（RDP 也可以），不能只在无桌面的纯命令行容器里运行。

---

## 0. 项目信息

| 项目 | 内容 |
| --- | --- |
| GitHub | https://github.com/tosyazz/PA_Agent |
| 默认分支 | `main` |
| 启动入口 | `run.py` |
| Python 包 | `pa_agent` |
| 运行平台 | Windows 10 / 11 |
| Python | 3.11+，本项目在 3.12 上验证 |
| 数据源 | 币安 Binance / OKX 公共 REST，现货 USDT 交易对，不需要交易所 API Key |
| AI | OpenAI 兼容接口，默认 DeepSeek（`https://api.deepseek.com`，`deepseek-flash`） |
| 本地配置 | `config/settings.json`，已被 `.gitignore` 忽略，**不会**从仓库下载 |

项目默认只做 **1h 周期**；行情不会轮询，点击「获取数据」单次拉取，开启「收盘自动分析」后只在每根 1h 收盘时拉取一次。

---

## 1. 安装前检查

在 **cmd**（不是 Jupyter/Spyder）中执行：

```bat
ver
git --version
py -3.12 --version
```

要求：

- 输出包含 `Windows`。
- Git 可用。
- Python 3.11 或 3.12 可用；若 `py -3.12` 不存在，改用 `py -3.11` 或 `python`，并保证版本 ≥ 3.11。

云电脑分辨率建议 **至少 1920×1080**。程序窗口按 1920×1080 固定布局设计，分辨率过低会导致窗口超出屏幕。

---

## 2. 克隆项目

建议放在短英文路径，避免中文路径引发 Qt/编码问题：

```bat
cd /d C:\
git clone https://github.com/tosyazz/PA_Agent.git
cd PA_Agent
```

如果目录已存在，先确认是否是同一个仓库，不要直接覆盖用户改动：

```bat
git remote -v
git status
```

---

## 3. 创建虚拟环境并安装依赖

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e .
```

说明：

- 必须使用 `.venv\Scripts\python.exe`，不要用系统 Python 混装。
- `pip install -e .` 会安装 PyQt6、pyqtgraph、numpy、pandas、openai、pydantic、cryptography、pywin32 等依赖。
- 如果 pip 下载慢，可先配置国内镜像，例如：
  ```bat
  .venv\Scripts\python.exe -m pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```
- 安装完成后做一次导入检查：
  ```bat
  .venv\Scripts\python.exe -c "import pa_agent; print('pa_agent import ok')"
  ```

---

## 4. 初始化本地配置

```bat
copy config\settings.example.json config\settings.json
```

`config\settings.json` 只存在于本机，包含模型地址、模型名、数据源、周期等设置。**不要把该文件提交回 Git**。

默认值通常为：

- `general.last_data_source`: `binance`
- `general.last_symbol`: `BTCUSDT`
- `general.last_timeframe`: `1h`
- `provider.base_url`: `https://api.deepseek.com`
- `provider.model`: `deepseek-flash`

---

## 5. 网络与代理

PA Agent 通过公共接口访问币安/OKX：

- 币安优先使用 `https://data-api.binance.vision`，失败时回退 `https://api.binance.com`。
- OKX 在国内网络通常需要代理；币安在部分网络也可能返回 HTTP 451。
- 如果本机 Clash/Mihomo 的 **7897** 端口在监听，直接双击 `启动PA_Agent.bat` 会自动注入：
  ```bat
  HTTP_PROXY=http://127.0.0.1:7897
  HTTPS_PROXY=http://127.0.0.1:7897
  ```
- 如果代理端口不是 7897，先手动设置环境变量再启动：
  ```bat
  set HTTP_PROXY=http://127.0.0.1:你的端口
  set HTTPS_PROXY=http://127.0.0.1:你的端口
  .venv\Scripts\python.exe run.py
  ```

不要为了绕过网络问题修改行情源代码；先确认代理和网络可达。

---

## 6. 启动程序

方式一（推荐给智能体，能看到控制台报错）：

```bat
.venv\Scripts\python.exe run.py
```

方式二（用户日常使用）：

```bat
启动PA_Agent.bat
```

启动成功的判断：

1. 出现标题为 `PA Agent — Trading Terminal` 的窗口。
2. 顶部显示 `Price Action`、`Spot`、数据源 `币安 Binance`、交易对 `BTCUSDT`、周期 `1h`。
3. 点击「获取数据」后，价格和 K 线图更新，底部流程条「数据」变为「已就绪」。
4. 窗口大小应为 1920×1080 左右（高 DPI 下为逻辑尺寸）。

首次启动如果没有 API Key，会弹出「需要配置 API Key」提示。此时：

- **不要伪造或猜测 API Key。**
- 请用户在「AI 模型设置」中填写自己的 DeepSeek（或其他 OpenAI 兼容服务）Key，保存后再提交分析。
- 行情和 K 线不需要 API Key，可以先验证行情是否正常。

---

## 7. 安装后自检

### 7.1 基础检查

```bat
.venv\Scripts\python.exe -m compileall -q pa_agent
.venv\Scripts\python.exe -c "from pa_agent.main import main; print('main import ok')"
```

### 7.2 可选：单元 + 非 live 集成测试

```bat
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest tests/unit tests/integration -q -m "not live"
```

注意：

- 测试需要 Qt 环境；无桌面会话时 GUI 测试可能失败，这不一定代表安装失败。
- 不要在测试里使用真实 API Key；`live` 标记的测试默认跳过。
- 如果只需要让程序跑起来，7.1 通过即可。

### 7.3 数据源连通性（可选）

用程序界面点击「获取数据」是最直接的验证。若命令行验证，可在仓库根目录执行：

```bat
.venv\Scripts\python.exe -c "from pa_agent.data.binance_source import BinanceSource; s=BinanceSource(); b=s.latest_snapshot(20); print(len(b), b[0].close)"
```

OKX 需要代理时，先 `set HTTP_PROXY/HTTPS_PROXY`，再执行类似检查。

---

## 8. 常见问题

| 现象 | 处理 |
| --- | --- |
| `ModuleNotFoundError: pa_agent` | 确认当前目录是仓库根目录，且已执行 `pip install -e .`；不要用系统 Python。 |
| `No module named PyQt6` | 装到了错误的 Python；用 `.venv\Scripts\python.exe -m pip ...`。 |
| Qt 报 `could not find the Qt platform plugin "windows"` | 确认在 Windows 桌面会话中运行；安装 VC++ 运行库；不要用无 GUI 的容器。 |
| 窗口闪退 | 查看 `logs\crash.log` 和 `logs\pa_agent.log`；通常是依赖、显卡驱动或 Qt 插件问题。 |
| 币安 HTTP 451 / OKX 403 | 配置代理后重启；确认 `HTTP_PROXY`、`HTTPS_PROXY` 在当前进程生效。 |
| 提示未配置 API Key | 让用户在 GUI 设置中填写；行情功能可先不配置。 |
| 窗口超出屏幕 | 云桌面分辨率调到至少 1920×1080；不要用缩放异常的远程桌面。 |
| `pip install` 卡住/超时 | 换 PyPI 镜像；确认网络可访问 pypi.org 或镜像站。 |
| `pywin32` 安装失败 | 使用 Python 3.12 官方安装包，安装时勾选 pip；必要时安装 Visual C++ Build Tools。 |

日志位置：

- `logs\pa_agent.log`
- `logs\crash.log`

---

## 9. 安全与仓库规则

- **不要**提交 `config/settings.json`、`config/exception_state.json`、`.env`、`logs/`、`records/`、`experience/`、`trade_records/`。
- 仓库里不应出现真实 API Key、飞书 Webhook、代理账号密码。
- 如果误把 Key 写进文件或提交，立即到服务商处作废并轮换。
- 安装智能体只做“克隆、装依赖、初始化配置、启动、验证”，不要修改业务代码或替换数据源。

---

## 10. 智能体完成标准

安装完成后请向用户报告：

1. 项目路径（例如 `C:\PA_Agent`）。
2. Python 与虚拟环境路径。
3. `pip install -e .` 是否成功。
4. `compileall` / `main import ok` 是否成功。
5. 是否成功启动 GUI，窗口是否可见。
6. 是否成功点击「获取数据」并出现 K 线。
7. 是否已配置 API Key；若没有，明确告诉用户需要手动填写。
8. 遇到的错误、已尝试的修复、日志中的关键行。

如果卡在 API Key、显示器、代理或权限问题，直接说明阻塞点，不要反复重装或改动代码。
