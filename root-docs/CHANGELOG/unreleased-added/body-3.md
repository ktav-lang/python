>>>>> lang=en
- `ktav.edit_value(source, path, replacement)` and
  `ktav.edit_value_segments(source, segments, replacement)` — lossless
  in-place source edits (source-edit 0.9). Only the bytes of the target
  value (plus inline wrappers the layout rules force to unfold) change;
  comments, key spelling, blank lines, BOM and CR/LF/CRLF survive, and
  an equal replacement is a byte-identical no-op. New exception family
  `KtavEditError` with `KtavInvalidPathError` (`body` = decimal UTF-8
  byte offset into the path), `KtavNotFoundError`, and
  `KtavUnsupportedError`; the same ten-field envelope, `error` is one
  of `EditInvalidPath` / `EditNotFound` / `EditUnsupported`.
- Spec 0.9 corpus: the conformance runner now executes the
  `versions/0.9/tests` fixtures (162 invalid — 72 new `diagnostics09`
  EOF/malformed-UTF-8 diagnostics), validates `expected_location`
  metadata (line, raw-byte `start`, exact `end` or `minimum_end`), and
  feeds every `raw_bytes`-flagged fixture through the shared byte
  boundary, so invalid UTF-8 raises the structured `InvalidUtf8`
  envelope in both backends.
- `UnclosedCompound` errors now pin the opener: `line` and `line_text`
  name the line that opened the innermost unclosed compound, and
  `span` runs from that opener to end of input.

>>>>> lang=ru
- `ktav.edit_value(source, path, replacement)` и
  `ktav.edit_value_segments(source, segments, replacement)` —
  lossless-правка исходника по месту (source-edit 0.9). Меняются только
  байты целевого значения (плюс inline-обёртки, которые требует
  раскрыть layout-правило); комментарии, написание ключей, пустые
  строки, BOM и CR/LF/CRLF сохраняются, а совпадающая замена —
  byte-identical no-op. Новое семейство исключений `KtavEditError` с
  `KtavInvalidPathError` (`body` = десятичный UTF-8 byte offset в
  путь), `KtavNotFoundError` и `KtavUnsupportedError`; тот же
  десятипольный конверт, `error` — один из `EditInvalidPath` /
  `EditNotFound` / `EditUnsupported`.
- Корпус spec 0.9: conformance runner исполняет fixtures из
  `versions/0.9/tests` (162 invalid — 72 новых диагностики
  `diagnostics09` EOF/битый UTF-8), проверяет метаданные
  `expected_location` (line, raw-byte `start`, точный `end` или
  `minimum_end`) и прогоняет все `raw_bytes`-fixture через общий
  byte-boundary, так что битый UTF-8 даёт структурированный конверт
  `InvalidUtf8` в обоих backend-ах.
- Ошибки `UnclosedCompound` теперь указывают открыватель: `line` и
  `line_text` называют строку, открывшую ближайший незакрытый
  контейнер, а `span` тянется от него до конца ввода.

>>>>> lang=zh
- `ktav.edit_value(source, path, replacement)` 与
  `ktav.edit_value_segments(source, segments, replacement)` ——
  无损的原地源文本编辑(source-edit 0.9)。只有目标值的字节会改变
  (加上布局规则要求展开的 inline 包装层);注释、键拼写、空行、
  BOM 与 CR/LF/CRLF 全部保留,相同替换是字节级 no-op。新增异常家族
  `KtavEditError`,含 `KtavInvalidPathError`(`body` = 路径参数的
  UTF-8 字节偏移十进制串)、`KtavNotFoundError` 与
  `KtavUnsupportedError`;信封仍是同样的十字段,`error` 取
  `EditInvalidPath` / `EditNotFound` / `EditUnsupported` 之一。
- spec 0.9 语料:conformance 运行器现在执行 `versions/0.9/tests`
  的 fixture(162 个 invalid —— 其中 72 个是新的 `diagnostics09`
  EOF/坏 UTF-8 诊断),校验 `expected_location` 元数据(line、
  原始字节 `start`、精确 `end` 或 `minimum_end`),并让所有
  `raw_bytes` fixture 走共享的字节边界,因此两个 backend 中坏
  UTF-8 都会抛出结构化的 `InvalidUtf8` 信封。
- `UnclosedCompound` 错误现在固定 opener:`line` 与 `line_text`
  指向打开最内层未闭合容器的行,`span` 从该 opener 延伸到输入末尾。

