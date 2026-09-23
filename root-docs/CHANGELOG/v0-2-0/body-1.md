>>>>> lang=en

## [0.2.0] — 2026-05-07

### Changed (breaking)

- **Picked up `ktav 0.2.0`** — multi-line strings now serialize in the
  indented stripped `( ... )` form by default. `:f 42` accepts integer
  literals (parsed as `42.0`). See the
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#020--2026-05-07).

  Code comparing serialized output byte-for-byte to a baked-in
  `((...))` literal must be updated. Round-trip is unchanged.

### Spec

- spec submodule synced (typed_float_integer_body fixture; oracle 42.0).

>>>>> lang=ru

## [0.2.0] — 2026-05-07

### Changed (breaking)

- **Подхвачен `ktav 0.2.0`** — многострочные строки теперь по
  умолчанию сериализуются в indented stripped форме `( ... )`. `:f 42`
  принимает целочисленные литералы (парсится как `42.0`). См.
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#020--2026-05-07).

  Код, который побайтово сравнивает сериализованный вывод с
  зашитым литералом `((...))`, нужно обновить. Round-trip не
  меняется.

### Spec

- spec submodule синхронизирован (typed_float_integer_body fixture;
  oracle 42.0).

>>>>> lang=zh

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

