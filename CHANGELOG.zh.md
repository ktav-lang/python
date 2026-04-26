<!-- TODO: sync with CHANGELOG.md — this translation is a stub awaiting
     a Simplified Chinese review. Translate in-place and remove this
     comment once the content is ready. -->

# Changelog — `ktav` (Python 绑定)

**Languages:** [English](CHANGELOG.md) · [Русский](CHANGELOG.ru.md) · **简体中文**

本文档记录 `ktav` Python 包的所有重要变更。格式基于
[Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/);包遵循
[Semantic Versioning](https://semver.org/),采用 pre-1.0 约定:
MINOR 版本升级视为破坏性。

格式规范本身的历史见
[`ktav-lang/spec`](https://github.com/ktav-lang/spec)。底层 Rust
实现见 [`ktav-lang/rust`](https://github.com/ktav-lang/rust)。

## [0.1.1] —— 2026-04-26

### 变更

- **升级到 `ktav 0.1.4`** —— 上游 Rust crate 中 PyO3 绑定使用的
  untyped `parse() → Value` 路径,小文档加速约 30%、大文档加速
  约 13%,只是 `Frame::Object` 的初始容量微调(4 → 8)。每次
  `ktav.loads` 都会透明地受益。

PyPI:`ktav==0.1.1`。

## [0.1.0] — 2026-04-22

首次发布。通过 PyO3 绑定参考 Rust 实现,实现
[Ktav 规范 0.1.0](https://github.com/ktav-lang/spec/blob/main/versions/0.1/spec.md)。

### 新增

- `ktav.loads(s)` / `ktav.dumps(obj)` —— 字符串层面的解析与序列化。
- `ktav.load(fp)` / `ktav.dump(obj, fp)` —— 类文件对象包装。
- 异常层次: `KtavError` (基类), `KtavDecodeError`, `KtavEncodeError`。
- 类型映射秉承 Ktav "不耍小聪明" 原则。
- 附带 `.pyi` 类型存根与 `py.typed` 标记 (PEP 561)。

### 支持平台

- **Linux** (manylinux + musllinux) —— `x86_64`, `aarch64`
- **macOS** —— `x86_64`, `arm64`
- **Windows** —— `x64`, `arm64`

使用稳定 ABI (`abi3-py39`)。

### MSRV

Rust **1.70** 或更新版本。
