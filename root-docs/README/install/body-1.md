>>>>> lang=en
## Install

```
pip install ktav
```

Wheels are published for every major platform and every supported
Python version:

- **Linux** (manylinux + musllinux) — `x86_64`, `aarch64`
- **macOS** — `x86_64`, `arm64` (Apple Silicon)
- **Windows** — `x64`, `arm64`

Python **3.9+** is required. The wheels target the stable ABI
(`abi3-py39`), so a single wheel per platform serves every supported
CPython release.

If no prebuilt wheel matches your platform, `pip` falls back to the
source distribution and compiles it locally — you need a Rust toolchain
(`rustup`) and the Python development headers.

### Without the compiled extension

`import ktav` no longer requires the native extension. A complete
pure-Python backend ships in the same package: `from ktav import pure`
works anywhere Python 3.9+ runs — no Rust toolchain, no wheel for your
platform, nothing compiled, downloaded or spawned:

>>>>> lang=ru
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

### Без скомпилированного расширения

`import ktav` больше не требует нативного расширения. В тот же пакет
входит полноценный чистый backend на Python: `from ktav import pure`
работает везде, где есть Python 3.9+ — без Rust toolchain, без wheel
под вашу платформу, без компиляции, загрузок и subprocess:

>>>>> lang=zh
## 安装

```
pip install ktav
```

所有主流平台、所有受支持的 Python 版本都有预编译 wheel 发布：

- **Linux** (manylinux + musllinux) — `x86_64`, `aarch64`
- **macOS** — `x86_64`, `arm64` (Apple Silicon)
- **Windows** — `x64`, `arm64`

要求 Python **3.9+**。Wheel 针对稳定 ABI (`abi3-py39`) 构建，因此每个
平台一个 wheel 即可服务所有受支持的 CPython 版本。

如果没有匹配的预编译 wheel，`pip` 会回退到源码分发包并在本地编译 ——
这需要 Rust 工具链 (`rustup`) 和 Python 开发头文件。

### 不使用编译扩展

`import ktav` 不再要求原生扩展。同一个包内附带了完整的纯 Python
backend：`from ktav import pure` 在任何能运行 Python 3.9+ 的地方都能
工作 —— 不需要 Rust 工具链，不需要匹配平台的 wheel，不编译、不下载、
不启动子进程：

