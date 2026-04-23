<!-- TODO: sync with README.md — this translation is a stub awaiting a
     Simplified Chinese review. The structure mirrors the English file;
     translate in-place and remove this comment once the content is
     ready. -->

# ktav (Python)

> [Ktav](https://github.com/ktav-lang/spec) 的 Python 绑定 —— 一种朴素的
> 配置格式。JSON 形状,无引号,无逗号,以点号串联的嵌套键。底层由 Rust 驱动。

**Languages:** [English](README.md) · [Русский](README.ru.md) · **简体中文**

**规范:** 本包实现 **Ktav 0.1**。格式独立版本化维护,参见
[`ktav-lang/spec`](https://github.com/ktav-lang/spec) 的正式文档。

---

## 安装

```
pip install ktav
```

针对所有主流平台和 Python 版本都发布了预编译 wheel:

- **Linux** (manylinux + musllinux) — `x86_64`, `aarch64`
- **macOS** — `x86_64`, `arm64` (Apple Silicon)
- **Windows** — `x64`, `arm64`

要求 Python **3.9+**。Wheel 使用稳定 ABI (`abi3-py39`),每个平台一个
wheel 即可覆盖所有受支持的 CPython 版本。

## 快速开始

```python
import ktav

text = """
port:i 8080

upstreams: [
    {
        host: a.example
        port:i 1080
    }
]
"""

cfg = ktav.loads(text)
back = ktav.dumps(cfg)
assert ktav.loads(back) == cfg
```

四个入口函数对应标准库 `json` 模块:

- `ktav.loads(s)` — 解析 Ktav 字符串
- `ktav.dumps(obj)` — 序列化为 Ktav 字符串
- `ktav.load(fp)` — 从类文件对象解析
- `ktav.dump(obj, fp)` — 写入类文件对象

## 类型映射

| Ktav               | Python   |
|--------------------|----------|
| `null`             | `None`   |
| `true` / `false`   | `bool`   |
| `:i <digits>`      | `int`    |
| `:f <number>`      | `float`  |
| 裸标量             | `str`    |
| `[ ... ]`          | `list`   |
| `{ ... }`          | `dict`   |

Ktav 坚持 **"不耍小聪明"** —— 裸 `port: 8080` 在解析层面仍然是字符串。
需要数字时,请使用类型标记 `:i` / `:f`。

## 相关项目

- [`ktav-lang/spec`](https://github.com/ktav-lang/spec)
- [`ktav-lang/rust`](https://github.com/ktav-lang/rust)

## 支持本项目

作者有许多构想,可能对全球 IT 广泛有益——不局限于 Ktav。实现这些
构想需要资金支持。如果您愿意提供帮助,请联系
**phpcraftdream@gmail.com**。

## 许可证

MIT。详见 [LICENSE](LICENSE)。
