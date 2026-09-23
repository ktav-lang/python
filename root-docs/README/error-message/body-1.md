>>>>> lang=en
`e.message` carries that same text as an attribute, so **`str(e) ==
e.message`**. It is redundant here by design: this binding has always
used the core's own rendering for `str(e)`, and the attribute exists so
the envelope has the same ten-field shape in Python that it has in every
other language — where `message` is the only way to reach the text. Use
it rather than rebuilding a sentence from `error`, `line` and `body`: a
reassembled message differs between bindings, and this one does not.

>>>>> lang=ru
`e.message` несёт тот же текст атрибутом, то есть **`str(e) ==
e.message`**. Здесь он избыточен намеренно: этот биндинг всегда брал для
`str(e)` собственный рендеринг ядра, а атрибут существует ради того,
чтобы конверт в Python имел ту же форму из десяти полей, что и в любом
другом языке, — там `message` единственный способ добраться до текста.
Пользуйтесь им, а не собирайте фразу заново из `error`, `line` и `body`:
пересобранное сообщение отличается от биндинга к биндингу, а это — нет.

>>>>> lang=zh
`e.message` 以属性形式携带同一段文本，即 **`str(e) == e.message`**。
它在这里是有意的冗余：本绑定的 `str(e)` 一直使用核心自身的渲染文本，
而这个属性存在的意义，是让信封在 Python 中拥有与其他任何语言相同的
十个字段 —— 在那些语言里，`message` 是取到该文本的唯一途径。请直接
使用它，而不要用 `error`、`line` 和 `body` 重新拼出一句话：重新拼装的
消息在各绑定之间并不一致，而这一个是一致的。

