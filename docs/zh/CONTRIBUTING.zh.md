# 为 ktav (Python) 贡献代码

**Languages:** [English](../CONTRIBUTING.md) · [Русский](../ru/CONTRIBUTING.ru.md) · **简体中文**

## 核心规则

### 1. 每个 bug 修复都伴随一个回归测试

发现 bug 时，**在修复之前**，先写一个能复现该 bug 的测试 ——
它在 `main` 上**必须失败**，并在修复后通过。测试与修复放在同一个 PR。

测试位于 `tests/`：

| 文件 | 范围 |
|------|------|
| `test_loads.py` | 解析器行为。 |
| `test_dumps.py` | 序列化器行为。 |
| `test_roundtrip.py` | `loads(dumps(x)) == x`。 |
| `test_errors.py` | 异常分类与传播。 |
| `test_load_dump.py` | 类文件对象包装。 |
| `test_module.py` | 模块级导出、版本字符串。 |
| `test_conformance.py` | 跨语言规范一致性测试。 |

### 2. 不要在绑定层重新发明格式

这些 Python 绑定**有意**做成薄包装。解析器 / 格式行为属于 Rust crate
([`ktav-lang/rust`](https://github.com/ktav-lang/rust)) ——
在那里修改一次即可同时更新所有语言绑定。只有 **Python 特有的人体工学**
（类文件包装、异常类型、类型存根）才属于本仓库。

如果你的改动需要修改格式，请先去
[`ktav-lang/spec`](https://github.com/ktav-lang/spec) 发起讨论。

### 3. 公开 API 的变更注明兼容性

如果你改动 `ktav` 或 `ktav._core` 导出的任何内容，请在 PR 描述中说明它
属于：

- **semver 兼容**（新增、更宽松的类型、文档改动）；或
- **semver 破坏**（重命名 / 移除、签名变更、类型收紧）——
  这种情况下版本 bump 会落在下一个 MINOR，毕竟我们还在 1.0 之前。

在同一个 PR 中更新 `root-docs/CHANGELOG/` 下的 CHANGELOG 源单元
(全部三个 `>>>>> lang=` 块)并重新生成产物。

### 4. 一个概念一个提交

提交应当原子化：bug 修复与其测试放在一起，功能与其测试放在一起，
重命名单独一次提交，重构单独一次提交。`git log --oneline`
读起来应像变更日志。不要给提交消息加 `feat:` / `fix:` 前缀 ——
这里不用 conventional commits。

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

### 测试

```
make test                          # full suite
pytest -v -k multiline             # filter by name
pytest -v tests/parse/test_loads.py  # single file
```

`test_conformance.py` 模块运行来自 `ktav-lang/spec` 的跨语言夹具套件，
路径硬编码为 `<repo>/spec/versions/0.1/tests`（git submodule `spec`）。
当 submodule 未填充时（例如仅 sdist 的检出），一致性测试会**跳过**而非
失败。

### Lint + typecheck

```
make lint         # ruff check + ruff format --check
make typecheck    # mypy --strict
make rust-lint    # cargo fmt --check + cargo clippy -D warnings
make all          # lint + typecheck + rust-lint + test
```

CI 运行相同的命令；推送前请在本地运行 `make all`。

### Pre-commit

```
pre-commit install
pre-commit run --all-files
```

这会把 ruff、mypy、rustfmt、clippy 以及标准 whitespace / EOL 钩子
接入 `git commit`。

## 理念

Ktav 的座右铭：**「做配置的朋友，而不是审查者」**。在提出新的
Python 特有功能之前，请问：

- 这是否会给读者增加一个必须记住的新规则？
- 它能否放在用户代码中，而不是库中？
- 它是否会侵蚀「类型无魔法」原则？

新规则代价高昂。拒绝一切不明确属于这里的东西。

## 语言政策

本仓库参与全组织范围的三语言政策（EN / RU / ZH）。每个 prose 文件都有
三个并行版本 —— 命名约定以及「一次提交更新全部三个版本」的规则见
[`ktav-lang/.github/AGENTS.md`](https://github.com/ktav-lang/.github/blob/main/AGENTS.md)。

如果你不掌握其中某门语言，也请用你掌握的语言提交 PR，并在未翻译的版本
顶部标注 `<!-- TODO: sync with <name>.md -->`，维护者或社区贡献者会在
合并前补齐缺口。

### 贡献许可

除非你明确声明相反，凡是你为本项目有意提交的贡献，按 Apache-2.0
许可证之定义，均以 **MIT OR Apache-2.0** 双重许可，
不附加任何额外条款或条件。
