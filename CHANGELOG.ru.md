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

## [0.6.0] — 2026-06-01

Синхронизация с Ktav 0.6.0 — ключи теперь поддерживают экранирование.

### Добавлено

- Ключи обрабатывают полный набор escape-последовательностей §3.7,
  включая два новых:
  - `\.` → `.` (литеральная точка — **не** делит dotted-path)
  - `\:` → `:` (литеральное двоеточие — **не** работает как разделитель
    ключ/значение)
- Примеры: `a\.b: v` → `{"a.b": "v"}`, `a\:b: v` → `{"a:b": "v"}`,
  `x.y\.z: v` → `{"x": {"y.z": "v"}}`.

### Ломающие изменения

- Литеральный backslash внутри ключа теперь требует `\\` (раньше `\` в
  ключе был обычным байтом). На практике встречается редко; по pre-1.0
  SemVer — MINOR bump.

### Изменено

- Отслеживает ktav-rust 0.6.0 / Ktav spec 0.6.0. Исходники биндинга не
  менялись — изменение escape-семантики целиком внутри Rust-ядра и
  прозрачно через границу PyO3.

---

## [0.3.1] — 2026-05-10

Обратносовместимый feature-релиз: top-level массивы и новая точка
входа `dumps_force_strings`.

### Добавлено

- **Поддержка top-level Array** (spec 0.1.1, § 5.0.1) — парсер
  теперь распознаёт документ, у которого первая значимая строка
  выглядит как item массива (голый скаляр, `:: text`, `:i 42`,
  `:f 3.14`, одиночный `{` / `[` или multi-line opener `(` / `((`),
  как корневой Array. `ktav.loads(":i 1\n:i 2")` возвращает
  `[1, 2]`. Object-документы не меняются. Сериализатор принимает
  top-level `list` / `tuple` и пишет items голыми, по одному на
  строку, без обрамляющих `[...]`.
- **`ktav.dumps_force_strings(obj)`** — рендер с приведением каждого
  лист-скаляра к String (типизированные integer/float, bool и
  `None` уплощаются до текстовой формы и пишутся через сырой
  маркер `::`, чтобы вывод round-tripил обратно как те же
  string-скаляры). Compounds сохраняют структуру; коэрсятся только
  листья. Python-идиоматичный snake_case-параллель `dumps` /
  `loads`.

### Изменено

- **Подхватили `ktav 0.3.1`** — добавляет format-level top-level
  Array и API `to_string_force_strings`, в который делегирует
  новая Python-точка. См.
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#031--2026-05-10).
- `ktav.dumps(list_or_tuple)` больше не бросает — теперь рендерит
  top-level Array по spec § 5.0.1.
- `__spec_version__` поднят до `0.1.1`.

### Спецификация

- spec submodule синхронизирован на `7256816` (Ktav 0.1.1 —
  top-level Array fixtures под
  `versions/0.1/tests/valid/top_level_array/` и
  `versions/0.1/tests/invalid/top_level/`).


## [0.3.0] — 2026-05-08

### Изменено (ломающее)

- **Подхватили `ktav 0.3.0`** — изменение upstream Rust crate по
  отклонению paren-strings. Inline paren-обёрнутые скаляры вида
  `a: (hello)` и `a: ((wrapped))` теперь decode error. PyO3 binding
  наследует поведение прозрачно. См.
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#030--2026-05-08).

### Спецификация

- spec submodule синхронизирован на `46d94a7` (новые invalid fixtures
  `inline_paren_string_double` и `inline_paren_string_single`,
  ужесточён `partial_parens` valid-fixture).


## [0.2.0] — 2026-05-07

### Изменено (ломающее)

- **Подхватили `ktav 0.2.0`** — многострочные строки теперь по
  умолчанию сериализуются в indented stripped форме `( ... )`. `:f 42`
  принимает целочисленные литералы (парсится как `42.0`). См.
  [`ktav` crate CHANGELOG](https://github.com/ktav-lang/rust/blob/main/CHANGELOG.md#020--2026-05-07).


## [0.1.2] — 2026-05-03

### Изменено

- **Подхватили `ktav 0.1.5`** — в upstream Rust crate появился API
  структурированных ошибок (`Error::Structured(ErrorKind)` с
  byte-offset spans), retroactive `#[non_exhaustive]` на error-enum-ах,
  и публичный event-based парсер `ktav::thin`. Поведение PyO3 binding
  для пользователя не меняется: `KtavDecodeError` / `KtavEncodeError`
  по-прежнему несут те же читаемые сообщения (Display-строки семи
  канонических категорий byte-identical к ktav 0.1.4). Маппинг
  `ktav::ErrorKind` на структурную Python-иерархию исключений
  (`MissingSeparatorSpace`, `DuplicateKey`, и т.д.) — отдельная
  follow-up задача, описанная в
  [`STRUCTURED_ERRORS.md`](https://github.com/ktav-lang/.github/blob/main/STRUCTURED_ERRORS.md).

PyPI: `ktav==0.1.2`.

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
