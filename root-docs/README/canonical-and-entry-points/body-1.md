>>>>> lang=en
Unlike the JavaScript bindings, `canonical_from_source` buys you no extra
numeric fidelity here — Python distinguishes `int` from `float`, so the
Ktav Integer/Float distinction survives `loads`, and
`emit_canonical(loads(src))` produces the same bytes as
`canonical_from_source(src)`. Both spell a float by the canonical rule
(§ 5.9.8) rather than by copying the source, so `1.23456789012345678901`
becomes `1.2345678901234567` down either path.

`ktav.dumps_force_strings(obj)` renders like `dumps` but coerces every
leaf scalar — integer, float, bool, null — to a String via the raw `::`
marker. Compounds keep their structure.

Four entry points mirror the standard library `json` module:

| Function              | Purpose                                      |
|-----------------------|----------------------------------------------|
| `ktav.loads(s)`       | Parse a Ktav string (or UTF-8 `bytes`).      |
| `ktav.dumps(obj)`     | Serialise a native Python value.             |
| `ktav.load(fp)`       | Parse from a file-like object.               |
| `ktav.dump(obj, fp)`  | Serialise to a file-like object.             |

`load` / `dump` accept both text-mode and binary-mode files.

For validation at trust boundaries, `ktav.loads_strict(s)` applies the
specification's canonical-scalar rules and raises `KtavDecodeError` for a
lossy scalar spelling. Canonical writer forms such as `1e-3` and `1e10` are
accepted and produce the same native values as `loads`.

>>>>> lang=ru
В отличие от биндингов для JavaScript, `canonical_from_source` не даёт
здесь дополнительной численной точности: Python различает `int` и
`float`, поэтому различие Integer/Float из Ktav переживает `loads`, и
`emit_canonical(loads(src))` выдаёт те же байты, что и
`canonical_from_source(src)`. Оба пишут float по каноническому правилу
(§ 5.9.8), а не копируют исходную запись, поэтому
`1.23456789012345678901` превращается в `1.2345678901234567` любым из
путей.

`ktav.dumps_force_strings(obj)` выводит как `dumps`, но приводит каждый
leaf-скаляр — integer, float, bool, null — к String через сырой маркер
`::`. Составные значения сохраняют структуру.

Четыре точки входа повторяют стандартный модуль `json`:

| Функция              | Назначение                                    |
|-----------------------|----------------------------------------------|
| `ktav.loads(s)`      | Разобрать строку Ktav (или UTF-8 `bytes`).    |
| `ktav.dumps(obj)`    | Сериализовать нативное значение Python.       |
| `ktav.load(fp)`      | Разобрать из файло-подобного объекта.         |
| `ktav.dump(obj, fp)` | Сериализовать в файло-подобный объект.        |

`load` / `dump` принимают файлы как в текстовом, так и в бинарном режиме.

Для проверки на границах доверия `ktav.loads_strict(s)` применяет
канонические правила спецификации для скаляров и выбрасывает
`KtavDecodeError` при потере записи скаляра. Формы canonical writer,
например `1e-3` и `1e10`, принимаются и дают те же нативные значения,
что и `loads`.

>>>>> lang=zh
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

