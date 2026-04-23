<!-- TODO: sync with CONTRIBUTING.md — this translation is a stub
     awaiting a Simplified Chinese review. Translate in-place and remove
     this comment once the content is ready. -->

# 为 ktav (Python) 贡献代码

**Languages:** [English](CONTRIBUTING.md) · [Русский](CONTRIBUTING.ru.md) · **简体中文**

## 核心规则

### 1. 每个 bug 修复都伴随一个回归测试

在修复 bug **之前**,先写一个能复现该 bug 的测试 —— 该测试**必须在
`main` 上失败**,并在修复后通过。测试与修复放在同一个 PR。

测试文件位于 `tests/`:

| 文件                         | 范围                                       |
|------------------------------|--------------------------------------------|
| `test_loads.py`              | 解析器行为。                               |
| `test_dumps.py`              | 序列化器行为。                             |
| `test_roundtrip.py`          | `loads(dumps(x)) == x`。                   |
| `test_errors.py`             | 异常层次与传播。                           |
| `test_load_dump.py`          | 类文件对象包装。                           |
| `test_module.py`             | 模块级导出、版本字符串。                   |
| `test_conformance.py`        | 跨语言规范一致性测试。                     |

### 2. 不要在绑定层重新发明格式

Python 绑定是**有意**做成薄包装。解析器 / 格式行为属于 Rust crate
([`ktav-lang/rust`](https://github.com/ktav-lang/rust)) —— 在那里修改
一次会同时更新所有语言绑定。只有 **Python 特有的人体工学**
(类文件包装、异常类型、类型存根) 才属于本仓库。

如果你的改动需要改格式,请先去
[`ktav-lang/spec`](https://github.com/ktav-lang/spec) 发起讨论。

## 开发环境

你需要:

- Python **3.9+** (任何你打算测试的版本)。
- 通过 [`rustup`](https://rustup.rs/) 安装的 Rust 工具链。MSRV: **1.70**。
- [`maturin`](https://www.maturin.rs/) 及测试工具:

```
pip install -e ".[dev]"
```

### 构建与测试

```
make dev       # debug 构建
make install   # release 构建
make test
make lint
make all       # 全部运行
```

## 语言政策

本仓库遵循组织级三语种政策 (EN / RU / ZH)。每份 prose 文档都有三种
并行版本 —— 详见
[`ktav-lang/.github/AGENTS.md`](https://github.com/ktav-lang/.github/blob/main/AGENTS.md)。
