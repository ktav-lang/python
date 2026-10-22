>>>>> lang=en


doc = pure.loads("server.port: 8080")
text = pure.dumps({"server": {"port": 8080}})
formatted = pure.format(text)
```

The pure backend provides the full parser, writer, formatter, and Ktav errors using only the Python standard library. It does not require third-party packages and does not load `_core`, WASM, or invoke network or subprocesses. It is explicitly selected; the native default never silently falls back to it.

`tomli` may appear in test or development extras for tooling on older Python versions; it is not a runtime dependency.

```python
from ktav import pure

config = pure.loads(open("config.ktav").read())
text = pure.dumps({"port": 8080})
formatted = pure.format(open("config.ktav").read())
```

Pure mode implements the full public operation set — `loads`, `loads_strict`, `dumps`, `emit_canonical`, `dumps_force_strings`, `format`, `canonical_from_source` (plus `load`/`dump`) — with the same ten-field error envelope, against spec 0.8.1. Prefer it when you have no Rust toolchain, when no wheel exists for your platform, for embedding, or when you want an implementation you can audit in pure Python. The honest tradeoff: pure mode runs at Python speed, not the native extension's — no speed claims are made either way. There is no global backend flag and no silent fallback: you choose a backend by choosing which module you import.

Since 0.8.1 the pure backend also ships as a real install artifact: the universal pure wheel `ktav-0.8.1-py3-none-any.whl` (same distribution name, same version) is published on PyPI alongside the native platform wheels. To install it, download/select the pure wheel (`py3-none-any`) from the release or PyPI files; `pip` prefers a matching platform wheel automatically when one exists. The pure wheel installs with no Rust toolchain, no compiler and no maturin, and provides exactly the `ktav.pure` backend — the native top-level functions then raise a clear `ImportError` pointing at `from ktav import pure`.

>>>>> lang=ru



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

>>>>> lang=zh


doc = pure.loads("server.port: 8080")
text = pure.dumps({"server": {"port": 8080}})
formatted = pure.format(text)
```

pure backend 提供完整的 parser、writer、formatter 和 Ktav errors，仅使用 Python 标准库。无需第三方包；不会加载 `_core` 或 WASM，也不会调用网络或 subprocess。必须显式选择；native 默认绝不会静默回退到 pure。

`tomli` 可作为旧版 Python 工具的 test/dev extras；它不是运行时依赖。

```python
from ktav import pure

config = pure.loads(open("config.ktav").read())
text = pure.dumps({"port": 8080})
formatted = pure.format(open("config.ktav").read())
```

纯模式实现完整的公开操作集 —— `loads`、`loads_strict`、`dumps`、`emit_canonical`、`dumps_force_strings`、`format`、`canonical_from_source`（以及 `load`/`dump`）—— 携带相同的十字段错误信封，遵循 spec 0.8.1。适合在以下情况选用：没有 Rust 工具链、没有匹配平台的 wheel、需要嵌入，或希望实现可以在纯 Python 中审计。诚实的取舍：纯模式以 Python 速度运行，而非原生扩展的速度 —— 双方都不做任何速度声明。没有全局 backend 开关，也没有静默回退：导入哪个模块，就用哪个 backend。

从 0.8.1 起，纯 backend 也以真实安装工件的形式发布：通用纯 wheel `ktav-0.8.1-py3-none-any.whl`（同一发行名、同一版本）与各原生平台 wheel 一起发布在 PyPI 上。安装时请从 release 或 PyPI 文件中下载/选择纯 wheel（`py3-none-any`）；当存在匹配的平台 wheel 时，`pip` 会自动优先选择。纯 wheel 的安装不需要 Rust 工具链、编译器或 maturin，并且只提供 `ktav.pure` 这一个 backend —— 此时原生的顶层函数会抛出明确的 `ImportError`，指向 `from ktav import pure`。

