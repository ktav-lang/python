>>>>> lang=en
## Philosophy

Ktav is intentionally small. Its five design principles
(from [`spec/CONTRIBUTING.md`](https://github.com/ktav-lang/spec/blob/main/CONTRIBUTING.md)):

1. **Locality** — a line's meaning does not depend on another line.
2. **One sentence** — any new rule fits in one sentence of the spec.
3. **No whitespace sensitivity** (line breaks aside).
4. **No magic types** — the format never decides `"8080"` means a number.
5. **Explicit over clever** — `::` is verbose on purpose.

The Python bindings honour this: they add no schema inference, no
auto-casting, no defaulting. If you want typing, you do it at the
boundary with your own tool — `pydantic`, `dataclasses`, `attrs` —
against the native Python structures this library returns.

>>>>> lang=ru
## Философия

Ktav намеренно маленький. Пять принципов проектирования
(из [`spec/CONTRIBUTING.md`](https://github.com/ktav-lang/spec/blob/main/CONTRIBUTING.md)):

1. **Локальность** — смысл строки не зависит от другой строки.
2. **Одно предложение** — новое правило умещается в одну фразу спеки.
3. **Нет чувствительности к пробелам** (кроме переноса строк).
4. **Никакой магии в типах** — формат не решает, что `"8080"` — число.
5. **Явно лучше, чем хитро** — `::` избыточен намеренно.

Python-биндинги следуют этому: никакой inference-ы схемы, никакого
авто-каста, никаких значений по умолчанию. Хотите типизацию — делайте её
на границе своим инструментом (`pydantic`, `dataclasses`, `attrs`)
поверх нативных Python-структур, которые вернула эта библиотека.

>>>>> lang=zh
## 哲学

Ktav 刻意保持小巧。它的五条设计原则
（出自 [`spec/CONTRIBUTING.md`](https://github.com/ktav-lang/spec/blob/main/CONTRIBUTING.md)）：

1. **局部性** —— 一行的含义不取决于另一行。
2. **一句话** —— 任何新规则都能写进规范的一句话里。
3. **对空白不敏感**（换行除外）。
4. **没有魔法类型** —— 格式从不判定 `"8080"` 表示数字。
5. **显式优于聪明** —— `::` 故意保持冗长。

Python 绑定遵守这一点：不做任何模式推断、不做自动类型转换、不提供默认
值。如果需要类型，请在边界处用自己的工具 —— `pydantic`、`dataclasses`、
`attrs` —— 对本库返回的原生 Python 结构进行。

