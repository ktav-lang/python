>>>>> lang=en
---

## [0.3.1] — 2026-05-10

Backward-compatible feature release: top-level Arrays and a new
`dumps_force_strings` entry point.

### Added

- **Top-level Array support** (spec 0.1.1, § 5.0.1) — the parser now
  recognises documents whose first content line is an array-item
  shape (a bare scalar, `:: text`, `:i 42`, `:f 3.14`, a lone `{` /
  `[`, or a multi-line opener `(` / `((`) as a root-level Array.
  `ktav.loads(":i 1\n:i 2")` returns `[1, 2]`. Object documents are
  unchanged. The serialiser accepts top-level `list` / `tuple` and
  emits items bare, one per line, with no surrounding `[...]`.
- **`ktav.dumps_force_strings(obj)`** — render every leaf scalar as
  a String (typed integers, typed floats, booleans, and `None` are
  flattened to their textual form via the raw `::` marker so the
  output round-trips back as the same string scalars). Compounds
  preserve their structure; only leaves are coerced. The
  Python-idiomatic snake_case parallel to `dumps` / `loads`.

>>>>> lang=ru
---

## [0.3.1] — 2026-05-10

Обратносовместимый feature-релиз: top-level Array'ы и новая точка
входа `dumps_force_strings`.

### Added

- **Поддержка top-level Array** (spec 0.1.1, § 5.0.1) — парсер теперь
  распознаёт документы, у которых первая значимая строка имеет форму
  элемента массива (голый скаляр, `:: text`, `:i 42`, `:f 3.14`,
  одиночный `{` / `[` или multi-line opener `(` / `((`), как корневой
  Array. `ktav.loads(":i 1\n:i 2")` возвращает `[1, 2]`.
  Object-документы не меняются. Сериализатор принимает top-level
  `list` / `tuple` и пишет элементы голыми, по одному на строку, без
  обрамляющих `[...]`.
- **`ktav.dumps_force_strings(obj)`** — рендерит каждый лист-скаляр
  как String (типизированные целые, типизированные дробные, булевы
  значения и `None` уплощаются до текстовой формы через сырой маркер
  `::`, так что вывод round-trip'ит обратно как те же string-скаляры).
  Compounds сохраняют структуру; коэрсятся только листья.
  Python-идиоматичный snake_case-параллель `dumps` / `loads`.

>>>>> lang=zh
---

## [0.3.1] — 2026-05-10

向后兼容的功能发布:支持 top-level Array,并新增
`dumps_force_strings` 入口。

### Added

- **支持 top-level Array**(spec 0.1.1,§ 5.0.1)——解析器现在能够识别
  首个内容行为数组元素形状(裸标量、`:: text`、`:i 42`、`:f 3.14`、
  单独的 `{` / `[`,或 multi-line 开括号 `(` / `((`)的文档,并将其作为
  根级 Array。`ktav.loads(":i 1\n:i 2")` 返回 `[1, 2]`。Object 文档
  不受影响。序列化器接受 top-level `list` / `tuple`,并按每行一个、
  不带外层 `[...]` 的方式写出元素。
- **`ktav.dumps_force_strings(obj)`**——将每个叶标量渲染为 String
  (类型化整数、类型化浮点、布尔值和 `None` 会被压平为文本形式,并经
  原始 `::` 标记写出,使输出能够 round-trip 回相同的字符串标量)。
  Compound 保持结构不变;只有叶被强制转换。这是与 `dumps` /
  `loads` 并列的、符合 Python 习惯的 snake_case 命名。

