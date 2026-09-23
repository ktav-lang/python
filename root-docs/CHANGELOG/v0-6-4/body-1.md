>>>>> lang=en
## [0.6.4] — 2026-08-23

Synchronized with Ktav spec and Rust core 0.6.4.

### Added

- Added `ktav.loads_strict()` for strict canonical-scalar validation.
  Canonical scientific float forms emitted by the writer are accepted.

### Changed

- Package version and spec metadata are now `0.6.4`.
- The Rust dependency uses `ktav = "0.6"`, selecting the latest compatible
  patch release in the 0.6 minor line.
- Spec submodule is pinned to the published Ktav 0.6.4 commit.

>>>>> lang=ru
## [0.6.4] — 2026-08-23

Синхронизация со спецификацией Ktav и Rust core 0.6.4.

### Added

- Добавлен `ktav.loads_strict()` для строгой проверки канонических
  скаляров. Научные формы чисел, которые выдаёт writer, принимаются.

### Changed

- Версия пакета и metadata спецификации теперь `0.6.4`.
- Зависимость Rust использует `ktav = "0.6"` и выбирает последний
  совместимый patch-релиз в ветке minor 0.6.
- Submodule спецификации закреплён на опубликованном коммите Ktav 0.6.4.

>>>>> lang=zh
## [0.6.4] — 2026-08-23

与 Ktav 规范和 Rust core 0.6.4 同步。

### Added

- 新增 `ktav.loads_strict()`,用于严格检查 canonical scalar。writer
  生成的科学计数法浮点形式会被接受。

### Changed

- 包版本和规范 metadata 更新为 `0.6.4`。
- Rust 依赖采用 `ktav = "0.6"`,选择 0.6 minor 线中最新的兼容 patch。
- spec 子模块固定到已发布的 Ktav 0.6.4 提交。

