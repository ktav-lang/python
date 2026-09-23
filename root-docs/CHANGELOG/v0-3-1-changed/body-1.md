>>>>> lang=en
### Changed

- **Picked up `ktav 0.3.1`** — adds the format-level top-level
  Array support and the `to_string_force_strings` API the new
  Python entry point delegates to. See the
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#031--2026-05-10).
- `ktav.dumps(list_or_tuple)` no longer raises — it now renders a
  top-level Array per spec § 5.0.1.
- `__spec_version__` bumped to `0.1.1`.

### Spec

- spec submodule synced to `7256816` (Ktav 0.1.1 — top-level Array
  fixtures under `versions/0.1/tests/valid/top_level_array/` and
  `versions/0.1/tests/invalid/top_level/`).

>>>>> lang=ru
### Changed

- **Подхвачен `ktav 0.3.1`** — добавляет format-level поддержку
  top-level Array и API `to_string_force_strings`, на который
  делегирует новая Python-точка входа. См.
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#031--2026-05-10).
- `ktav.dumps(list_or_tuple)` больше не бросает исключение — теперь
  рендерит top-level Array по spec § 5.0.1.
- `__spec_version__` поднят до `0.1.1`.

### Spec

- spec submodule синхронизирован на `7256816` (Ktav 0.1.1 — top-level
  Array fixtures в `versions/0.1/tests/valid/top_level_array/` и
  `versions/0.1/tests/invalid/top_level/`).

>>>>> lang=zh
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

