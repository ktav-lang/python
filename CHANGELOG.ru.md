# Changelog — `ktav` (Python-биндинги)

**Языки:** [English](CHANGELOG.md) · **Русский** · [简体中文](CHANGELOG.zh.md)

Все значимые изменения Python-пакета `ktav` документируются здесь.
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/);
пакет следует [Semantic Versioning](https://semver.org/) с pre-1.0
соглашением, что MINOR bump — ломающий.

История самой спецификации формата — в
[`ktav-lang/spec`](https://github.com/ktav-lang/spec). Нижележащая
Rust-реализация — в
[`ktav-lang/rust`](https://github.com/ktav-lang/rust).

## [0.1.1] — 2026-04-26

### Изменено

- **Подхватили `ktav 0.1.4`** — untyped путь `parse() → Value` в
  upstream Rust crate (тот, что использует PyO3 binding) теперь
  ~30% быстрее на маленьких документах и ~13% на больших, благодаря
  однострочной правке initial capacity для `Frame::Object` (4 → 8).
  Каждый `ktav.loads` получит ускорение прозрачно.

PyPI: `ktav==0.1.1`.

## [0.1.0] — 2026-04-22

Первый релиз. Реализует [спеку Ktav 0.1.0](https://github.com/ktav-lang/spec/blob/main/versions/0.1/spec.md)
через PyO3-биндинги над reference-Rust-реализацией.

### Добавлено

- `ktav.loads(s)` — разбирает строку Ktav (или UTF-8 `bytes`) в нативные
  Python-значения.
- `ktav.dumps(obj)` — сериализует нативное Python-значение в текст Ktav.
- `ktav.load(fp)` / `ktav.dump(obj, fp)` — обёртки под файл-подобные
  объекты, работают и в текстовом, и в бинарном режиме.
- Иерархия исключений: `KtavError` (база), `KtavDecodeError`,
  `KtavEncodeError`.
- Соответствие типов в духе «никакой магии» Ktav:
  - скаляр без маркера → `str`;
  - маркер `:i` → `int` (round-trip для bigint произвольной точности);
  - маркер `:f` → `float` (на выходе точка всегда присутствует);
  - ключевые слова `null` / `true` / `false` → `None` / `bool`;
  - `[ ... ]` → `list`;
  - `{ ... }` → `dict` (порядок вставки сохраняется).
- `NaN` / `±Infinity` отвергаются сериализатором — Ktav 0.1.0 их не
  представляет.
- В комплекте `.pyi` type stubs и `py.typed`-маркер (PEP 561).
- `ktav.__version__` — версия пакета.
- `ktav.__spec_version__` — версия формата Ktav, которую реализует
  биндинг.

### Поддерживаемые платформы

Prebuilt wheels:

- **Linux** (manylinux + musllinux) — `x86_64`, `aarch64`
- **macOS** — `x86_64`, `arm64`
- **Windows** — `x64`, `arm64`

Wheels используют стабильный ABI (`abi3-py39`); одного wheel на
платформу достаточно для всех поддерживаемых релизов CPython.

### MSRV

Rust **1.70** или новее — совпадает с нижележащим крейтом `ktav`.
