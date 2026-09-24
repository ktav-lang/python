>>>>> lang=en
### Build

```
make dev          # debug build (fast incremental)
make install      # release build (realistic perf)
```

Or directly:

```
maturin develop
maturin develop --release
```

`maturin develop` compiles the Rust extension and installs it into the
currently-active Python environment — run tests from the same env.

>>>>> lang=ru
### Сборка

```
make dev          # debug build (fast incremental)
make install      # release build (realistic perf)
```

Или напрямую:

```
maturin develop
maturin develop --release
```

`maturin develop` компилирует Rust-расширение и устанавливает его в
текущее активное Python-окружение — запускайте тесты из того же
окружения.

>>>>> lang=zh
### 构建

```
make dev          # debug build (fast incremental)
make install      # release build (realistic perf)
```

或者直接用：

```
maturin develop
maturin develop --release
```

`maturin develop` 会编译 Rust 扩展并将其安装到当前活动的 Python 环境 ——
请从同一环境运行测试。

