#requires -Version 5.1
<#
.SYNOPSIS
    每小时整点后 10 秒自动点击 PA Agent 的「获取数据」→「提交分析」。

.DESCRIPTION
    通过 Windows UI Automation 操作 PA Agent 窗口，无需鼠标键盘。
    计划任务在整点（HH:00:00）触发，脚本内部再等 StartDelaySeconds 秒，
    等效于「每小时 HH:00:10」执行。
    默认行为：执行一次（供计划任务调用）。
        -Install    注册计划任务（每小时整点触发）
        -Uninstall  删除计划任务
        -Status     查看计划任务状态
    日志：<项目根>\logs\auto_task.log
#>
param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Status,
    [int]$WaitSeconds = 12,
    [int]$StartDelaySeconds = 10
)

$ErrorActionPreference = 'Stop'
$TaskName  = 'PA_Agent_Hourly_Fetch_Analyze'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogFile  = Join-Path $ProjectRoot 'logs\auto_task.log'
$TitlePattern = '^PA Agent . Trading Terminal'

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

function Write-Log([string]$Message) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $dir = Split-Path -Parent $LogFile
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Add-Content -Path $LogFile -Value "$ts  $Message" -Encoding UTF8
}

function Get-AppWindow {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $all = $root.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($w in $all) {
        if ($w.Current.Name -match $TitlePattern) { return $w }
    }
    return $null
}

function Find-Button($Window, [string]$Name) {
    $cond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::NameProperty, $Name)
    return $Window.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
}

function Invoke-Button($Window, [string]$Name, [int]$TimeoutSec = 25) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $btn = Find-Button -Window $Window -Name $Name
        if ($btn -and $btn.Current.IsEnabled) {
            $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Get-BlockingDialog {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $all = $root.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($w in $all) {
        if ($w.Current.Name -match 'API Key|TradingView') { return $w.Current.Name }
    }
    return $null
}

# ---------- 计划任务管理 ----------
if ($Install) {
    $action = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`""
    $out = schtasks /Create /TN $TaskName /TR $action /SC HOURLY /MO 1 /ST 00:00 /F 2>&1
    Write-Log "注册计划任务：$out"
    Write-Output $out
    exit 0
}

if ($Uninstall) {
    $out = schtasks /Delete /TN $TaskName /F 2>&1
    Write-Log "删除计划任务：$out"
    Write-Output $out
    exit 0
}

if ($Status) {
    schtasks /Query /TN $TaskName /FO LIST 2>&1
    exit 0
}

# ---------- 单次执行 ----------
Write-Log '--- 触发：开始取数 + 提交分析 ---'

if ($StartDelaySeconds -gt 0) {
    Write-Log "等待 $StartDelaySeconds 秒，对齐到整点后 $StartDelaySeconds 秒"
    Start-Sleep -Seconds $StartDelaySeconds
}

$dialog = Get-BlockingDialog
if ($dialog) {
    Write-Log "存在阻塞对话框「$dialog」，本次跳过"
    exit 0
}

$win = Get-AppWindow
if (-not $win) {
    Write-Log '未找到 PA Agent 主窗口（程序未启动？），本次跳过'
    exit 0
}
Write-Log "已找到窗口：PID $($win.Current.ProcessId)"

if (-not (Invoke-Button -Window $win -Name '获取数据')) {
    Write-Log '「获取数据」按钮不可用或点击失败，本次结束'
    exit 0
}
Write-Log '已点击「获取数据」'

Start-Sleep -Seconds $WaitSeconds
Write-Log "等待 $WaitSeconds 秒后提交分析"

$submitted = $false
if (Invoke-Button -Window $win -Name '提交分析' -TimeoutSec 8) {
    Write-Log '已点击「提交分析」'
    $submitted = $true
}
if (-not $submitted) {
    if (Invoke-Button -Window $win -Name '增量分析' -TimeoutSec 30) {
        Write-Log '已点击「增量分析」（已有分析结果时界面用这个按钮）'
        $submitted = $true
    }
}
if (-not $submitted) {
    Write-Log '「提交分析」和「增量分析」都不可用（未配置 API Key / 数据未就绪），本次结束'
    exit 0
}
Write-Log '本次任务完成'