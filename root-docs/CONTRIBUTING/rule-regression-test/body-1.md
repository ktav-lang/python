>>>>> lang=en
## Core rules

### 1. Every bug fix ships with a regression test

When you find a bug, **before fixing it**, write a test that reproduces
it — the test **must fail on `main`** and pass after the fix. Include
both in the same PR.

Tests live under `tests/`:

| File                         | Scope                                        |
|------------------------------|----------------------------------------------|
| `test_loads.py`              | Parser behaviour.                            |
| `test_dumps.py`              | Serializer behaviour.                        |
| `test_roundtrip.py`          | `loads(dumps(x)) == x`.                      |
| `test_errors.py`             | Exception taxonomy and propagation.          |
| `test_load_dump.py`          | File-like wrappers.                          |
| `test_module.py`             | Module-level exports, version strings.       |
| `test_conformance.py`        | Cross-language conformance against the spec. |

>>>>> lang=ru
## Основные правила

### 1. Каждый багфикс сопровождается регрессионным тестом

Когда вы нашли баг, **до того, как его исправлять**, напишите
воспроизводящий тест — он **должен падать на `main`** и проходить
после фикса. И тест, и фикс — в одном PR.

Тесты лежат в `tests/`:

| Файл | Область |
|------|---------|
| `test_loads.py` | Поведение парсера. |
| `test_dumps.py` | Поведение сериализатора. |
| `test_roundtrip.py` | `loads(dumps(x)) == x`. |
| `test_errors.py` | Таксономия и распространение исключений. |
| `test_load_dump.py` | Обёртки под файл-подобные объекты. |
| `test_module.py` | Экспорты модуля, строки версий. |
| `test_conformance.py` | Кросс-языковое соответствие спецификации. |

>>>>> lang=zh
## 核心规则

### 1. 每个 bug 修复都伴随一个回归测试

发现 bug 时，**在修复之前**，先写一个能复现该 bug 的测试 ——
它在 `main` 上**必须失败**，并在修复后通过。测试与修复放在同一个 PR。

测试位于 `tests/`：

| 文件 | 范围 |
|------|------|
| `test_loads.py` | 解析器行为。 |
| `test_dumps.py` | 序列化器行为。 |
| `test_roundtrip.py` | `loads(dumps(x)) == x`。 |
| `test_errors.py` | 异常分类与传播。 |
| `test_load_dump.py` | 类文件对象包装。 |
| `test_module.py` | 模块级导出、版本字符串。 |
| `test_conformance.py` | 跨语言规范一致性测试。 |

