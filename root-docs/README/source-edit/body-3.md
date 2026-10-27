>>>>> lang=en
`insert_value` and `remove_value` take the same textual paths as
`edit_value`; the `_segments` forms take already-decoded literal
segments. Insert's final segment names a new Object key: its parent must
exist and be an Object, and an existing key is never overwritten. Array
insertion is unsupported. Remove accepts an existing value, including
an array element (later elements shift); emptied parent Objects remain
rather than being pruned. Rename addresses an Object member and takes
`new_key` as one literal name, not a path; dots and backslashes there
are ordinary characters. The member's position and value stay put, and
a name collision is rejected.

These operations splice source text rather than serializing the whole
document. Existing layout and unrelated text are preserved whenever a
lossless patch is possible; unsupported structural cases fail explicitly
instead of guessing. Empty segment lists and missing targets are errors.
The insert, remove and rename APIs are available with the native
backend. The pure-Python backend implements insert, remove and rename (including
`insert_value_segments`); their current readiness and conformance are pending CI
verification.

>>>>> lang=ru
`insert_value` и `remove_value` принимают текстовые пути как
`edit_value`; варианты `_segments` принимают уже декодированные
literal-сегменты. Последний сегмент вставки задаёт новый ключ Object:
родитель должен существовать и быть Object, существующий ключ никогда
не перезаписывается. Вставка в Array не поддерживается. Удаление
принимает существующее значение, включая элемент массива (последующие
элементы сдвигаются); опустевшие родительские Object сохраняются.
Переименование адресует член Object, а `new_key` — одно буквальное имя,
не путь: точки и обратные косые черты в нём являются обычными символами.
Позиция и значение члена сохраняются; конфликт имени отклоняется.

Эти операции выполняют splice исходника, а не сериализуют весь документ.
Существующая раскладка и посторонний текст сохраняются, если возможна
lossless-правка; неподдерживаемые структурные случаи явно завершаются
ошибкой вместо догадок. Пустой список сегментов и отсутствующая цель —
ошибки. API вставки, удаления и переименования доступны с native
backend. Pure-Python backend реализует вставку, удаление и переименование
(включая `insert_value_segments`); их текущая готовность и соответствие
ожидают проверки CI.

>>>>> lang=zh
`insert_value` 和 `remove_value` 接受与 `edit_value` 相同的文本路径；
`_segments` 形式接受已解码的 literal 段。插入路径的最后一段是新
Object 键：父级必须存在且为 Object，已有键绝不会被覆盖。不支持向
Array 插入。删除接受既有值，包括数组元素（后续元素会前移）；变空
的父 Object 不会被裁掉。重命名定位 Object 成员，`new_key` 是单个
literal 名称而非路径，其中的点号和反斜杠都是普通字符。成员位置与
值保持不变；名称冲突会被拒绝。

这些操作通过 splice 修改源文本，而不是序列化整个文档。只要存在
无损补丁，就保留已有布局及无关文本；不支持的结构情形会明确失败，
不会猜测。空段列表和不存在的目标均为错误。插入、删除与重命名 API
可在 native backend 中使用。Pure-Python backend 已实现插入、删除与重命名（包括
`insert_value_segments`）；其当前就绪度与符合预期情况仍待 CI 验证。

