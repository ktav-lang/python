# ktav (Python)

[![PyPI](https://img.shields.io/pypi/v/ktav?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/ktav/)
[![CI](https://img.shields.io/github/actions/workflow/status/ktav-lang/python/CI.yml?style=flat-square&logo=github&label=CI)](https://github.com/ktav-lang/python/actions)
![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue?style=flat-square)
[![Playground](https://img.shields.io/badge/playground-try%20online-7c3aed?style=flat-square&logo=rocket&logoColor=white)](https://ktav-lang.github.io/)

> Python-биндинги для [Ktav](https://github.com/ktav-lang/spec) — простого
> формата конфигов. Форма JSON, без кавычек, без запятых, вложенность
> через точки в ключах. Под капотом — Rust.

**Languages:** [English](../../README.md) · **Русский** · [简体中文](../zh/README.zh.md)

**Песочница:** конвертация JSON / YAML / TOML / INI ⇄ Ktav прямо в браузере — **[ktav-lang.github.io](https://ktav-lang.github.io/)**.

**Спецификация:** этот пакет реализует **Ktav**. Формат версионируется
и поддерживается независимо от этого пакета — нормативный документ см.
в [`ktav-lang/spec`](https://github.com/ktav-lang/spec).

---

## Установка

```
pip install ktav
```

Готовые wheel-ы публикуются для всех основных платформ и всех
поддерживаемых версий Python:

- **Linux** (manylinux + musllinux) — `x86_64`, `aarch64`
- **macOS** — `x86_64`, `arm64` (Apple Silicon)
- **Windows** — `x64`, `arm64`

Требуется Python **3.9+**. Wheel-ы собраны под стабильный ABI
(`abi3-py39`), поэтому одного wheel на платформу хватает для всех
поддерживаемых релизов CPython.

Если под вашу платформу нет готового wheel, `pip` откатится на исходники
и соберёт расширение локально — для этого нужен Rust toolchain
(`rustup`) и заголовочные файлы Python-разработки.

## Быстрый старт

### Парсинг — типизированно читаем поля прямо из dict

```python
import ktav

src = """
service: web
port: 8080
ratio: 0.75
tls: true
tags: [
    prod
    eu-west-1
]
db.host: primary.internal
db.timeout: 30
"""

cfg = ktav.loads(src)

service: str = cfg["service"]
port: int = cfg["port"]
ratio: float = cfg["ratio"]
tls: bool = cfg["tls"]
tags: list[str] = cfg["tags"]
db_host: str = cfg["db"]["host"]
db_timeout: int = cfg["db"]["timeout"]
```

### Обход — диспатч по runtime-типу

```python
for k, v in cfg.items():
    if v is None:
        kind = "null"
    elif isinstance(v, bool):
        kind = f"bool={v}"  # bool first — True is also an int!
    elif isinstance(v, int):
        kind = f"int={v}"
    elif isinstance(v, float):
        kind = f"float={v}"
    elif isinstance(v, str):
        kind = f"str={v!r}"
    elif isinstance(v, list):
        kind = f"array({len(v)})"
    elif isinstance(v, dict):
        kind = f"object({len(v)})"
    print(f"{k} -> {kind}")
```

### Сборка и рендер — конструируем документ в коде

```python
doc = {
    "name": "frontend",
    "port": 8443,
    "tls": True,
    "ratio": 0.95,
    "upstreams": [
        {"host": "a.example", "port": 1080},
        {"host": "b.example", "port": 1080},
    ],
    "notes": None,
}
text = ktav.dumps(doc)
# name: frontend
# port: 8443
# tls: true
# ratio: 0.95
# upstreams: [
#     { host: a.example  port: 1080 }
#     { host: b.example  port: 1080 }
# ]
# notes: null
```

Полный запускаемый пример — в [`examples/basic.py`](../../examples/basic.py).

### Форматирование — нормализуем файл, сохраняя комментарии

```python
import ktav

print(ktav.format(open("config.ktav").read()))
```

`ktav.format` переписывает документ в канонической форме (§ 5.9),
сохраняя каждый комментарий дословно. Серии пустых строк схлопываются в
одну, пустой отступ внутри скобок выбрасывается — поэтому форматирование
является неподвижной точкой и его безопасно ставить в pre-commit хук.
Порядок ключей не меняется никогда.

Канонический вывод дают три функции, и они различаются тем, что
принимают и что сохраняют:

| | вход | комментарии | пустые строки |
| --- | --- | --- | --- |
| `ktav.format(src)` | исходный текст | **сохраняются** | **сохраняются** (серия схлопывается в одну) |
| `ktav.canonical_from_source(src)` | исходный текст | отбрасываются | отбрасываются |
| `ktav.emit_canonical(obj)` | объект Python | сохранять нечего | сохранять нечего |

Выбирайте по тому, что у вас в руках: `emit_canonical` — когда объект,
`canonical_from_source` — когда текст и не нужно строить промежуточное
значение Python, `format` — когда нужно сохранить собственные
комментарии и группировку документа.

В отличие от биндингов для JavaScript, `canonical_from_source` не даёт
здесь дополнительной численной точности: Python различает `int` и
`float`, поэтому различие Integer/Float из Ktav переживает `loads`, и
`emit_canonical(loads(src))` выдаёт те же байты, что и
`canonical_from_source(src)`. Оба пишут float по каноническому правилу
(§ 5.9.8), а не копируют исходную запись, поэтому
`1.23456789012345678901` превращается в `1.2345678901234567` любым из
путей.

`ktav.dumps_force_strings(obj)` выводит как `dumps`, но приводит каждый
leaf-скаляр — integer, float, bool, null — к String через сырой маркер
`::`. Составные значения сохраняют структуру.

Четыре точки входа повторяют стандартный модуль `json`:

| Функция              | Назначение                                    |
|-----------------------|----------------------------------------------|
| `ktav.loads(s)`      | Разобрать строку Ktav (или UTF-8 `bytes`).    |
| `ktav.dumps(obj)`    | Сериализовать нативное значение Python.       |
| `ktav.load(fp)`      | Разобрать из файло-подобного объекта.         |
| `ktav.dump(obj, fp)` | Сериализовать в файло-подобный объект.        |

`load` / `dump` принимают файлы как в текстовом, так и в бинарном режиме.

Для проверки на границах доверия `ktav.loads_strict(s)` применяет
канонические правила спецификации для скаляров и выбрасывает
`KtavDecodeError` при потере записи скаляра. Формы canonical writer,
например `1e-3` и `1e10`, принимаются и дают те же нативные значения,
что и `loads`.

## Соответствие типов

| Ktav                 | Python   |
|----------------------|----------|
| `null`               | `None`   |
| `true` / `false`     | `bool`   |
| голое целое          | `int`    |
| голое десятичное     | `float`  |
| прочий скаляр        | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav типизирует числа по **лексической форме** — голый `port: 8080`
это `int`, `ratio: 0.5` — `float`, а всё, что не является голым
числом, остаётся `str`. Чтобы число-подобное значение осталось
строкой, форсируйте его через `::` (`zip:: 01007`).

`dict` сохраняет порядок вставки (гарантия Python 3.7+), что совпадает с
семантикой упорядоченных объектов Ktav.

Сериализация — обратное соответствие:

- Python `int` → голое целое (в том числе bigint произвольной точности).
- Python `float` → голое десятичное (точка всегда присутствует;
  `NaN` / `±Infinity` отвергаются — Ktav их не представляет).
- Python `tuple` допустим как массив, симметрично `list`.
- Ключи `dict`, не являющиеся `str`, вызывают `KtavEncodeError`.

## Экранирование в ключах

Начиная со spec 0.6.4, литеральные `.` или `:` внутри сегмента ключа
записываются через обратный слеш:

```text
a\.b: v        # key is the single segment "a.b" -> {"a.b": "v"}
a\:b: v        # key contains a colon            -> {"a:b": "v"}
x.y\.z: v      # split on the first dot only     -> {"x": {"y.z": "v"}}
```

Литеральный обратный слеш в ключе пишется как `\\`.

## Ошибки

```python
import ktav

try:
    ktav.loads("x: [")
except ktav.KtavDecodeError as e:
    print("decode:", e)

try:
    ktav.dumps({"v": float("nan")})
except ktav.KtavEncodeError as e:
    print("encode:", e)

# Catching the base class catches either.
try:
    ktav.loads("a: 1\na: 2")
except ktav.KtavError:
    ...
```

| Исключение          | Источник          | База                |
|---------------------|-------------------|---------------------|
| `KtavError`         | (базовое)        | `Exception`         |
| `KtavDecodeError`   | `loads` / `load`  | `KtavError`         |
| `KtavEncodeError`   | `dumps` / `dump`  | `KtavError`         |

Начиная с 0.7.1 каждое брошенное исключение несёт ещё и структурный
конверт ошибки в виде атрибутов: `error`, `reason`, `line`, `line_text`,
`span`, `path`, `body`, `canonical`, `spec_section`. Отсутствующие
сведения — `None`, а не пропущенный атрибут. `span` — это
`{"start": …, "end": …}`, смещения в байтах по UTF-8-исходнику;
`path` — список точных декодированных сегментов ключа (ключ, буквально
названный `a.b`, — это один сегмент, и он никогда не разрезается).
`str(e)` остаётся человекочитаемым сообщением — сырой конверт вместо
него не подставляется.

`e.message` несёт тот же текст атрибутом, то есть **`str(e) ==
e.message`**. Здесь он избыточен намеренно: этот биндинг всегда брал для
`str(e)` собственный рендеринг ядра, а атрибут существует ради того,
чтобы конверт в Python имел ту же форму из десяти полей, что и в любом
другом языке, — там `message` единственный способ добраться до текста.
Пользуйтесь им, а не собирайте фразу заново из `error`, `line` и `body`:
пересобранное сообщение отличается от биндинга к биндингу, а это — нет.

## Философия

Ktav намеренно маленький. Пять принципов проектирования
(из [`spec/CONTRIBUTING.md`](https://github.com/ktav-lang/spec/blob/main/CONTRIBUTING.md)):

1. **Локальность** — смысл строки не зависит от другой строки.
2. **Одно предложение** — новое правило умещается в одну фразу спеки.
3. **Нет чувствительности к пробелам** (кроме переноса строк).
4. **Никакой магии в типах** — формат не решает, что `"8080"` — число.
5. **Явно лучше, чем хитро** — `::` избыточен намеренно.

Python-биндинги следуют этому: никакой inference-ы схемы, никакого
авто-каста, никаких значений по умолчанию. Хотите типизацию — делайте её
на границе своим инструментом (`pydantic`, `dataclasses`, `attrs`)
поверх нативных Python-структур, которые вернула эта библиотека.

## Другие реализации Ktav

- [`spec`](https://github.com/ktav-lang/spec) — спецификация + conformance-тесты
- [`rust`](https://github.com/ktav-lang/rust) — эталонный Rust crate (`cargo add ktav`); этот Python-биндинг — тонкая PyO3-обёртка над ним
- [`csharp`](https://github.com/ktav-lang/csharp) — C# / .NET (`dotnet add package Ktav`)
- [`golang`](https://github.com/ktav-lang/golang) — Go (`go get github.com/ktav-lang/golang`)
- [`java`](https://github.com/ktav-lang/java) — Java / JVM (`io.github.ktav-lang:ktav` на Maven Central)
- [`js`](https://github.com/ktav-lang/js) — JS / TS (`npm install @ktav-lang/ktav`)
- [`php`](https://github.com/ktav-lang/php) — PHP (`composer require ktav-lang/ktav`)

## Версионирование

Пакет следует [Semantic Versioning](https://semver.org/) с pre-1.0
соглашением: минорный bump — ломающий. Версия пакета и версия крейта
`ktav` движутся вместе. `ktav.__spec_version__` показывает версию
формата Ktav, которую поддерживает данный биндинг.

## Разработка

Настройка dev-окружения, структура тестов и процесс внесения вклада
описаны в [CONTRIBUTING.md](../CONTRIBUTING.md) (и в
[CONTRIBUTING.ru.md](CONTRIBUTING.ru.md)).

## Поддержите проект

У автора много идей, которые могут быть полезны IT во всём мире, — и
далеко не только для Ktav. Их реализация требует финансирования. Если
вы хотите помочь — пишите на **phpcraftdream@gmail.com**.

## Лицензия

MIT OR Apache-2.0. См. [LICENSE-MIT](../../LICENSE-MIT) и [LICENSE-APACHE](../../LICENSE-APACHE).
