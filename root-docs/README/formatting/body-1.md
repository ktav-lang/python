>>>>> lang=en
### Format — normalise a file, keep the comments

```python
import ktav

print(ktav.format(open("config.ktav").read()))
```

`ktav.format` rewrites a document in canonical form (spec § 5.9) while
preserving every comment verbatim. Blank-line runs collapse to one and
blank padding inside brackets is dropped, so formatting is a fixed
point — safe to run in a pre-commit hook. Key order is never changed.

Three functions produce canonical output and they differ in what they
accept and what they keep:

| | input | comments | blank lines |
| --- | --- | --- | --- |
| `ktav.format(src)` | source text | **kept** | **kept** (runs collapse to one) |
| `ktav.canonical_from_source(src)` | source text | dropped | dropped |
| `ktav.emit_canonical(obj)` | a Python object | none to keep | none to keep |

Pick by what you are holding: `emit_canonical` when you have an object,
`canonical_from_source` when you have text and want no Python value
built in between, `format` when you want the document's own comments and
grouping to survive.

>>>>> lang=ru
### Форматирование — нормализуем файл, сохраняя комментарии

```python
import ktav

print(ktav.format(open("config.ktav").read()))
```

`ktav.format` переписывает документ в канонической форме (§ 5.9),
сохраняя каждый комментарий дословно. Серии пустых строк схлопываются в
одну, пустой отступ внутри скобок выбрасывается — поэтому форматирование
является неподвижной точкой и его безопасно ставить в pre-commit хук.
Порядок ключей не меняется никогда.

Канонический вывод дают три функции, и они различаются тем, что
принимают и что сохраняют:

| | вход | комментарии | пустые строки |
| --- | --- | --- | --- |
| `ktav.format(src)` | исходный текст | **сохраняются** | **сохраняются** (серия схлопывается в одну) |
| `ktav.canonical_from_source(src)` | исходный текст | отбрасываются | отбрасываются |
| `ktav.emit_canonical(obj)` | объект Python | сохранять нечего | сохранять нечего |

Выбирайте по тому, что у вас в руках: `emit_canonical` — когда объект,
`canonical_from_source` — когда текст и не нужно строить промежуточное
значение Python, `format` — когда нужно сохранить собственные
комментарии и группировку документа.

>>>>> lang=zh
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

