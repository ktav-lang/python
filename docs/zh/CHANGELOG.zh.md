# Changelog — `ktav` (Python bindings)

**Languages:** [English](../../CHANGELOG.md) · [Русский](../ru/CHANGELOG.ru.md) · **简体中文**

本文档记录 `ktav` Python 包的所有重要变更。格式基于
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/);本包遵循
[Semantic Versioning](https://semver.org/),并采用 pre-1.0 约定:
MINOR 版本升级视为破坏性。

格式规范本身的历史见
[`ktav-lang/spec`](https://github.com/ktav-lang/spec)。底层
Rust 实现见 [`ktav-lang/rust`](https://github.com/ktav-lang/rust)。

## Unreleased

与 Ktav 规范 0.8.0 和 Rust core 0.8.0 同步。

### Added

- 带引号的键(spec 0.7.0 § 5.3.3)、`\uXXXX` 转义(§ 3.7.1)以及 0.7.0 的
  representable-Value writer 规则(§ 5.9.0)均已通过底层 Rust 核心获得。
- conformance 运行器现在会执行规范中的 `unrepresentable/` 与
  `parseable-unrepresentable/` fixture 类别(writer 必须拒绝)。
- `ktav.format()` —— 保留注释的「文本 → 文本」格式化器,底层是
  Rust 核心的 `format_str`(ktav 0.7.1,issue rust#13)。它把结构规范化
  为规范形式,逐字保留每一条注释,将连续空行折叠为一行,并且是不动点。
- 本绑定抛出的每个异常现在都以属性形式携带结构化错误信封
  (ktav issue rust#12):`error`、`reason`、`line`、`line_text`、
  `span`、`path`、`body`、`canonical`、`spec_section`。其中 `path` 是
  精确解码后的键段列表,绝不是拼接字符串;`str(exc)` 仍然保持人类可读。
- `exc.message` —— 信封自身的第十个字段(ktav 0.8.0),逐字取自核心。
  `str(exc) == exc.message` 由构造保证;本绑定的 `str(exc)` 一直使用
  核心自身的渲染,因此该属性在此处是多余的,但它让信封在 Python 中
  与其他语言保持同样的十字段结构。
- `ktav.canonical_from_source()` —— 从源文本直接得到规范文本,中间不
  构建 Python 值。与 JavaScript 绑定不同,这在这里不会带来额外的数值
  精度收益(Python 本身就区分 `int` 与 `float`),但它像
  `emit_canonical` 一样会丢弃注释和空行 —— 这一点与 `format` 不同。
- conformance 运行器强制执行规范 § 8.5 的精确语料库清单,并在整个
  valid 语料库上运行 `format`。

### Changed

- Rust 依赖改为 `ktav = "0.8"`——信封中携带 `message` 字段的第一个
  已发布核心(0.7.2 从未发布);`rust-version` 提升至
  `1.71`(ktav 0.7 的 MSRV)。
- spec 子模块固定到已发布的 Ktav `v0.8.0` 标签(新增 § 5.2:带有多余
  前导零的十进制数解析为 String,而非 Integer);规范元数据与
  `ktav.__spec_version__` 现在报告 `0.8.0`。
- 包版本移至 **0.8.0**,与核心和规范同步。
- 写入器的拒绝改传上游分类:NaN/±Infinity 报告原因 `NonFiniteFloat`,
  标量根报告 `ScalarRoot`,因此这两种情况下的 `str(exc)` 发生了变化
  (破坏性,但属预期——信封此前从未发布过)。
- 在 `ktav/_core.pyi` 中补上缺失的 `canonical_from_source` 存根——
  编译出的扩展不携带 Python 层面的注解,缺少它时 mypy 会把(本已可用
  的)函数视为 `Any`。

## [0.6.4] — 2026-08-23

与 Ktav 规范和 Rust core 0.6.4 同步。

### Added

- 新增 `ktav.loads_strict()`,用于严格检查 canonical scalar。writer
  生成的科学计数法浮点形式会被接受。

### Changed

- 包版本和规范 metadata 更新为 `0.6.4`。
- Rust 依赖采用 `ktav = "0.6"`,选择 0.6 minor 线中最新的兼容 patch。
- spec 子模块固定到已发布的 Ktav 0.6.4 提交。

## [0.6.1] — 2026-06-05

- 文档:所有 README 示例改写为 spec 0.6 语法(裸数字替代已移除的
  `:i`/`:f` 标记;`##` 注释替代 `#`)。

## [0.6.0] — 2026-06-01

同步至 Ktav 0.6.0——键现在支持转义。

### Added

- 键处理完整的 §3.7 转义集合,并新增两个转义:
  - `\.` → `.`(字面量点——**不**会切分 dotted-path)
  - `\:` → `:`(字面量冒号——**不**作为键/值分隔符)
- 示例:`a\.b: v` → `{"a.b": "v"}`、`a\:b: v` → `{"a:b": "v"}`、
  `x.y\.z: v` → `{"x": {"y.z": "v"}}`。

### Breaking

- 键中的字面量反斜杠现在需要写成 `\`(此前键中的 `` 是普通字节)。
  实际中很少出现;按 pre-1.0 SemVer 为 MINOR bump。

### Changed

- 跟踪 ktav-rust 0.6.0 / Ktav 规范 0.6.0。绑定源码未改动——escape
  语义的变化完全在 Rust 内核中,PyO3 边界对其透明。

---

## [0.5.0] — 2026-05-28

实现 Ktav 规范 0.5.0 的破坏性发布。

### Breaking

- **移除类型标记 `:i` 与 `:f`。** 数字、布尔值和 `null` 由标量的词法
  形式推断得出(spec §§ 3.6, 5.2)。`port: 8080` 现在生成 `int(8080)`;
  欲保留 String,请使用 `port:: 8080`。
- **注释使用 `##`**(仅限行首)。单个 `#` 字节即内容——
  `color: #FF0000` 是合法的字符串值。
- **Inline 复合结构** `{k: v, …}` / `[i, …]` 现在合法(spec § 5.8)。
  解析器不再发出 `InlineNonEmptyCompound` 错误。

### Added

- **`ktav.emit_canonical(obj)`**——发出规范化后(spec § 5.9)的字节
  确定性规范形式的 Python 值。
- **数字字面量语法**——hex(`0x`)、octal(`0o`)、binary(`0b`)、十进制
  以及下划线分隔符;i64 溢出回退为 String。
- **八个转义序列**用于 inline 标量(spec § 3.7):`\`、`\,`、`\}`、
  `\]`、`\{`、`\[`、`\n`、`\r`。

### Changed

- 许可证:`MIT` → `MIT OR Apache-2.0`。新增 `LICENSE-APACHE`;
  `LICENSE` 更名为 `LICENSE-MIT`。
- spec 子模块固定到 `v0.5.0`。
- 采用 `ktav 0.5.0`。

---

## [0.3.1] — 2026-05-10

向后兼容的功能发布:支持 top-level Array,并新增
`dumps_force_strings` 入口。

### Added

- **支持 top-level Array**(spec 0.1.1,§ 5.0.1)——解析器现在能够识别
  首个内容行为数组元素形状(裸标量、`:: text`、`:i 42`、`:f 3.14`、
  单独的 `{` / `[`,或 multi-line 开括号 `(` / `((`)的文档,并将其作为
  根级 Array。`ktav.loads(":i 1\n:i 2")` 返回 `[1, 2]`。Object 文档
  不受影响。序列化器接受 top-level `list` / `tuple`,并按每行一个、
  不带外层 `[...]` 的方式写出元素。
- **`ktav.dumps_force_strings(obj)`**——将每个叶标量渲染为 String
  (类型化整数、类型化浮点、布尔值和 `None` 会被压平为文本形式,并经
  原始 `::` 标记写出,使输出能够 round-trip 回相同的字符串标量)。
  Compound 保持结构不变;只有叶被强制转换。这是与 `dumps` /
  `loads` 并列的、符合 Python 习惯的 snake_case 命名。

### Changed

- **采用 `ktav 0.3.1`**——新增 format 层面的 top-level Array 支持,以及
  新 Python 入口所委托的 `to_string_force_strings` API。参见
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#031--2026-05-10)。
- `ktav.dumps(list_or_tuple)` 不再抛出异常——现在按 spec § 5.0.1
  渲染 top-level Array。
- `__spec_version__` 提升至 `0.1.1`。

### Spec

- spec 子模块同步至 `7256816`(Ktav 0.1.1 —— top-level Array 的
  fixtures 位于 `versions/0.1/tests/valid/top_level_array/` 和
  `versions/0.1/tests/invalid/top_level/`)。


## [0.3.0] — 2026-05-08

### Changed (breaking)

- **采用 `ktav 0.3.0`**——上游 Rust crate 决定拒绝 paren 包裹的字符串。
  像 `a: (hello)` 与 `a: ((wrapped))` 这样的 inline paren 包裹标量现在
  属于解码错误。PyO3 绑定透明地继承这一行为。参见
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#030--2026-05-08)。

### Spec

- spec 子模块同步至 `46d94a7`(新增 invalid fixtures
  `inline_paren_string_double` 与 `inline_paren_string_single`,
  并收紧 `partial_parens` valid fixture)。


## [0.2.0] — 2026-05-07

### Changed (breaking)

- **采用 `ktav 0.2.0`**——多行字符串现在默认以缩进的 stripped
  `( ... )` 形式序列化。`:f 42` 现在接受整数字面量(解析为
  `42.0`)。参见
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#020--2026-05-07)。

  将序列化输出与内置 `((...))` 字面量进行逐字节比较的代码需要更新。
  Round-trip 不变。

### Spec

- spec 子模块已同步(typed_float_integer_body fixture;oracle 42.0)。


## [0.1.2] — 2026-05-03

### Changed

- **采用 `ktav 0.1.5`**——上游 Rust crate 引入了结构化错误 API
  (`Error::Structured(ErrorKind)`,带字节偏移 span)、对错误枚举追溯
  应用的 `#[non_exhaustive]`,以及公开的事件驱动解析器 `ktav::thin`。
  PyO3 绑定对用户可见的行为没有变化:`KtavDecodeError` /
  `KtavEncodeError` 仍携带相同的人类可读消息(七个标准类别的 Display
  字符串与 ktav 0.1.4 完全字节相同)。将 `ktav::ErrorKind` 映射到
  结构化的 Python 异常层级(`MissingSeparatorSpace`、`DuplicateKey`
  等)是单独的后续工作,记录在 workspace 的
  [`STRUCTURED_ERRORS.md`](https://github.com/ktav-lang/.github/blob/main/STRUCTURED_ERRORS.md)。

PyPI: `ktav==0.1.2`。

## [0.1.1] — 2026-04-26

### Changed

- **升级到 `ktav 0.1.4`**——上游 Rust crate 中 PyO3 绑定所使用的
  untyped `parse() → Value` 路径,在小文档上快约 30%,在大文档上快约
  13%,仅来自 `Frame::Object` 初始容量的一行调整(4 → 8)。每次
  `ktav.loads` 调用都会透明地受益。

PyPI: `ktav==0.1.1`。

## [0.1.0] — 2026-04-22

首次发布。通过 PyO3 绑定在参考 Rust 实现之上实现
[Ktav spec 0.1.0](https://github.com/ktav-lang/spec/blob/main/versions/0.1/spec.md)。

### Added

- `ktav.loads(s)`——将 Ktav 字符串(或 UTF-8 `bytes`)解析为原生
  Python 值。
- `ktav.dumps(obj)`——将原生 Python 值序列化为 Ktav 文本。
- `ktav.load(fp)` / `ktav.dump(obj, fp)`——类文件对象包装,同时适用于
  文本模式和二进制模式的文件。
- 异常层级:`KtavError`(基类)、`KtavDecodeError`、`KtavEncodeError`。
- 类型映射秉承 Ktav「不耍小聪明」的原则:
  - 裸标量 → `str`;
  - `:i` 标记 → `int`(任意精度可 round-trip);
  - `:f` 标记 → `float`(输出时小数点始终存在);
  - 关键字 `null` / `true` / `false` → `None` / `bool`;
  - `[ ... ]` → `list`;
  - `{ ... }` → `dict`(保留插入顺序)。
- 序列化器拒绝 `NaN` / `±Infinity`——Ktav 0.1.0 不表示它们。
- 附带 `.pyi` 类型存根与 `py.typed` 标记(PEP 561)。
- `ktav.__version__`——包版本。
- `ktav.__spec_version__`——本绑定实现的 Ktav 格式版本。

### Supported platforms

预构建 wheel:

- **Linux**(manylinux + musllinux)——`x86_64`、`aarch64`
- **macOS**——`x86_64`、`arm64`
- **Windows**——`x64`、`arm64`

Wheel 使用稳定 ABI(`abi3-py39`);每种平台只需一个 wheel 即可服务所有
受支持的 CPython 版本。

### MSRV

Rust **1.70** 或更新版本——与底层 `ktav` crate 一致。
