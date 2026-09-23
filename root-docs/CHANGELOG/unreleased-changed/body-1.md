>>>>> lang=en
### Changed

- The Rust dependency now uses `ktav = "0.8"` — the first published
  core to carry the envelope's `message` field (0.7.2 was never
  published); `rust-version` raised to `1.71` (ktav 0.7's MSRV).
- Spec submodule is pinned to the published Ktav `v0.8.0` tag (adds
  § 5.2: a decimal with a redundant leading zero parses as a String,
  not an Integer); the spec metadata and `ktav.__spec_version__` now
  report `0.8.0`.
- The package version moves to **0.8.0**, in step with the core and the
  specification.
- Writer rejections surface the upstream taxonomy: NaN/±Infinity
  reports reason `NonFiniteFloat` and a scalar root reports
  `ScalarRoot`, so `str(exc)` for those two cases changed (breaking,
  intended — the envelope has never shipped before).
- Added the missing `canonical_from_source` stub to
  `ktav/_core.pyi` — the compiled extension carries no Python-level
  annotations, so mypy treated the (already-working) function as `Any`
  without it.

>>>>> lang=ru
### Changed

- Зависимость Rust теперь использует `ktav = "0.8"` — первое
  опубликованное ядро, несущее поле `message` в конверте (0.7.2 так и
  не был опубликован); `rust-version` поднят до `1.71` (MSRV ktav 0.7).
- Submodule спецификации закреплён на опубликованном теге Ktav `v0.8.0`
  (добавлен § 5.2: десятичное число с избыточным ведущим нулём
  разбирается как String, а не Integer); metadata спецификации и
  `ktav.__spec_version__` теперь сообщают `0.8.0`.
- Версия пакета переходит на **0.8.0**, синхронно с ядром и
  спецификацией.
- Отказы writer'а передают таксономию ядра: NaN/±Infinity сообщает
  причину `NonFiniteFloat`, а скалярный корень — `ScalarRoot`, поэтому
  `str(exc)` для этих двух случаев изменился (breaking, осознанно —
  конверт раньше не поставлялся).
- В `ktav/_core.pyi` добавлена недостающая заглушка
  `canonical_from_source` — скомпилированное расширение не несёт
  Python-аннотаций, поэтому без неё mypy считал (уже работавшую)
  функцию `Any`.

>>>>> lang=zh
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

