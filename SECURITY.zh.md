# 安全策略

**语言:** [English](SECURITY.md) · [Русский](SECURITY.ru.md) · **简体中文**

## 支持的版本

本包仍处于 pre-1.0 阶段，仅维护**最新发布的次版本**。安全修复会进入
`main`，并在数日内以 PATCH 发布。

| 版本    | 支持                   |
|---------|------------------------|
| 0.1.x   | ✅                     |
| 更早    | ❌ —— 请先升级         |

## 上报漏洞

**请不要为安全问题开公开 issue。**

请发邮件至 **phpcraftdream@gmail.com**，并提供:

- 对漏洞的简短描述。
- 复现步骤或代码片段（触发该行为的 Ktav 输入、受影响的 API ——
  `loads` / `dumps` / 文件变体，预期结果 vs 实际结果）。
- 观察到问题时所用的版本（通常 `pip show ktav` 的输出就够了），
  以及 OS / Python 版本 —— 以便确认当时使用的是哪个 abi3 wheel。
- 你偏好的披露时间线（如有）。

你应在 **72 小时**内收到确认。对于高影响问题，已发布的修复通常在
**一周**内跟进；如果修复需要与 Rust crate 或格式规范协同推进，则
可能更久。

## 范围

以下问题会按本包的安全问题处理:

- 编译后的 `_core` 扩展模块中的越界读写或 panic（PyO3 会捕获 Rust
  panic 并重新抛为 `pyo3_runtime.PanicException`，解释器得以存活 ——
  但可信输入下的 panic 仍然是值得上报的 bug）。
- 解析构造输入时出现失控的内存或 CPU 消耗。
- 任何允许构造的 Ktav 输入逃逸出预期值域的行为（任意对象构造、
  通过扩展的内存泄露等）。
- 绕过 PyO3 panic 桥的 segfault —— 这类问题指向真正的 `unsafe`
  soundness 问题，优先处理。

以下**不**算本包的安全问题 —— 请走普通 issue:

- 没有崩溃 / 挂起特征的性能回归。
- 不可利用的异常类型失配（例如应当是 `TypeError` 的地方报了 `ValueError`）。
- Ktav 格式本身的问题 —— 这类问题属于
  [`ktav-lang/spec`](https://github.com/ktav-lang/spec)。
