>>>>> lang=en
### Source edits — `edit_value` / `edit_value_segments`

```python
import ktav

out = ktav.edit_value("port: 8080\nhost: db\n", "port", 9090)
# "port: 9090\nhost: db\n"

out = ktav.edit_value_segments("a: {x: 1, y: 2}\n", ["a", "y"], {"n": [1]})
# "a: {x: 1, y: {n: [1]}}\n"
```

`edit_value` takes a textual path (`key1.key2.0.key4`): inside a
segment `\.` is a literal dot and `\\` a literal backslash; any other
escape raises `KtavInvalidPathError` whose `body` is the decimal UTF-8
byte offset of the problem. `edit_value_segments` takes
already-decoded literal segments with no extra unescaping — a numeric
segment is a string key inside an Object and a zero-based index inside
an Array. Only replacement of an existing value is supported; missing
keys, out-of-bounds indexes and descent through a scalar raise
`KtavNotFoundError`.

The edit is a source splice, not a parse→mutate→serialize of the whole
document: comments, key spelling, order, whitespace, BOM and
CR/LF/CRLF outside the effective change are preserved byte-for-byte,
dotted/inline/block forms are kept, and an equal replacement is a
byte-identical no-op — even for noncanonical spelling. Every
successful patch is re-parsed and semantically verified. When no
lossless patch exists (noncontiguous dotted/reopened targets, internal
comments under structural replacement, a `))` line inside a multiline
replacement) the call raises `KtavUnsupportedError` instead of
guessing. Long or multiline replacements unfold only the touched
inline wrappers; untouched nested branches stay inline. Both the
native and the pure backend implement the identical semantics.

>>>>> lang=ru
### Правка исходника — `edit_value` / `edit_value_segments`

```python
import ktav

out = ktav.edit_value("port: 8080\nhost: db\n", "port", 9090)
# "port: 9090\nhost: db\n"

out = ktav.edit_value_segments("a: {x: 1, y: 2}\n", ["a", "y"], {"n": [1]})
# "a: {x: 1, y: {n: [1]}}\n"
```

`edit_value` принимает текстовый путь (`key1.key2.0.key4`): внутри
сегмента `\.` — literal точка, `\\` — literal backslash; любой другой
escape бросает `KtavInvalidPathError`, у которого `body` — десятичный
UTF-8 byte offset проблемного места. `edit_value_segments` принимает
уже декодированные literal-сегменты без повторного unescape — числовой
сегмент это строковый ключ в Object и zero-based индекс в Array.
Поддерживается только замена существующего значения: отсутствующий
ключ, выход за границы массива и спуск сквозь скаляр дают
`KtavNotFoundError`.

Правка — это splice исходника, а не parse→mutate→serialize всего
документа: комментарии, написание ключей, порядок, пробелы, BOM и
CR/LF/CRLF вне эффективного изменения сохраняются побайтово,
dotted/inline/block-формы держатся, а совпадающая замена —
byte-identical no-op, даже при неканоничном написании. Каждый
успешный патч перепарсится и семантически проверяется. Когда lossless
патча не существует (noncontiguous dotted/reopen-цели, внутренние
комментарии при структурной замене, строка `))` внутри multiline
замены), вызов бросает `KtavUnsupportedError`, а не угадывает. Длинные
и многострочные замены раскрывают только затронутые inline-обёртки;
нетронутые ветки остаются inline. Native и pure backend реализуют
идентичную семантику.

>>>>> lang=zh
### 源文本编辑 —— `edit_value` / `edit_value_segments`

```python
import ktav

out = ktav.edit_value("port: 8080\nhost: db\n", "port", 9090)
# "port: 9090\nhost: db\n"

out = ktav.edit_value_segments("a: {x: 1, y: 2}\n", ["a", "y"], {"n": [1]})
# "a: {x: 1, y: {n: [1]}}\n"
```

`edit_value` 接受文本路径(`key1.key2.0.key4`):段内 `\.` 表示
literal 点号,`\\` 表示 literal 反斜杠;任何其他转义都会抛出
`KtavInvalidPathError`,其 `body` 是问题位置的 UTF-8 字节偏移十进制串。
`edit_value_segments` 接受已解码的 literal 段,不再额外反转义 ——
数字段在 Object 中是字符串键,在 Array 中是零基索引。仅支持替换
既有值:缺失键、越界索引与穿过标量的下降都会抛出
`KtavNotFoundError`。

编辑是对源文本的 splice,而不是整个文档的
parse→mutate→serialize:有效修改之外的注释、键拼写、顺序、空白、
BOM 与 CR/LF/CRLF 按字节保留,dotted/inline/block 形式得以维持,
相同替换是字节级 no-op —— 即使拼写非规范。每个成功的补丁都会
重新解析并做语义校验。当不存在无损补丁时(noncontiguous 的
dotted/reopen 目标、结构替换下的内部注释、multiline 替换中的
`))` 行),调用抛出 `KtavUnsupportedError` 而不是猜测。长或多行
替换只展开被触及的 inline 包装层;未触及的嵌套分支保持 inline。
native 与 pure backend 实现完全一致的语义。

