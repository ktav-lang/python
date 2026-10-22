>>>>> lang=en
## Errors

```python
import ktav

try:
    ktav.loads("x: [")
except ktav.KtavDecodeError as e:
    print("decode:", e)

try:
    ktav.dumps({"v": float("nan")})
except ktav.KtavEncodeError as e:
    print("encode:", e)

# Catching the base class catches either.
try:
    ktav.loads("a: 1\na: 2")
except ktav.KtavError:
    ...
```

| Exception           | Raised by   | Base                |
|---------------------|-------------|---------------------|
| `KtavError`         | (base)      | `Exception`         |
| `KtavDecodeError`   | `loads` / `load` | `KtavError`    |
| `KtavEncodeError`   | `dumps` / `dump` | `KtavError`    |

Both backends raise the same exceptions carrying the identical
ten-field envelope. One deliberate delta: for a `str` input containing
literal lone surrogates, pure mode raises `KtavDecodeError` with the
error category `InvalidUtf8` and a nonempty span over the malformed
bytes, where the native extension surfaces a `UnicodeEncodeError`.

>>>>> lang=ru
## Ошибки

```python
import ktav

try:
    ktav.loads("x: [")
except ktav.KtavDecodeError as e:
    print("decode:", e)

try:
    ktav.dumps({"v": float("nan")})
except ktav.KtavEncodeError as e:
    print("encode:", e)

# Catching the base class catches either.
try:
    ktav.loads("a: 1\na: 2")
except ktav.KtavError:
    ...
```

| Исключение          | Источник          | База                |
|---------------------|-------------------|---------------------|
| `KtavError`         | (базовое)        | `Exception`         |
| `KtavDecodeError`   | `loads` / `load`  | `KtavError`         |
| `KtavEncodeError`   | `dumps` / `dump`  | `KtavError`         |

Оба backend-а бросают одни и те же исключения с идентичным
десятипольным конвертом. Одно осознанное отличие: для входной `str`
с литеральными lone-суррогатами pure-режим бросает `KtavDecodeError`
с категорией ошибки `InvalidUtf8` и непустым span над некорректными байтами,
тогда как нативное расширение отдаёт `UnicodeEncodeError`.

>>>>> lang=zh
## 错误

```python
import ktav

try:
    ktav.loads("x: [")
except ktav.KtavDecodeError as e:
    print("decode:", e)

try:
    ktav.dumps({"v": float("nan")})
except ktav.KtavEncodeError as e:
    print("encode:", e)

# Catching the base class catches either.
try:
    ktav.loads("a: 1\na: 2")
except ktav.KtavError:
    ...
```

| 异常                | 抛出者            | 基类                |
|---------------------|-------------------|---------------------|
| `KtavError`         | （基类）          | `Exception`         |
| `KtavDecodeError`   | `loads` / `load`  | `KtavError`         |
| `KtavEncodeError`   | `dumps` / `dump`  | `KtavError`         |

两个 backend 抛出相同的异常，携带完全一致的十字段信封。唯一刻意的
差异：当输入 `str` 含有字面 lone surrogate 时，纯模式抛出
`KtavDecodeError`，错误类别为 `InvalidUtf8`，并对畸形字节给出非空 span；
而原生扩展则抛出 `UnicodeEncodeError`。

