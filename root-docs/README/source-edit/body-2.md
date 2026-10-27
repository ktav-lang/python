>>>>> lang=en
The edit is a source splice, not a parse→mutate→serialize of the whole
document: comments, key spelling, order, whitespace, BOM and
CR/LF/CRLF outside the effective change are preserved byte-for-byte,
dotted/inline/block forms are kept, and an equal replacement is a
byte-identical no-op — even for noncanonical spelling. Every
successful patch is re-parsed and semantically verified. When no
lossless patch exists (noncontiguous dotted/reopened targets, internal
comments under structural replacement, an unrepresentable value in the
target context) the call raises `KtavUnsupportedError` instead of
guessing. Long or multiline replacements unfold only the touched
inline wrappers; untouched nested branches stay inline. Both the
native and the pure backend implement the identical semantics.

### Structural source edits — insert, remove, rename

```python
inserted = ktav.insert_value(source, "service.timeout", 30)
removed = ktav.remove_value(inserted, "service.old")
renamed = ktav.rename_key(removed, "service.timeout", "deadline")

# Literal segments avoid path escaping:
inserted = ktav.insert_value_segments(source, ["a.b", "x\\y"], "v")
renamed = ktav.rename_key_segments(source, ["a.b", "x\\y"], "z.w")
```

>>>>> lang=ru
Правка — это splice исходника, а не parse→mutate→serialize всего
документа: комментарии, написание ключей, порядок, пробелы, BOM и
CR/LF/CRLF вне эффективного изменения сохраняются побайтово,
dotted/inline/block-формы держатся, а совпадающая замена —
byte-identical no-op, даже при неканоничном написании. Каждый
успешный патч перепарсится и семантически проверяется. Когда lossless
патча не существует (noncontiguous dotted/reopen-цели, внутренние
комментарии при структурной замене, непредставимое в контексте цели
значение), вызов бросает `KtavUnsupportedError`, а не угадывает. Длинные
и многострочные замены раскрывают только затронутые inline-обёртки;
нетронутые ветки остаются inline. Native и pure backend реализуют
идентичную семантику.

### Структурные правки исходника — вставка, удаление, переименование

```python
inserted = ktav.insert_value(source, "service.timeout", 30)
removed = ktav.remove_value(inserted, "service.old")
renamed = ktav.rename_key(removed, "service.timeout", "deadline")

# Literal-сегменты не требуют экранирования пути:
inserted = ktav.insert_value_segments(source, ["a.b", "x\\y"], "v")
renamed = ktav.rename_key_segments(source, ["a.b", "x\\y"], "z.w")
```

>>>>> lang=zh
编辑是对源文本的 splice,而不是整个文档的
parse→mutate→serialize:有效修改之外的注释、键拼写、顺序、空白、
BOM 与 CR/LF/CRLF 按字节保留,dotted/inline/block 形式得以维持,
相同替换是字节级 no-op —— 即使拼写非规范。每个成功的补丁都会
重新解析并做语义校验。当不存在无损补丁时(noncontiguous 的
dotted/reopen 目标、结构替换下的内部注释、或在目标上下文中无法
无损表示的值),调用抛出 `KtavUnsupportedError` 而不是猜测。长或多行
替换只展开被触及的 inline 包装层;未触及的嵌套分支保持 inline。
native 与 pure backend 实现完全一致的语义。

### 结构化源文本编辑 —— 插入、删除与重命名

```python
inserted = ktav.insert_value(source, "service.timeout", 30)
removed = ktav.remove_value(inserted, "service.old")
renamed = ktav.rename_key(removed, "service.timeout", "deadline")

# literal 段无需路径转义：
inserted = ktav.insert_value_segments(source, ["a.b", "x\\y"], "v")
renamed = ktav.rename_key_segments(source, ["a.b", "x\\y"], "z.w")
```

