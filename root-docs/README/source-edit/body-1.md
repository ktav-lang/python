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

