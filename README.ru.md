# ktav (Python)

[![PyPI](https://img.shields.io/pypi/v/ktav?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/ktav/)
[![CI](https://img.shields.io/github/actions/workflow/status/ktav-lang/python/CI.yml?style=flat-square&logo=github&label=CI)](https://github.com/ktav-lang/python/actions)
![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue?style=flat-square)
[![Playground](https://img.shields.io/badge/playground-try%20online-7c3aed?style=flat-square&logo=rocket&logoColor=white)](https://ktav-lang.github.io/)

> Python-биндинги для [Ktav](https://github.com/ktav-lang/spec) — простого
> формата конфигов. Форма JSON, без кавычек, без запятых, вложенность через
> точки в ключах. Под капотом — Rust.

**Языки:** [English](README.md) · **Русский** · [简体中文](README.zh.md)

**Песочница:** конвертация JSON / YAML / TOML / INI ⇄ Ktav прямо в браузере — **[ktav-lang.github.io](https://ktav-lang.github.io/)**.

**Спецификация:** этот пакет реализует **Ktav**. Формат версионируется
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
- Ключ словаря не-`str` → `KtavEncodeError`.

## Экранирование в ключах

Начиная со spec 0.6.0 литеральные `.` или `:` внутри сегмента ключа
записываются через backslash:

```text
a\.b: v        # ключ — один сегмент "a.b"     -> {"a.b": "v"}
a\:b: v        # двоеточие внутри ключа        -> {"a:b": "v"}
x.y\.z: v      # делим только по первой точке  -> {"x": {"y.z": "v"}}
```

Литеральный backslash в ключе пишется как `\\`.

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

MIT OR Apache-2.0. См. [LICENSE-MIT](LICENSE-MIT) и [LICENSE-APACHE](LICENSE-APACHE).
