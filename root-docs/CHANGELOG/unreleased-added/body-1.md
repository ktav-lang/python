>>>>> lang=en
### Added

- Quoted keys (spec 0.7.0 § 5.3.3), `\uXXXX` escapes (§ 3.7.1), and the
  0.7.0 representable-Value writer rules (§ 5.9.0) are picked up through
  the underlying Rust core.
- Conformance runner now executes the spec's `unrepresentable/` and
  `parseable-unrepresentable/` fixture categories (writer must refuse).
- `ktav.format()` — comment-preserving text→text formatter backed by
  the Rust core's `format_str` (ktav 0.7.1, issue rust#13). Normalises
  structure to canonical form, keeps every comment verbatim, collapses
  blank-line runs to one, and is a fixed point.
- Every exception raised by the binding now carries the structured
  error envelope (ktav issue rust#12) as attributes: `error`, `reason`,
  `line`, `line_text`, `span`, `path`, `body`, `canonical`,
  `spec_section` — `path` a list of exact decoded key segments, never
  a joined string; `str(exc)` stays human-readable.
- `exc.message` — the envelope's own tenth field (ktav 0.8.0), taken
  verbatim from the core. `str(exc) == exc.message` by construction;
  this binding has always used the core's own rendering for `str(exc)`,
  so the attribute is redundant here but keeps the same ten-field
  shape the envelope has in every other language.
- `ktav.canonical_from_source()` — canonical text from source text with
  no Python value built in between. Unlike the JavaScript bindings this
  buys no extra numeric fidelity here (Python already distinguishes
  `int` from `float`), but it does skip comments and blank lines like
  `emit_canonical`, unlike `format`.
- The conformance runner enforces the exact corpus inventory from
  spec § 8.5 and exercises `format` across the whole valid corpus.

>>>>> lang=ru
### Added

- Ключи в кавычках (spec 0.7.0 § 5.3.3), escape-последовательности
  `\uXXXX` (§ 3.7.1) и правила writer'а 0.7.0 для представимых Value
  (§ 5.9.0) подхватываются через нижележащее Rust-ядро.
- Conformance runner теперь выполняет категории fixtures из спецификации
  `unrepresentable/` и `parseable-unrepresentable/` (writer обязан
  отказаться).
- `ktav.format()` — форматтер «текст → текст» с сохранением
  комментариев, на базе `format_str` ядра Rust (ktav 0.7.1, issue
  rust#13). Приводит структуру к канонической форме, сохраняет каждый
  комментарий дословно, схлопывает серии пустых строк до одной и
  является фиксированной точкой.
- Каждое исключение, которое бросает биндинг, теперь несёт конверт
  структурированной ошибки (ktav issue rust#12) в виде атрибутов:
  `error`, `reason`, `line`, `line_text`, `span`, `path`, `body`,
  `canonical`, `spec_section` — `path` это список точных декодированных
  сегментов ключа, а не склеенная строка; `str(exc)` остаётся
  человекочитаемым.
- `exc.message` — собственное десятое поле конверта (ktav 0.8.0),
  взятое дословно от ядра. `str(exc) == exc.message` по построению;
  этот биндинг всегда использовал собственный рендеринг ядра для
  `str(exc)`, поэтому атрибут здесь избыточен, но сохраняет ту же
  десятипольную форму конверта, что и в остальных языках.
- `ktav.canonical_from_source()` — канонический текст из исходного
  текста, без построения промежуточного Python-значения. В отличие от
  биндингов для JavaScript, здесь это не даёт выигрыша в точности
  чисел (Python и так различает `int` и `float`), но, как и
  `emit_canonical`, отбрасывает комментарии и пустые строки — в
  отличие от `format`.
- Conformance runner проверяет точную инвентаризацию корпуса fixtures
  из spec § 8.5 и прогоняет `format` по всему валидному корпусу.

>>>>> lang=zh
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

