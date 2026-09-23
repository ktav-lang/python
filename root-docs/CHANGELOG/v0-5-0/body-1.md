>>>>> lang=en
---

## [0.5.0] — 2026-05-28

Breaking release implementing Ktav specification 0.5.0.

### Breaking

- **Typed markers `:i` and `:f` removed.** Numbers, booleans, and `null`
  are inferred from the scalar's lexical form (spec §§ 3.6, 5.2).
  `port: 8080` now yields `int(8080)`; use `port:: 8080` to keep a String.
- **Comments use `##`** (line-start only). A single `#` byte is content —
  `color: #FF0000` is a valid string value.
- **Inline compounds** `{k: v, …}` / `[i, …]` are now valid (spec § 5.8).
  The `InlineNonEmptyCompound` error is no longer emitted by the parser.

### Added

- **`ktav.emit_canonical(obj)`** — emit the normalised (spec § 5.9)
  byte-deterministic canonical form of a Python value.
- **Number literal grammar** — hex (`0x`), octal (`0o`), binary (`0b`),
  decimal, and underscore separators; i64 overflow falls back to String.
- **Eight escape sequences** in inline scalars (spec § 3.7):
  `\\`, `\,`, `\}`, `\]`, `\{`, `\[`, `\n`, `\r`.

### Changed

- License: `MIT` → `MIT OR Apache-2.0`. Added `LICENSE-APACHE`;
  renamed `LICENSE` → `LICENSE-MIT`.
- Spec submodule pinned to `v0.5.0`.
- Picked up `ktav 0.5.0`.

>>>>> lang=ru
---

## [0.5.0] — 2026-05-28

Ломающий релиз, реализующий спецификацию Ktav 0.5.0.

### Breaking

- **Типизированные маркеры `:i` и `:f` удалены.** Числа, булевы
  значения и `null` выводятся из лексической формы скаляра
  (spec §§ 3.6, 5.2). `port: 8080` теперь даёт `int(8080)`; используйте
  `port:: 8080`, чтобы сохранить String.
- **Комментарии используют `##`** (только в начале строки). Один байт
  `#` — это содержимое — `color: #FF0000` является корректным строковым
  значением.
- **Inline-compounds** `{k: v, …}` / `[i, …]` теперь корректны
  (spec § 5.8). Парсер больше не выдаёт ошибку
  `InlineNonEmptyCompound`.

### Added

- **`ktav.emit_canonical(obj)`** — выдаёт нормализованную
  (spec § 5.9) байт-детерминированную каноническую форму
  Python-значения.
- **Грамматика числовых литералов** — hex (`0x`), octal (`0o`),
  binary (`0b`), decimal и разделители `_`; переполнение i64
  откатывается на String.
- **Восемь escape-последовательностей** в inline-скалярах
  (spec § 3.7): `\`, `\,`, `\}`, `\]`, `\{`, `\[`, `\n`, `\r`.

### Changed

- Лицензия: `MIT` → `MIT OR Apache-2.0`. Добавлен `LICENSE-APACHE`;
  `LICENSE` переименован в `LICENSE-MIT`.
- Submodule спецификации закреплён на `v0.5.0`.
- Подхвачен `ktav 0.5.0`.

>>>>> lang=zh
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

