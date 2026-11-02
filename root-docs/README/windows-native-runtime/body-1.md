>>>>> lang=en
## Windows native runtime

The prepared 0.8.1 Windows wheels use the actual GNU/LLVM targets `x86_64-pc-windows-gnullvm` and `aarch64-pc-windows-gnullvm`, retaining the standard `win_amd64` and `win_arm64` wheel tags. Installing a matching wheel does not need Rust, LLVM or C build tools. The extension links the installed CPython stable ABI and Windows system/UCRT APIs; the interpreter and its own runtime dependencies are not bundled. Full original Cargo, Rust compiler, MinGW/libunwind and CPython import-interface source/licence materials are retained in `ktav/_third_party/NOTICE.json` inside the wheel. Preserve that resource when redistributing the package. This describes the prepared candidate, not a repair of historical published wheels.

>>>>> lang=ru
## Нативное расширение Windows

Подготовленные Windows wheels 0.8.1 используют actual GNU/LLVM targets `x86_64-pc-windows-gnullvm` и `aarch64-pc-windows-gnullvm`, сохраняя стандартные wheel tags `win_amd64` и `win_arm64`. Для установки подходящего wheel не нужны Rust, LLVM или C build tools. Расширение связывается с установленным stable ABI CPython и системными Windows/UCRT API; интерпретатор и его собственные runtime-зависимости в wheel не включены. Полные original Cargo, Rust compiler, MinGW/libunwind и CPython import-interface source/licence materials сохранены в `ktav/_third_party/NOTICE.json` внутри wheel. Сохраняйте этот ресурс при распространении пакета. Это описание подготовленного candidate, а не исправление исторических опубликованных wheels.

>>>>> lang=zh
## Windows 原生运行时

准备中的 0.8.1 Windows wheel 使用实际的 GNU/LLVM 目标 `x86_64-pc-windows-gnullvm` 和 `aarch64-pc-windows-gnullvm`，同时保留标准的 `win_amd64`、`win_arm64` wheel 标签。安装匹配的 wheel 无需 Rust、LLVM 或 C 构建工具。扩展链接已安装的 CPython 稳定 ABI 和 Windows 系统/UCRT API；wheel 不包含解释器及其自身的运行时依赖。完整的 Cargo、Rust 编译器、MinGW/libunwind 和 CPython 导入接口原始源码及许可证材料保留在 wheel 内的 `ktav/_third_party/NOTICE.json` 中。重新分发包时应保留该资源。此说明仅适用于准备中的候选发行包，不表示已修复历史发布的 wheel。

