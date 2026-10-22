>>>>> lang=en
- The conformance runner enforces the exact corpus inventory from
  spec § 8.5 and exercises `format` across the whole valid corpus.
- A native-free install artifact: the universal pure wheel
  `ktav-0.8.1-py3-none-any.whl` (same distribution name and version,
  built from `packaging/pure/`), published on PyPI alongside the
  native platform wheels. It installs with no Rust toolchain, compiler
  or maturin and provides exactly the `ktav.pure` backend.

>>>>> lang=ru
- `ktav.pure` — полноценный чистый backend на Python: парсер и
  генератор, в обе стороны, без скомпилированного расширения, без
  Rust-бинарника, WASM и subprocess. Он реализует весь публичный набор
  операций (`loads`, `loads_strict`, `dumps`, `emit_canonical`,
  `dumps_force_strings`, `format`, `canonical_from_source`, `load`,
  `dump`) с тем же десятипольным конвертом ошибок и семантикой
  spec 0.8.1. CI прогоняет весь conformance-корпус через оба backend-а
  и проверяет побайтовую идентичность канонического вывода.
- Артефакт установки без нативного кода: универсальный pure wheel
  `ktav-0.8.1-py3-none-any.whl` (то же имя дистрибуции и версия,
  собирается из `packaging/pure/`), публикуемый на PyPI рядом с
  нативными платформенными wheel-ами. Он ставится без Rust toolchain,
  компилятора и maturin и предоставляет ровно backend `ktav.pure`.

>>>>> lang=zh
- `ktav.pure` —— 完整的纯 Python backend：解析器与生成器,双向可用,
  全程不加载编译扩展、Rust 二进制、WASM 或子进程。它实现完整的公开
  操作集(`loads`、`loads_strict`、`dumps`、`emit_canonical`、
  `dumps_force_strings`、`format`、`canonical_from_source`、`load`、
  `dump`),携带相同的十字段错误信封,遵循 spec 0.8.1 语义。CI 会
  通过两个 backend 运行整个 conformance 语料库,并断言规范输出的
  字节完全一致。
- 无需原生代码的安装工件：通用纯 wheel
  `ktav-0.8.1-py3-none-any.whl`（同一发行名与版本,由
  `packaging/pure/` 构建）,与各原生平台 wheel 一同发布在 PyPI 上。
  它的安装不需要 Rust 工具链、编译器或 maturin,并且只提供
  `ktav.pure` 这一个 backend。

