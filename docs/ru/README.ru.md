# ktav (Python)

[![PyPI](https://img.shields.io/pypi/v/ktav?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/ktav/)
[![CI](https://img.shields.io/github/actions/workflow/status/ktav-lang/python/CI.yml?style=flat-square&logo=github&label=CI)](https://github.com/ktav-lang/python/actions)
![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue?style=flat-square)
[![Playground](https://img.shields.io/badge/playground-try%20online-7c3aed?style=flat-square&logo=rocket&logoColor=white)](https://ktav-lang.github.io/)

> Python-биндинги для [Ktav](https://github.com/ktav-lang/spec) — простого
> формата конфигов. Форма JSON, кавычки не обязательны, без запятых, вложенность
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

По умолчанию используется native backend: соответствующий platform wheel содержит наше встроенное Rust-ядро. Зависимости Python для работы не нужны. Поддерживаемые wheels рассчитаны на Python 3.9+.

Если подходящего wheel нет, установка из исходников компилирует native-расширение на Rust с помощью maturin; нужны Rust toolchain и заголовочные файлы Python. Установка из исходников не переключается на pure mode.

### Чистый Python

Для универсального wheel явно установите существующий артефакт `py3-none-any`:

```
pip install ./ktav-0.8.1-py3-none-any.whl
```

Затем явно выберите pure API:

```
from ktav import pure





doc = pure.loads("server.port: 8080")
text = pure.dumps({"server": {"port": 8080}})
formatted = pure.format(text)
```

Pure backend предоставляет полный parser, writer, formatter и ошибки Ktav, используя только стандартную библиотеку Python. Сторонние пакеты не нужны; он не загружает `_core` или WASM и не запускает сеть либо subprocess. Выбор выполняется явно; native backend по умолчанию никогда не переключается на pure незаметно.

`tomli` может быть в test/dev extras для инструментов на старых версиях Python; это не runtime-зависимость.

```python
from ktav import pure

config = pure.loads(open("config.ktav").read())
text = pure.dumps({"port": 8080})
formatted = pure.format(open("config.ktav").read())
```

Pure-режим реализует весь публичный набор операций — `loads`, `loads_strict`, `dumps`, `emit_canonical`, `dumps_force_strings`, `format`, `canonical_from_source` (плюс `load`/`dump`) — с тем же десятипольным конвертом ошибок, по spec 0.8.1. Выбирайте его, когда нет Rust toolchain, когда под вашу платформу нет wheel, для встраивания или когда нужна реализация, которую можно проаудировать в чистом Python. Честный компромисс: pure-режим работает со скоростью Python, а не нативного расширения — никаких заявлений о скорости в обе стороны. Глобального флага выбора backend нет, тихого fallback тоже нет: backend выбирается тем, какой модуль вы импортируете.

Начиная с 0.8.1 чистый backend поставляется и как реальный артефакт установки: универсальный pure wheel `ktav-0.8.1-py3-none-any.whl` (то же имя дистрибуции, та же версия) публикуется на PyPI рядом с нативными платформенными wheel-ами. Чтобы его поставить, скачайте или выберите pure wheel (`py3-none-any`) среди файлов релиза или на PyPI; `pip` при наличии подходящего платформенного wheel автоматически предпочитает его. Pure wheel ставится без Rust toolchain, компилятора и maturin и предоставляет ровно backend `ktav.pure` — нативные функции верхнего уровня тогда бросают понятный `ImportError` с указанием на `from ktav import pure`.

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

> **Ещё не выпущено (подготовка 0.9):** Эти API редактирования и обновлённая диагностика не входят в опубликованные пакеты 0.8.1. Native-backend требует закреплённое ядро 0.9 (C ABI 2 для C-FFI); pure-backend остаётся самостоятельным.

### Правка исходника — `edit_value` / `edit_value_segments`

```python
import ktav

out = ktav.edit_value("port: 8080\nhost: db\n", "port", 9090)
# "port: 9090\nhost: db\n"

out = ktav.edit_value_segments("a: {x: 1, y: 2}\n", ["a", "y"], {"n": [1]})
# "a: {x: 1, y: {n: [1]}}\n"
```

`edit_value` принимает текстовый путь (`key1.key2.0.key4`): внутри
сегмента `\.` — literal точка, `\\` — literal backslash; любой другой
escape бросает `KtavInvalidPathError`, у которого `body` — десятичный
UTF-8 byte offset проблемного места. `edit_value_segments` принимает
уже декодированные literal-сегменты без повторного unescape — числовой
сегмент это строковый ключ в Object и zero-based индекс в Array.
Поддерживается только замена существующего значения: отсутствующий
ключ, выход за границы массива и спуск сквозь скаляр дают
`KtavNotFoundError`.

Правка — это splice исходника, а не parse→mutate→serialize всего
документа: комментарии, написание ключей, порядок, пробелы, BOM и
CR/LF/CRLF вне эффективного изменения сохраняются побайтово,
dotted/inline/block-формы держатся, а совпадающая замена —
byte-identical no-op, даже при неканоничном написании. Каждый
успешный патч перепарсится и семантически проверяется. Когда lossless
патча не существует (noncontiguous dotted/reopen-цели, внутренние
комментарии при структурной замене, непредставимое в контексте цели
значение), вызов бросает `KtavUnsupportedError`, а не угадывает. Длинные
и многострочные замены раскрывают только затронутые inline-обёртки;
нетронутые ветки остаются inline. Native и pure backend реализуют
идентичную семантику.

### Практические примеры правки исходника

Примеры относятся к ещё не выпущенному API 0.9, а не к опубликованному пакету 0.8.1. Они заменяют только существующие значения: не переименовывают ключи, не создают отсутствующие пути и не удаляют записи. Фрагменты независимы; Rust `?` предполагает внешнюю функцию с результатом `Result`. В Go panic используется только для фиксированных корректных данных примера; приложение должно обработать возвращённую ошибку.

Примеры привязок используют самостоятельный pure-бэкенд без native-бинарника. Нативные точки входа принимают те же пути и значения: `ktav.EditValue` (Go), `Ktav.editValue` (Java), `KtavApi.EditValue(..., KtavBackend.Native)` (C#), `Ktav::editValue` (PHP), native/FFI-экспорты пакета (JS), `ktav.edit_value` (Python). C ABI требует версию 2; PyO3/N-API/WASM — совместимое ядро подготовки 0.9. FFI-вызовы Bun/Deno возвращают promise и требуют `await`; показанные pure/Node/WASM-варианты синхронны.

```python
import ktav.pure as ktav
```

#### 1. Настройка развёртывания через dotted-ключ

Меняется только адрес; комментарий, dotted-форма и соседнее поле пользователя сохраняются байт-в-байт.

```python
source = "## deployment\ntargets.storagehost.address: old\ntargets.storagehost.user: mcp-agent\n"
updated = ktav.edit_value(source, "targets.storagehost.address", "192.168.0.88:22")
```

Результат:

```ktav
## deployment
targets.storagehost.address: 192.168.0.88:22
targets.storagehost.user: mcp-agent
```

#### 2. Буквальные точки: текстовый путь или сегменты

Ключ исходника в кавычках буквально называется `a.b`. В текстовом пути точка экранируется; API сегментов получает декодированное имя напрямую. Оба вызова возвращают одинаковый результат.

```python
source = "\"a.b\": {port: 80}\n"
updated = ktav.edit_value(source, "a\\.b.port", 90)
same = ktav.edit_value_segments(source, ["a.b", "port"], 90)
```

Результат:

```ktav
"a.b": {port: 90}
```

#### 3. Лист внутри массива со смешанными формами

Здесь `0` — индекс массива. В объекте такой же сегмент обозначал бы ключ с именем `0`; нетронутые контейнеры остаются inline.

```python
source = "servers: [{host: old, keep: yes}, standby]\n"
updated = ktav.edit_value_segments(source, ["servers", "0", "host"], "new")
```

Результат:

```ktav
servers: [{host: new, keep: yes}, standby]
```

#### 4. Похожая на число строка остаётся строкой

Замена имеет тип String, а не Integer. Raw-маркер сохраняет это различие. Для числового значения передавайте типизированный Integer.

```python
source = "port: 8080\n"
updated = ktav.edit_value(source, "port", "9090")
```

Результат:

```ktav
port:: 9090
```

#### 5. Многострочная замена: раскрывается только необходимое

Изменённый массив раскрывается с отступом четыре пробела. Нетронутый объект остаётся inline, содержимое verbatim-строки не переотступается.

```python
source = "a: [old, {keep: yes}]\n"
updated = ktav.edit_value(source, "a.0", "x\ny")
```

Результат:

```ktav
a: [
    ((
x
y
    ))
    {keep: yes}
]
```

#### 6. No-op сохраняет неканоническое написание

Значение Integer уже равно 1. Проверка равенства возвращает исходные байты, включая `+1` и пробелы разделителя; критерии читаемости не применяются.

```python
source = "n  : +1\n"
updated = ktav.edit_value(source, "n", 1)
assert updated == source
```

Результат:

```ktav
n  : +1
```

#### 7. BOM, CRLF и последняя строка без перевода

Результат сохраняет BOM и CRLF, не добавляя финальный перевод строки. Экранированное представление делает эти байты видимыми.

```python
source = "\ufeffport: 8080\r\nhost: db"
updated = ktav.edit_value(source, "port", 9090)
```

Результат:

```text
"\uFEFFport: 9090\r\nhost: db"
```

Критерии раскрытия фиксированы: многострочная замена, рост сверх `max(100, исходная длина строки)` либо не менее четырёх экранирований с накладными расходами от 25% для отдельной строки замены. Ширина считается в Unicode scalar values, а не байтах UTF-8 или колонках терминала. Уже длинная строка без роста сохраняется. Новые уровни используют четыре пробела и EOL исходника. Если CR или строка данных `))` мешают lossless-кодированию вне inline, сохраняется корректный inline-вариант; эти символы не означают автоматический отказ любой inline-правки.

#### 8. Точная замена Integer

Домен Integer в исходнике — знаковый 64-битный. Это значение больше безопасного диапазона JavaScript Number, но помещается в i64; используйте точное host-представление, а не округлённое число с плавающей точкой. Типизированный Integer вне i64 невозможно сохранить в исходнике как Integer: правка отказывает, не обрезая значение. Для текстового большого идентификатора используйте String. Float различает отрицательный и положительный нуль; no-op для Object не зависит от порядка ключей, порядок Array значим.

```python
updated = ktav.edit_value("n: 1\n", "n", 9007199254740993)
```

```ktav
n: 9007199254740993
```

### Диагностика и безопасные отказы в 0.9

Координаты исходника — байтовые смещения UTF-8 с учётом BOM; spans полуоткрыты `[start, end)`, строки нумеруются с 1. Поддерживаются LF, отдельный CR и CRLF; CRLF считается одним переводом строки. Один Unicode-символ может занимать несколько байтов.

Незавершённый `a: [\n` даёт `UnclosedCompound`, строку 1 и span `3..5`: начало — самая внутренняя незакрытая скобка, а не начало ключа или строки. Для сырых байтов `61 3A 20 FF` (`a: ` и невалидный UTF-8) валидация сообщает `InvalidUtf8`, строку 1 и покрывающий span `3..4`; `line_text` равен null, а не придуманному тексту после lossy-декодирования. Проверка UTF-8 предшествует грамматике.

Некорректный текстовый путь, включая пустой путь или пустой текстовый сегмент, даёт `EditInvalidPath`; смещение считается в байтах UTF-8 самого пути. Пустой список сегментов, отсутствующий ключ, индекс вне диапазона или спуск через скаляр дают `EditNotFound`. В объекте числовой сегмент остаётся ключом; индекс массива содержит ASCII-цифры, допускает ведущие нули, но не знаки.

Целые промежуточные объекты из dotted/reopened-определений могут занимать несколько физических диапазонов и давать `EditUnsupported`; их существующие листья остаются редактируемыми. Структурная замена контейнера не должна удалять внутренние комментарии. Ошибка не возвращает частичный патч и не меняет переданный исходник. Результат повторно разбирается и семантически проверяется: цель должна равняться замене, остальное дерево значений — исходному.

В привязках ошибочный исходник даёт обычный конверт парсера до проверки пути. Некорректный wire-payload — ошибка `Message` без выдуманных координат. Wire-конверт содержит `error`, `reason`, `line`, `line_text`, `span`, `path`, `body`, `canonical`, `spec_section`, `message`; имена host-accessors описаны в разделе ошибок. В `body` находятся десятичное байтовое смещение пути для `EditInvalidPath`, null для `EditNotFound` и причина отказа для `EditUnsupported`.

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
| голое целое (в пределах 64 бит)   | `int`    |
| целое за пределами 64 бит         | `str`    |
| голое десятичное     | `float`  |
| прочий скаляр        | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav типизирует числа по **лексической форме** — голый `port: 8080`
это `int`, `ratio: 0.5` — `float`, а всё, что не является голым
числом, остаётся `str`. Чтобы число-подобное значение осталось
строкой, форсируйте его через `::` (`zip:: 01007`).

Домен Integer совпадает с нативным расширением (64 бита со знаком):
целочисленный литерал за пределами `i64` разбирается как `str` и
повторно выводится через сырой маркер `::`, чтобы остаться строкой —
поведение одинаково в обоих backend-ах.

`dict` сохраняет порядок вставки (гарантия Python 3.7+), что совпадает с
семантикой упорядоченных объектов Ktav.

Сериализация — обратное соответствие:

- Python `int` → голое целое (в том числе bigint произвольной точности;
  при чтении такой литерал вернётся как `str` — см. выше).
- Python `float` → голое десятичное (точка всегда присутствует;
  `NaN` / `±Infinity` отвергаются — Ktav их не представляет).
- Python `tuple` допустим как массив, симметрично `list`.
- Ключи `dict`, не являющиеся `str`, вызывают `KtavEncodeError`.

## Экранирование в ключах

Начиная со spec 0.6.4, литеральные `.` или `:` внутри сегмента ключа
записываются через обратный слеш:

```text
a\.b: v
a\:b: v
x.y\.z: v
a."b.c".d: v
"\u0041": v
```

Литеральный обратный слеш в ключе пишется как `\\`. Начиная со spec 0.7,
сегмент можно также взять в двойные, одинарные кавычки или обратные апострофы.
Кавычки ограничивают только сегменты ключа, не значения; `\uXXXX` декодирует
кодовую точку Unicode.

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

Оба backend-а бросают одни и те же исключения с идентичным
десятипольным конвертом. Одно осознанное отличие: для входной `str`
с литеральными lone-суррогатами pure-режим бросает `KtavDecodeError`
с категорией ошибки `InvalidUtf8` и непустым span над некорректными байтами,
тогда как нативное расширение отдаёт `UnicodeEncodeError`.

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

В этот пакет входят два backend-а. **Нативный** — по умолчанию:
API верхнего уровня `ktav` — это тонкая PyO3-обёртка над Rust-ядром
(0.8.1). **Чистый** backend, `ktav.pure`, — полноценные парсер и
генератор на чистом Python, без скомпилированного расширения.
Глобального флага выбора backend нет, тихого fallback тоже нет:
backend выбирается импортом, а CI проверяет побайтовую идентичность
канонического вывода обоих. Чистый backend поставляется также в виде
универсального pure wheel (`ktav-0.8.1-py3-none-any.whl`),
публикуемого рядом с нативными платформенными wheel-ами.

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
