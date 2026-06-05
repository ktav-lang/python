<!-- TODO: sync with README.md — this translation is a stub awaiting a
     Simplified Chinese review. The structure mirrors the English file;
     translate in-place and remove this comment once the content is
     ready. -->

# ktav (Python)

[![PyPI](https://img.shields.io/pypi/v/ktav?style=flat-square&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/ktav/)
[![CI](https://img.shields.io/github/actions/workflow/status/ktav-lang/python/CI.yml?style=flat-square&logo=github&label=CI)](https://github.com/ktav-lang/python/actions)
![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue?style=flat-square)
[![Playground](https://img.shields.io/badge/playground-try%20online-7c3aed?style=flat-square&logo=rocket&logoColor=white)](https://ktav-lang.github.io/)

> [Ktav](https://github.com/ktav-lang/spec) 的 Python 绑定 —— 一种朴素的
> 配置格式。JSON 形状,无引号,无逗号,以点号串联的嵌套键。底层由 Rust 驱动。

**Languages:** [English](README.md) · [Русский](README.ru.md) · **简体中文**

**演练场：** 在浏览器中互转 JSON / YAML / TOML / INI ⇄ Ktav — **[ktav-lang.github.io](https://ktav-lang.github.io/)**。

**规范:** 本包实现 **Ktav**。格式独立版本化维护,参见
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
port:    int = cfg["port"]
ratio: float = cfg["ratio"]
tls:    bool = cfg["tls"]
tags: list[str] = cfg["tags"]
db_host:    str = cfg["db"]["host"]
db_timeout: int = cfg["db"]["timeout"]
```

### 遍历 —— 按运行时类型分派

```python
for k, v in cfg.items():
    if v is None:              kind = "null"
    elif isinstance(v, bool):  kind = f"bool={v}"   # bool 先判断 —— True 也是 int!
    elif isinstance(v, int):   kind = f"int={v}"
    elif isinstance(v, float): kind = f"float={v}"
    elif isinstance(v, str):   kind = f"str={v!r}"
    elif isinstance(v, list):  kind = f"array({len(v)})"
    elif isinstance(v, dict):  kind = f"object({len(v)})"
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
```

完整可运行示例:[`examples/basic.py`](examples/basic.py)。

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
| 裸整数             | `int`    |
| 裸小数             | `float`  |
| 其他标量           | `str`    |
| `[ ... ]`          | `list`   |
| `{ ... }`          | `dict`   |

Ktav 按**词法形式**为数字定型 —— 裸 `port: 8080` 是 `int`,
`ratio: 0.5` 是 `float`,而任何并非裸数字的内容都保持为 `str`。
要让看起来像数字的值保持为字符串,用 `::` 强制(`zip:: 01007`)。

## 键的转义

自 spec 0.6.0 起,键段内的字面量 `.` 或 `:` 通过反斜杠书写:

```text
a\.b: v        # 键是单个段 "a.b"        -> {"a.b": "v"}
a\:b: v        # 键中包含冒号            -> {"a:b": "v"}
x.y\.z: v      # 只按第一个点切分        -> {"x": {"y.z": "v"}}
```

键中的字面量反斜杠写作 `\\`。

## 其他 Ktav 实现

- [`spec`](https://github.com/ktav-lang/spec) —— 规范 + 一致性测试套件
- [`rust`](https://github.com/ktav-lang/rust) —— 参考 Rust crate(`cargo add ktav`);本 Python 绑定是其上的薄 PyO3 包装
- [`csharp`](https://github.com/ktav-lang/csharp) —— C# / .NET(`dotnet add package Ktav`)
- [`golang`](https://github.com/ktav-lang/golang) —— Go(`go get github.com/ktav-lang/golang`)
- [`java`](https://github.com/ktav-lang/java) —— Java / JVM(`io.github.ktav-lang:ktav`,Maven Central)
- [`js`](https://github.com/ktav-lang/js) —— JS / TS(`npm install @ktav-lang/ktav`)
- [`php`](https://github.com/ktav-lang/php) —— PHP(`composer require ktav-lang/ktav`)

## 支持本项目

作者有许多构想,可能对全球 IT 广泛有益——不局限于 Ktav。实现这些
构想需要资金支持。如果您愿意提供帮助,请联系
**phpcraftdream@gmail.com**。

## 许可证

MIT OR Apache-2.0。详见 [LICENSE-MIT](LICENSE-MIT) 和 [LICENSE-APACHE](LICENSE-APACHE)。
