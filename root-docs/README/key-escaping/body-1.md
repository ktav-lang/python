>>>>> lang=en
## Key escaping

Since spec 0.6.4 a literal `.` or `:` inside a key segment is written
with a backslash:

```text
a\.b: v
a\:b: v
x.y\.z: v
a."b.c".d: v
"\u0041": v
```

A literal backslash in a key is `\\`. Since spec 0.7, a whole segment
may instead use double quotes, single quotes or backticks. Quotes only
delimit key segments, not values; `\uXXXX` decodes a Unicode code point.

>>>>> lang=ru
## Экранирование в ключах

Начиная со spec 0.6.4, литеральные `.` или `:` внутри сегмента ключа
записываются через обратный слеш:

```text
a\.b: v
a\:b: v
x.y\.z: v
a."b.c".d: v
"\u0041": v
```

Литеральный обратный слеш в ключе пишется как `\\`. Начиная со spec 0.7,
сегмент можно также взять в двойные, одинарные кавычки или обратные апострофы.
Кавычки ограничивают только сегменты ключа, не значения; `\uXXXX` декодирует
кодовую точку Unicode.

>>>>> lang=zh
## 键的转义

自 spec 0.6.4 起，键段内的字面量 `.` 或 `:` 通过反斜杠书写：

```text
a\.b: v
a\:b: v
x.y\.z: v
a."b.c".d: v
"\u0041": v
```

键中的字面量反斜杠写作 `\\`。自 spec 0.7 起,还可以用双引号、单引号或
反引号括住整个键段。引号只用于键段,不用于值;`\uXXXX` 解码 Unicode 码点。

