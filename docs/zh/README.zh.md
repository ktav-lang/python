# ktav (Python)

[![PyPI](https://img.shields.io/pypi/v/ktav?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/ktav/)
[![CI](https://img.shields.io/github/actions/workflow/status/ktav-lang/python/CI.yml?style=flat-square&logo=github&label=CI)](https://github.com/ktav-lang/python/actions)
![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue?style=flat-square)
[![Playground](https://img.shields.io/badge/playground-try%20online-7c3aed?style=flat-square&logo=rocket&logoColor=white)](https://ktav-lang.github.io/)

> [Ktav](https://github.com/ktav-lang/spec) 的 Python 绑定 —— 一种朴素的
> 配置格式。JSON 形状，无需强制引号，无逗号，以点号串联的嵌套键。底层由
> Rust 驱动。

**Languages:** [English](../../README.md) · [Русский](../ru/README.ru.md) · **简体中文**

**演练场：** 在浏览器中互转 JSON / YAML / TOML / INI ⇄ Ktav — **[ktav-lang.github.io](https://ktav-lang.github.io/)**。

**规范：** 本包实现 **Ktav**。格式的版本化与维护独立于本包 —— 规范正文
见 [`ktav-lang/spec`](https://github.com/ktav-lang/spec)。

---

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

## 快速上手

### 解析 —— 直接从 dict 按类型读取字段

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
port: int = cfg["port"]
ratio: float = cfg["ratio"]
tls: bool = cfg["tls"]
tags: list[str] = cfg["tags"]
db_host: str = cfg["db"]["host"]
db_timeout: int = cfg["db"]["timeout"]
```

### 遍历 —— 按运行时类型分派

```python
for k, v in cfg.items():
    if v is None:
        kind = "null"
    elif isinstance(v, bool):
        kind = f"bool={v}"  # bool first — True is also an int!
    elif isinstance(v, int):
        kind = f"int={v}"
    elif isinstance(v, float):
        kind = f"float={v}"
    elif isinstance(v, str):
        kind = f"str={v!r}"
    elif isinstance(v, list):
        kind = f"array({len(v)})"
    elif isinstance(v, dict):
        kind = f"object({len(v)})"
    print(f"{k} -> {kind}")
```

### 构建并渲染 —— 用代码搭建文档

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
# name: frontend
# port: 8443
# tls: true
# ratio: 0.95
# upstreams: [
#     { host: a.example  port: 1080 }
#     { host: b.example  port: 1080 }
# ]
# notes: null
```

完整可运行示例见 [`examples/basic.py`](../../examples/basic.py)。

### 格式化 —— 规范整个文件，同时保留注释

```python
import ktav

print(ktav.format(open("config.ktav").read()))
```

`ktav.format` 以规范形式（§ 5.9）重写文档，同时逐字保留每一条注释。
连续空行折叠为一行，括号内侧的空白填充被丢弃 —— 因此格式化是一个不动
点，可以放心地放进 pre-commit 钩子。键序永不改变。

有三个函数都会产生规范输出，它们的区别在于接受什么、保留什么：

| | 输入 | 注释 | 空行 |
| --- | --- | --- | --- |
| `ktav.format(src)` | 源文本 | **保留** | **保留**（连续空行折叠为一行） |
| `ktav.canonical_from_source(src)` | 源文本 | 丢弃 | 丢弃 |
| `ktav.emit_canonical(obj)` | Python 对象 | 无注释可留 | 无空行可留 |

按手上握着什么来选：有对象时用 `emit_canonical`，有文本且不想在中间
构造出 Python 值时用 `canonical_from_source`，想让文档自身的注释与分组
存活下来时用 `format`。

与 JavaScript 绑定不同，`canonical_from_source` 在这里不会带来额外的
数值精度 —— Python 区分 `int` 与 `float`，因此 Ktav 的 Integer/Float
之分在 `loads` 之后依然保留，并且 `emit_canonical(loads(src))` 产生的
字节与 `canonical_from_source(src)` 完全相同。两条路径都按规范规则
（§ 5.9.8）拼写 float，而不是照抄源文本，因此
`1.23456789012345678901` 在任一路径下都会变成 `1.2345678901234567`。

`ktav.dumps_force_strings(obj)` 的渲染方式与 `dumps` 相同，但会把每个
叶子标量 —— integer、float、bool、null —— 通过原始标记 `::` 强制为
String。复合值保持其结构。

四个入口函数镜像标准库 `json` 模块：

| 函数                  | 用途                                          |
|-----------------------|----------------------------------------------|
| `ktav.loads(s)`      | 解析 Ktav 字符串（或 UTF-8 `bytes`）。        |
| `ktav.dumps(obj)`    | 序列化原生 Python 值。                        |
| `ktav.load(fp)`      | 从类文件对象解析。                            |
| `ktav.dump(obj, fp)` | 序列化到类文件对象。                          |

`load` / `dump` 同时接受文本模式与二进制模式的文件。

要在信任边界上校验输入时，`ktav.loads_strict(s)` 会应用规范中的
canonical scalar 规则，并在遇到会造成信息损失的标量写法时抛出
`KtavDecodeError`。canonical writer 形式（如 `1e-3` 和 `1e10`）会被
接受，并产生与 `loads` 相同的原生值。

## 类型映射

| Ktav                 | Python   |
|----------------------|----------|
| `null`               | `None`   |
| `true` / `false`     | `bool`   |
| 裸整数               | `int`    |
| 裸小数               | `float`  |
| 其他标量             | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav 按**词法形式**为数字定型 —— 裸写的 `port: 8080` 是 `int`，
`ratio: 0.5` 是 `float`，而任何并非裸数字的内容都保持为 `str`。若要
让看起来像数字的值保持为字符串，用 `::` 强制（`zip:: 01007`）。

`dict` 保留插入顺序（Python 3.7+ 的保证），与 Ktav 的有序对象语义一致。

序列化是它的逆运算：

- Python `int` → 裸整数（包括任意精度的大整数）。
- Python `float` → 裸小数（小数点始终存在；`NaN` / `±Infinity` 会被
  拒绝 —— Ktav 不表示它们）。
- Python `tuple` 可作为数组接受，与 `list` 对称。
- `dict` 中的非 `str` 键会引发 `KtavEncodeError`。

## 键的转义

自 spec 0.6.4 起，键段内的字面量 `.` 或 `:` 通过反斜杠书写：

```text
a\.b: v
a\:b: v
x.y\.z: v
a."b.c".d: v
"\u0041": v
```

键中的字面量反斜杠写作 `\\`。自 spec 0.7 起,还可以用双引号、单引号或
反引号括住整个键段。引号只用于键段,不用于值;`\uXXXX` 解码 Unicode 码点。

## 错误

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

# Catching the base class catches either.
try:
    ktav.loads("a: 1\na: 2")
except ktav.KtavError:
    ...
```

| 异常                | 抛出者            | 基类                |
|---------------------|-------------------|---------------------|
| `KtavError`         | （基类）          | `Exception`         |
| `KtavDecodeError`   | `loads` / `load`  | `KtavError`         |
| `KtavEncodeError`   | `dumps` / `dump`  | `KtavError`         |

自 0.7.1 起，每个抛出的异常实例还以属性形式携带结构化错误信封：`error`、
`reason`、`line`、`line_text`、`span`、`path`、`body`、`canonical`、
`spec_section`。缺失的信息是 `None`，而不是缺少属性。`span` 是
`{"start": …, "end": …}`，即 UTF-8 源文本中的字节偏移；`path` 是精确
解码后的键段列表（字面名为 `a.b` 的键是一个段，绝不会被切开）。
`str(e)` 仍然是人类可读的消息 —— 原始信封不会被用来取代它。

`e.message` 以属性形式携带同一段文本，即 **`str(e) == e.message`**。
它在这里是有意的冗余：本绑定的 `str(e)` 一直使用核心自身的渲染文本，
而这个属性存在的意义，是让信封在 Python 中拥有与其他任何语言相同的
十个字段 —— 在那些语言里，`message` 是取到该文本的唯一途径。请直接
使用它，而不要用 `error`、`line` 和 `body` 重新拼出一句话：重新拼装的
消息在各绑定之间并不一致，而这一个是一致的。

## 哲学

Ktav 刻意保持小巧。它的五条设计原则
（出自 [`spec/CONTRIBUTING.md`](https://github.com/ktav-lang/spec/blob/main/CONTRIBUTING.md)）：

1. **局部性** —— 一行的含义不取决于另一行。
2. **一句话** —— 任何新规则都能写进规范的一句话里。
3. **对空白不敏感**（换行除外）。
4. **没有魔法类型** —— 格式从不判定 `"8080"` 表示数字。
5. **显式优于聪明** —— `::` 故意保持冗长。

Python 绑定遵守这一点：不做任何模式推断、不做自动类型转换、不提供默认
值。如果需要类型，请在边界处用自己的工具 —— `pydantic`、`dataclasses`、
`attrs` —— 对本库返回的原生 Python 结构进行。

## 其他 Ktav 实现

- [`spec`](https://github.com/ktav-lang/spec) —— 规范 + 一致性测试套件
- [`rust`](https://github.com/ktav-lang/rust) —— 参考 Rust crate (`cargo add ktav`)；本 Python 绑定是包在其外的薄 PyO3 包装
- [`csharp`](https://github.com/ktav-lang/csharp) —— C# / .NET (`dotnet add package Ktav`)
- [`golang`](https://github.com/ktav-lang/golang) —— Go (`go get github.com/ktav-lang/golang`)
- [`java`](https://github.com/ktav-lang/java) —— Java / JVM（`io.github.ktav-lang:ktav`，Maven Central）
- [`js`](https://github.com/ktav-lang/js) —— JS / TS (`npm install @ktav-lang/ktav`)
- [`php`](https://github.com/ktav-lang/php) —— PHP (`composer require ktav-lang/ktav`)

## 版本管理

本包遵循 [Semantic Versioning](https://semver.org/)，并采用 1.0 之前的
约定：MINOR 版本号提升即为破坏性变更。包版本与 `ktav` crate 的版本同步
变动。`ktav.__spec_version__` 报告本绑定所支持的 Ktav 格式版本。

## 开发

开发环境搭建、测试布局与贡献流程见 [CONTRIBUTING.md](../CONTRIBUTING.md)
（以及 [CONTRIBUTING.zh.md](CONTRIBUTING.zh.md)）。

## 支持本项目

作者有许多构想，可能对全球 IT 广泛有益 —— 并不局限于 Ktav。实现这些
构想需要资金支持。如果您愿意提供帮助，请联系 **phpcraftdream@gmail.com**。

## 许可证

MIT OR Apache-2.0。详见 [LICENSE-MIT](../../LICENSE-MIT) 和 [LICENSE-APACHE](../../LICENSE-APACHE)。
