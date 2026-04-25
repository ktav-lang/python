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

### 解析 —— 直接从 dict 按类型读取字段

```python
import ktav

src = """
service: web
port:i 8080
ratio:f 0.75
tls: true
tags: [
    prod
    eu-west-1
]
db.host: primary.internal
db.timeout:i 30
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
