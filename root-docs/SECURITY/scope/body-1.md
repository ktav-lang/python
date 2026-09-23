>>>>> lang=en
## Scope

Issues that count as security problems for this package:

- Out-of-bounds reads / writes or panics in the compiled `_core`
  extension module (PyO3 catches Rust panics and re-raises them as
  `pyo3_runtime.PanicException`, so the interpreter survives — but a
  panic on trusted input is still a bug worth reporting here).
- Runaway memory or CPU when parsing crafted input.
- Any behaviour that allows crafted Ktav input to escape the expected
  value-domain (arbitrary object construction, memory disclosure
  through the extension, etc.).
- Segfaults that bypass PyO3's panic bridge — these indicate real
  `unsafe` soundness issues and take priority.

Issues that are **not** security problems here — please use regular
issues for these:

- Performance regressions without crash / hang characteristics.
- Exception type mismatches that aren't exploitable (e.g. `ValueError`
  where `TypeError` would read better).
- Problems in the Ktav format itself — those belong in
  [`ktav-lang/spec`](https://github.com/ktav-lang/spec).
>>>>> lang=ru
## Область

Проблемы, которые считаются проблемами безопасности для этого пакета:

- Чтения / записи за пределы буфера или паники в скомпилированном модуле
  расширения `_core` (PyO3 перехватывает Rust-паники и пробрасывает их
  как `pyo3_runtime.PanicException`, поэтому интерпретатор выживает — но
  паника на доверенном входе всё равно — баг, о котором стоит сообщить
  сюда).
- Неконтролируемые память или CPU при разборе злонамеренного входа.
- Любое поведение, позволяющее злонамеренному входу Ktav выйти за
  ожидаемый value-домен (произвольная конструкция объектов, раскрытие
  памяти через расширение и т. п.).
- Сегфолты в обход panic-моста PyO3 — они указывают на реальные
  проблемы soundness в `unsafe` и имеют приоритет.

Проблемы, которые **не** считаются проблемами безопасности здесь —
используйте для них обычные issue:

- Регрессии производительности без признаков падения / зависания.
- Несоответствия типа исключения, которые не эксплуатируются
  (например, `ValueError` там, где лучше читался бы `TypeError`).
- Проблемы в самом формате Ktav — им место в
  [`ktav-lang/spec`](https://github.com/ktav-lang/spec).
>>>>> lang=zh
## 范围

会被视作本包安全问题的情况：

- 编译后的 `_core` 扩展模块中的越界读写或 panic（PyO3 会捕获 Rust
  panic 并重新抛为 `pyo3_runtime.PanicException`，使解释器得以存活 ——
  但可信输入下的 panic 仍然是值得上报的 bug）。
- 解析构造输入时出现失控的内存或 CPU 消耗。
- 任何允许构造的 Ktav 输入逃逸出预期值域的行为（任意对象构造、
  通过扩展的内存泄露等）。
- 绕过 PyO3 panic 桥的 segfault —— 这类问题指向真正的 `unsafe`
  soundness 问题，优先处理。

**不**算作本包安全问题的情况 —— 请走普通 issue：

- 没有崩溃 / 挂起特征的性能回归。
- 不可利用的异常类型失配（例如应当是 `TypeError` 的地方报了 `ValueError`）。
- Ktav 格式本身的问题 —— 它们属于
  [`ktav-lang/spec`](https://github.com/ktav-lang/spec)。
