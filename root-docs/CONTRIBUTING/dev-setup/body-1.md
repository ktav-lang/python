>>>>> lang=en
## Dev setup

You need:

- Python **3.9+** (any version you plan to test against).
- A Rust toolchain via [`rustup`](https://rustup.rs/). MSRV: **1.70**.
- [`maturin`](https://www.maturin.rs/) plus the test tooling:

```
pip install -e ".[dev]"
```

Layout during development — these bindings resolve the `ktav` Rust
crate via a `path = "../rust"` dependency in `Cargo.toml`. Clone the
sibling repo next to this one:

```
ktav-lang/
├── python/   ← this repo
├── rust/     ← sibling Rust crate
└── spec/     ← conformance fixtures (optional but recommended)
```

Once `ktav` is published to crates.io, the path dependency goes away
and only the `version = "0.1"` requirement stays. See the comment on
that line in `Cargo.toml`.

>>>>> lang=ru
## Настройка окружения

Нужно:

- Python **3.9+** (любая версия, под которую тестируете).
- Rust-тулчейн через [`rustup`](https://rustup.rs/). MSRV: **1.70**.
- [`maturin`](https://www.maturin.rs/) и тестовый инструментарий:

```
pip install -e ".[dev]"
```

Раскладка во время разработки — эти биндинги разрешают Rust-крейт
`ktav` через зависимость `path = "../rust"` в `Cargo.toml`. Клонируйте
соседний репозиторий рядом с этим:

```
ktav-lang/
├── python/   ← this repo
├── rust/     ← sibling Rust crate
└── spec/     ← conformance fixtures (optional but recommended)
```

Когда `ktav` будет опубликован на crates.io, path-зависимость уйдёт, и
останется только требование `version = "0.1"`. См. комментарий на той
строке в `Cargo.toml`.

>>>>> lang=zh
## 开发环境搭建

你需要：

- Python **3.9+**（任何你打算测试的版本）。
- 通过 [`rustup`](https://rustup.rs/) 安装的 Rust 工具链。MSRV：**1.70**。
- [`maturin`](https://www.maturin.rs/) 以及测试工具：

```
pip install -e ".[dev]"
```

开发期间的目录布局 —— 这些绑定通过 `Cargo.toml` 中的
`path = "../rust"` 依赖来解析 `ktav` Rust crate。请把相邻仓库克隆到
其旁边：

```
ktav-lang/
├── python/   ← this repo
├── rust/     ← sibling Rust crate
└── spec/     ← conformance fixtures (optional but recommended)
```

一旦 `ktav` 发布到 crates.io，path 依赖就会消失，只剩下
`version = "0.1"` 要求。见 `Cargo.toml` 中该行的注释。

