# ktav (Python)

> Python-биндинги для [Ktav](https://github.com/ktav-lang/spec) — простого
> формата конфигов. Форма JSON, без кавычек, без запятых, вложенность через
> точки в ключах. Под капотом — Rust.

**Языки:** [English](README.md) · **Русский** · [简体中文](README.zh.md)

**Спецификация:** этот пакет реализует **Ktav 0.1**. Формат версионируется
и развивается отдельно — см.
[`ktav-lang/spec`](https://github.com/ktav-lang/spec) для нормативного
документа.

---

## Установка

```
pip install ktav
```

Готовые wheel-ы публикуются для всех основных платформ и поддерживаемых
версий Python:

- **Linux** (manylinux + musllinux) — `x86_64`, `aarch64`
- **macOS** — `x86_64`, `arm64` (Apple Silicon)
- **Windows** — `x64`, `arm64`

Требуется Python **3.9+**. Wheel-ы собраны под стабильный ABI
(`abi3-py39`), поэтому одного wheel на платформу хватает для всех
поддерживаемых версий CPython.

Если под вашу платформу нет готового wheel, `pip` откатится на sdist и
соберёт расширение локально — для этого нужен Rust toolchain
(`rustup`) и заголовочные файлы Python-разработчика.

## Быстрый старт

### Парсинг — типизированно читаем поля

```python
import ktav

src = """
service: web
port:i 8080
ratio:f 0.75
tls: true
tags: [
    prod
    eu-west-1
]
db.host: primary.internal
db.timeout:i 30
"""

cfg = ktav.loads(src)

service: str = cfg["service"]
port:    int = cfg["port"]
ratio: float = cfg["ratio"]
tls:    bool = cfg["tls"]
tags: list[str] = cfg["tags"]
db_host:    str = cfg["db"]["host"]
db_timeout: int = cfg["db"]["timeout"]
```

### Обход — диспатч по runtime-типу

```python
for k, v in cfg.items():
    if v is None:              kind = "null"
    elif isinstance(v, bool):  kind = f"bool={v}"   # bool первым — True это int!
    elif isinstance(v, int):   kind = f"int={v}"
    elif isinstance(v, float): kind = f"float={v}"
    elif isinstance(v, str):   kind = f"str={v!r}"
    elif isinstance(v, list):  kind = f"array({len(v)})"
    elif isinstance(v, dict):  kind = f"object({len(v)})"
    print(f"{k} -> {kind}")
```

### Билд + рендер — собираем документ в коде

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
```

Полный запускаемый пример — в [`examples/basic.py`](examples/basic.py).

Четыре публичные функции — форма повторяет стандартный `json`:

| Функция               | Назначение                                    |
|-----------------------|-----------------------------------------------|
| `ktav.loads(s)`       | Разобрать строку Ktav (или UTF-8 `bytes`).    |
| `ktav.dumps(obj)`     | Сериализовать нативное значение Python.       |
| `ktav.load(fp)`       | Разобрать из файла-подобного объекта.         |
| `ktav.dump(obj, fp)`  | Сериализовать в файл-подобный объект.         |

`load` / `dump` принимают как текстовый, так и бинарный режим файла.

## Соответствие типов

| Ktav                 | Python   |
|----------------------|----------|
| `null`               | `None`   |
| `true` / `false`     | `bool`   |
| `:i <digits>`        | `int`    |
| `:f <number>`        | `float`  |
| скаляр без маркера   | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav живёт по принципу **«никакой магии в типах»** — голый `port: 8080`
на уровне парсера остаётся строкой. Нужны числа — используйте
маркеры `:i` / `:f`, либо приводите типы сами на прикладном уровне.

`dict` сохраняет порядок вставки (гарантия Python 3.7+), что совпадает с
семантикой упорядоченных объектов Ktav.

Сериализация — обратное соответствие:

- Python `int` → маркер `:i` (в том числе bigint произвольной точности).
- Python `float` → маркер `:f` (точка всегда присутствует;
  `NaN` / `±Infinity` отвергаются — Ktav 0.1.0 их не представляет).
- Python `tuple` допустим как массив, симметрично `list`.
- Ключ словаря не-`str` → `KtavEncodeError`.

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

# Ловля базового класса перехватывает оба варианта.
try:
    ktav.loads("a: 1\na: 2")
except ktav.KtavError:
    ...
```

| Исключение          | Источник          | База                |
|---------------------|-------------------|---------------------|
| `KtavError`         | (базовое)         | `Exception`         |
| `KtavDecodeError`   | `loads` / `load`  | `KtavError`         |
| `KtavEncodeError`   | `dumps` / `dump`  | `KtavError`         |

## Философия

Ktav намеренно маленький. Пять принципов проектирования
(из [`spec/CONTRIBUTING.md`](https://github.com/ktav-lang/spec/blob/main/CONTRIBUTING.md)):

1. **Локальность** — смысл строки не зависит от другой строки.
2. **Одно предложение** — новое правило умещается в одну фразу спеки.
3. **Нет чувствительности к пробелам** (кроме переноса строк).
4. **Никакой магии в типах** — формат не решает, что `"8080"` — число.
5. **Явно лучше, чем хитро** — `::` избыточен намеренно.

Python-биндинги живут по тем же правилам: никакой inference-ы схемы,
никакого авто-каста, никаких defaults. Хотите типизацию — делайте её
на границе своим инструментом (`pydantic`, `dataclasses`, `attrs`)
поверх нативных Python-структур, которые вернула эта библиотека.

## Связанные проекты

- [`ktav-lang/spec`](https://github.com/ktav-lang/spec) — нормативная
  спецификация формата и language-agnostic conformance-тесты.
- [`ktav-lang/rust`](https://github.com/ktav-lang/rust) — reference
  Rust-реализация. Текущие Python-биндинги — тонкая PyO3-обёртка над
  этой библиотекой.

## Версионирование

Пакет следует [Semantic Versioning](https://semver.org/) с pre-1.0
соглашением: минорный bump — ломающий. Версия Python-пакета и версия
крейта `ktav` движутся вместе. `ktav.__spec_version__` показывает
версию формата Ktav, которую поддерживает данный биндинг.

## Разработка

Dev-окружение, структура тестов и процесс вклада описаны в
[CONTRIBUTING.md](CONTRIBUTING.md) (и в
[CONTRIBUTING.ru.md](CONTRIBUTING.ru.md)).

## Поддержите проект

У автора много идей, которые могут быть полезны IT во всём мире, — и
далеко не только для Ktav. Их реализация требует финансирования. Если
вы хотите помочь — пишите на **phpcraftdream@gmail.com**.

## Лицензия

MIT. См. [LICENSE](LICENSE).
