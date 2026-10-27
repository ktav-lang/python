>>>>> lang=en
## Unreleased — 0.9 preparation

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
- `ktav.insert_value(source, path, value)` and
  `ktav.insert_value_segments(source, segments, value)` add a new Object
  member without overwriting an existing key. `ktav.remove_value(source, path)`
  and `ktav.remove_value_segments(source, segments)` remove an existing
  value (array elements shift; empty parent Objects remain).
- `ktav.rename_key(source, path, new_key)` and
  `ktav.rename_key_segments(source, segments, new_key)` rename an Object
  member in place; `new_key` is one literal key, not a dotted path.
  All six APIs use lossless source splices, are available in native and
  pure-Python backends, and reject unsupported structural cases explicitly.
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

### Documentation

- Expand README examples for dotted and literal-key paths, mixed arrays, String/Integer identity, multiline unfolding, byte-identical no-op and BOM/CRLF/EOF preservation. Clarify 0.9 byte diagnostics, safe refusal, ABI 2 and standalone pure usage; these additions are not part of published 0.8.1.

>>>>> lang=ru
## Ещё не выпущено — подготовка 0.9

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
- `ktav.insert_value(source, path, value)` и
  `ktav.insert_value_segments(source, segments, value)` добавляют новый
  член Object без перезаписи существующего ключа. `ktav.remove_value(source, path)`
  и `ktav.remove_value_segments(source, segments)` удаляют существующее
  значение (элементы массива сдвигаются; пустые родительские Object остаются).
- `ktav.rename_key(source, path, new_key)` и
  `ktav.rename_key_segments(source, segments, new_key)` переименовывают член Object
  на месте; `new_key` — одно буквальное имя, а не dotted-путь.
  Все шесть API выполняют lossless-splice исходника, доступны в native и
  pure-Python backend и явно отклоняют неподдерживаемые структурные случаи.
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

### Документация

- Дополнены примеры README: dotted-пути и буквальные ключи, смешанные массивы, различие String/Integer, раскрытие многострочной замены, побайтовый no-op и сохранение BOM/CRLF/EOF. Уточнены байтовая диагностика 0.9, безопасные отказы, ABI 2 и самостоятельный pure-бэкенд; дополнения не относятся к опубликованному 0.8.1.

>>>>> lang=zh
## 尚未发布 — 0.9 准备版本

- `ktav.edit_value(source, path, replacement)` 与
  `ktav.edit_value_segments(source, segments, replacement)` ——
  无损的原地源文本编辑(source-edit 0.9)。只有目标值的字节会改变
  (加上布局规则要求展开的 inline 包装层);注释、键拼写、空行、
  BOM 与 CR/LF/CRLF 全部保留,相同替换是字节级 no-op。新增异常家族
  `KtavEditError`,含 `KtavInvalidPathError`(`body` = 路径参数的
  UTF-8 字节偏移十进制串)、`KtavNotFoundError` 与
  `KtavUnsupportedError`;信封仍是同样的十字段,`error` 取
  `EditInvalidPath` / `EditNotFound` / `EditUnsupported` 之一。
- `ktav.insert_value(source, path, value)` 与
  `ktav.insert_value_segments(source, segments, value)` 新增 Object 成员，
  不覆盖已有键。`ktav.remove_value(source, path)` 与
  `ktav.remove_value_segments(source, segments)` 删除已有值（数组元素前移，
  空的父 Object 保留）。
- `ktav.rename_key(source, path, new_key)` 与
  `ktav.rename_key_segments(source, segments, new_key)` 原位重命名 Object 成员；
  `new_key` 是一个字面键名，而非点分路径。六个 API 均通过无损源文本 splice
  实现，native 与 pure-Python 后端均可用，并会明确拒绝不支持的结构情况。
- spec 0.9 语料:conformance 运行器现在执行 `versions/0.9/tests`
  的 fixture(162 个 invalid —— 其中 72 个是新的 `diagnostics09`
  EOF/坏 UTF-8 诊断),校验 `expected_location` 元数据(line、
  原始字节 `start`、精确 `end` 或 `minimum_end`),并让所有
  `raw_bytes` fixture 走共享的字节边界,因此两个 backend 中坏
  UTF-8 都会抛出结构化的 `InvalidUtf8` 信封。
- `UnclosedCompound` 错误现在固定 opener:`line` 与 `line_text`
  指向打开最内层未闭合容器的行,`span` 从该 opener 延伸到输入末尾。

### 文档

- 扩展 README 示例：点分路径与字面键、混合数组、String/Integer 区别、多行展开、逐字节 no-op 及 BOM/CRLF/EOF 保留。明确 0.9 字节诊断、安全拒绝、ABI 2 和独立纯实现用法；这些新增功能不属于已发布的 0.8.1。

