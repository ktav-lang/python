>>>>> lang=en
## [0.1.1] — 2026-04-26

### Changed

- **Picked up `ktav 0.1.4`** — the upstream Rust crate's untyped
  `parse() → Value` path (which the PyO3 binding uses) is now ~30%
  faster on small documents and ~13% faster on large ones, just from
  a one-line `Frame::Object` capacity tweak (4 → 8). Every
  `ktav.loads` call benefits transparently.

PyPI: `ktav==0.1.1`.

>>>>> lang=ru
## [0.1.1] — 2026-04-26

### Changed

- **Подхвачен `ktav 0.1.4`** — untyped путь `parse() → Value` в
  upstream Rust crate (тот, что использует PyO3-биндинг) теперь
  примерно на 30% быстрее на маленьких документах и на ~13% быстрее на
  больших — благодаря однострочной правке initial capacity для
  `Frame::Object` (4 → 8). Каждый вызов `ktav.loads` прозрачно
  выигрывает.

PyPI: `ktav==0.1.1`.

>>>>> lang=zh
## [0.1.1] — 2026-04-26

### Changed

- **升级到 `ktav 0.1.4`**——上游 Rust crate 中 PyO3 绑定所使用的
  untyped `parse() → Value` 路径,在小文档上快约 30%,在大文档上快约
  13%,仅来自 `Frame::Object` 初始容量的一行调整(4 → 8)。每次
  `ktav.loads` 调用都会透明地受益。

PyPI: `ktav==0.1.1`。

