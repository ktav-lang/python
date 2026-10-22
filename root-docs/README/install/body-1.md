>>>>> lang=en
## Install

```
pip install ktav
```

The default backend is native and includes our bundled Rust core in a matching platform wheel. No Python runtime dependency is required. Wheels target Python 3.9+ on supported platforms.

If no wheel matches, install from source: the native extension is compiled with Rust through maturin, so a Rust toolchain and Python development headers are needed. Source installation does not switch to pure mode.

### Pure Python

For a universal wheel, install the existing `py3-none-any` artifact explicitly:

```
pip install ./ktav-0.8.1-py3-none-any.whl
```

Then select the pure API directly:

```
from ktav import pure


>>>>> lang=ru
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


>>>>> lang=zh
## 安装

```
pip install ktav
```

默认 backend 是 native；匹配的平台 wheel 内含我们打包的 Rust 核心，无需 Python 运行时依赖。受支持的平台 wheel 面向 Python 3.9+。

若没有匹配的 wheel，从源码安装会通过 maturin 使用 Rust 编译 native 扩展，因此需要 Rust 工具链和 Python 开发头文件。源码安装不会切换到 pure 模式。

### 纯 Python

如需通用 wheel，请显式安装现有的 `py3-none-any` 工件：

```
pip install ./ktav-0.8.1-py3-none-any.whl
```

然后显式选择 pure API：

```
from ktav import pure


