>>>>> lang=en

## [0.3.0] — 2026-05-08

### Changed (breaking)

- **Picked up `ktav 0.3.0`** — the upstream Rust crate's reject-paren-strings
  change. Inline paren-wrapped scalars like `a: (hello)` and `a: ((wrapped))`
  are now decode errors. The PyO3 binding inherits this behaviour
  transparently. See the
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#030--2026-05-08).

### Spec

- spec submodule synced to `46d94a7` (new invalid fixtures
  `inline_paren_string_double` and `inline_paren_string_single`,
  tightened `partial_parens` valid-fixture).

>>>>> lang=ru

## [0.3.0] — 2026-05-08

### Changed (breaking)

- **Подхвачен `ktav 0.3.0`** — изменение upstream Rust crate,
  отклоняющее paren-строки. Inline paren-обёрнутые скаляры вида
  `a: (hello)` и `a: ((wrapped))` теперь являются decode error'ами.
  PyO3-биндинг наследует это поведение прозрачно. См.
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#030--2026-05-08).

### Spec

- spec submodule синхронизирован на `46d94a7` (новые invalid fixtures
  `inline_paren_string_double` и `inline_paren_string_single`,
  ужесточён `partial_parens` valid-fixture).

>>>>> lang=zh

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

