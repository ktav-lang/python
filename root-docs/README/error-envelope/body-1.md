>>>>> lang=en
Since 0.7.1 every raised instance also carries the structured error
envelope as attributes: `error`, `reason`, `line`, `line_text`, `span`,
`path`, `body`, `canonical`, `spec_section`. Absent information is
`None`, never a missing attribute. `span` is `{"start": …, "end": …}`
byte offsets into the UTF-8 source; `path` is the list of exact decoded
key segments (a key literally named `a.b` is one segment, never split).
`str(e)` stays a human-readable message — the raw envelope is never
substituted for it.

>>>>> lang=ru
Начиная с 0.7.1 каждое брошенное исключение несёт ещё и структурный
конверт ошибки в виде атрибутов: `error`, `reason`, `line`, `line_text`,
`span`, `path`, `body`, `canonical`, `spec_section`. Отсутствующие
сведения — `None`, а не пропущенный атрибут. `span` — это
`{"start": …, "end": …}`, смещения в байтах по UTF-8-исходнику;
`path` — список точных декодированных сегментов ключа (ключ, буквально
названный `a.b`, — это один сегмент, и он никогда не разрезается).
`str(e)` остаётся человекочитаемым сообщением — сырой конверт вместо
него не подставляется.

>>>>> lang=zh
自 0.7.1 起，每个抛出的异常实例还以属性形式携带结构化错误信封：`error`、
`reason`、`line`、`line_text`、`span`、`path`、`body`、`canonical`、
`spec_section`。缺失的信息是 `None`，而不是缺少属性。`span` 是
`{"start": …, "end": …}`，即 UTF-8 源文本中的字节偏移；`path` 是精确
解码后的键段列表（字面名为 `a.b` 的键是一个段，绝不会被切开）。
`str(e)` 仍然是人类可读的消息 —— 原始信封不会被用来取代它。

