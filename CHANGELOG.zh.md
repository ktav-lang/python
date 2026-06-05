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

## [0.6.1] — 2026-06-05

- 文档：将所有 README 示例改写为 spec 0.6 语法（裸数字替代已移除的 `:i`/`:f` 标记；`##` 注释替代 `#`）。

## [0.6.0] —— 2026-06-01

同步至 Ktav 0.6.0 —— 键现在支持转义。

### 新增

- 键处理完整的 §3.7 转义集合,并新增两个转义:
  - `\.` → `.`(字面量点 —— **不**会切分 dotted-path)
  - `\:` → `:`(字面量冒号 —— **不**作为键/值分隔符)
- 示例: `a\.b: v` → `{"a.b": "v"}`,`a\:b: v` → `{"a:b": "v"}`,
  `x.y\.z: v` → `{"x": {"y.z": "v"}}`。

### 破坏性变更

- 键中的字面量反斜杠现在需要写作 `\\`(此前键中的 `\` 是普通字节)。
  实际中很少出现;按 pre-1.0 SemVer 为 MINOR bump。

### 变更

- 跟踪 ktav-rust 0.6.0 / Ktav 规范 0.6.0。绑定源码未改动 —— escape
  语义的变化完全在 Rust 内核中实现,PyO3 边界对其透明。

---

## [0.1.2] —— 2026-05-03

### 变更

- **已采用 `ktav 0.1.5`** —— 上游 Rust crate 引入了结构化错误 API
  (`Error::Structured(ErrorKind)` 带字节偏移 span)、对错误枚举追溯
  应用了 `#[non_exhaustive]`,以及公开的事件式解析器 `ktav::thin`。
  PyO3 binding 对用户可见的行为没有变化:`KtavDecodeError` /
  `KtavEncodeError` 仍然携带相同的人类可读消息(七个标准类别的
  Display 字符串与 ktav 0.1.4 完全字节相同)。将 `ktav::ErrorKind`
  映射到结构化的 Python 异常层级(`MissingSeparatorSpace`、
  `DuplicateKey` 等)是单独的后续工作,记录在
  [`STRUCTURED_ERRORS.md`](https://github.com/ktav-lang/.github/blob/main/STRUCTURED_ERRORS.md)。

PyPI:`ktav==0.1.2`。

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
