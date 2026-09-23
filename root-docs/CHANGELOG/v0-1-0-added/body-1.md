>>>>> lang=en
## [0.1.0] — 2026-04-22

Initial release. Implements [Ktav spec 0.1.0](https://github.com/ktav-lang/spec/blob/main/versions/0.1/spec.md)
via PyO3 bindings over the reference Rust implementation.

### Added

- `ktav.loads(s)` — parse a Ktav string (or UTF-8 `bytes`) into native
  Python values.
- `ktav.dumps(obj)` — serialise a native Python value into Ktav text.
- `ktav.load(fp)` / `ktav.dump(obj, fp)` — file-like wrappers that work
  for both text-mode and binary-mode files.
- Exception hierarchy: `KtavError` (base), `KtavDecodeError`,
  `KtavEncodeError`.
- Type mapping honouring Ktav's "no magic types" principle:
  - bare scalars → `str`;
  - `:i` marker → `int` (arbitrary precision round-trips);
  - `:f` marker → `float` (decimal point always present on output);
  - keywords `null` / `true` / `false` → `None` / `bool`;
  - `[ ... ]` → `list`;
  - `{ ... }` → `dict` (insertion order preserved).
- `NaN` / `±Infinity` rejected by the serialiser — Ktav 0.1.0 does not
  represent them.
- Bundled `.pyi` type stubs and `py.typed` marker (PEP 561).
- `ktav.__version__` — package version.
- `ktav.__spec_version__` — Ktav format version these bindings
  implement.

>>>>> lang=ru
## [0.1.0] — 2026-04-22

Первый релиз. Реализует [Ktav spec 0.1.0](https://github.com/ktav-lang/spec/blob/main/versions/0.1/spec.md)
через PyO3-биндинги над reference Rust реализацией.

### Added

- `ktav.loads(s)` — разбирает строку Ktav (или UTF-8 `bytes`) в
  нативные Python-значения.
- `ktav.dumps(obj)` — сериализует нативное Python-значение в текст
  Ktav.
- `ktav.load(fp)` / `ktav.dump(obj, fp)` — файл-подобные обёртки,
  работающие и с текстовыми, и с бинарными файлами.
- Иерархия исключений: `KtavError` (база), `KtavDecodeError`,
  `KtavEncodeError`.
- Соответствие типов в духе принципа Ktav «никакой магии»:
  - скаляры без маркера → `str`;
  - маркер `:i` → `int` (round-trip с произвольной точностью);
  - маркер `:f` → `float` (на выходе точка всегда присутствует);
  - ключевые слова `null` / `true` / `false` → `None` / `bool`;
  - `[ ... ]` → `list`;
  - `{ ... }` → `dict` (порядок вставки сохраняется).
- `NaN` / `±Infinity` отвергаются сериализатором — Ktav 0.1.0 не
  представляет их.
- В комплекте `.pyi` type stubs и маркер `py.typed` (PEP 561).
- `ktav.__version__` — версия пакета.
- `ktav.__spec_version__` — версия формата Ktav, которую реализует
  этот биндинг.

>>>>> lang=zh
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

