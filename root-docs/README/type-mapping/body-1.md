>>>>> lang=en
## Type mapping

| Ktav                 | Python   |
|----------------------|----------|
| `null`               | `None`   |
| `true` / `false`     | `bool`   |
| bare integer (fits signed 64-bit) | `int`    |
| integer beyond 64-bit             | `str`    |
| bare decimal         | `float`  |
| other scalar         | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav types numbers by **lexical form** — a bare `port: 8080` is an
`int`, `ratio: 0.5` a `float`, and anything that isn't a bare number
stays a `str`. Force a numeric-looking value to stay a string with
`::` (`zip:: 01007`).

The Integer domain matches the native extension's (signed 64-bit): an
integer literal beyond `i64` parses as a `str`, re-emitted via the raw
`::` marker so it stays a string — the same behaviour in both backends.

`dict` preserves insertion order (Python 3.7+ guarantee), matching the
ordered-object semantics of Ktav.

Serialisation is the inverse:

- Python `int` → bare integer (including arbitrary-precision bigints;
  reading such a literal back yields a `str` — see above).
- Python `float` → bare decimal (decimal point always present;
  `NaN` / `±Infinity` are rejected — Ktav does not represent them).
- Python `tuple` is accepted as an array, for symmetry with `list`.
- Non-`str` keys in a `dict` raise `KtavEncodeError`.

>>>>> lang=ru
## Соответствие типов

| Ktav                 | Python   |
|----------------------|----------|
| `null`               | `None`   |
| `true` / `false`     | `bool`   |
| голое целое (в пределах 64 бит)   | `int`    |
| целое за пределами 64 бит         | `str`    |
| голое десятичное     | `float`  |
| прочий скаляр        | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav типизирует числа по **лексической форме** — голый `port: 8080`
это `int`, `ratio: 0.5` — `float`, а всё, что не является голым
числом, остаётся `str`. Чтобы число-подобное значение осталось
строкой, форсируйте его через `::` (`zip:: 01007`).

Домен Integer совпадает с нативным расширением (64 бита со знаком):
целочисленный литерал за пределами `i64` разбирается как `str` и
повторно выводится через сырой маркер `::`, чтобы остаться строкой —
поведение одинаково в обоих backend-ах.

`dict` сохраняет порядок вставки (гарантия Python 3.7+), что совпадает с
семантикой упорядоченных объектов Ktav.

Сериализация — обратное соответствие:

- Python `int` → голое целое (в том числе bigint произвольной точности;
  при чтении такой литерал вернётся как `str` — см. выше).
- Python `float` → голое десятичное (точка всегда присутствует;
  `NaN` / `±Infinity` отвергаются — Ktav их не представляет).
- Python `tuple` допустим как массив, симметрично `list`.
- Ключи `dict`, не являющиеся `str`, вызывают `KtavEncodeError`.

>>>>> lang=zh
## 类型映射

| Ktav                 | Python   |
|----------------------|----------|
| `null`               | `None`   |
| `true` / `false`     | `bool`   |
| 裸整数（64 位有符号范围内）| `int`    |
| 超出 64 位的整数          | `str`    |
| 裸小数               | `float`  |
| 其他标量             | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav 按**词法形式**为数字定型 —— 裸写的 `port: 8080` 是 `int`，
`ratio: 0.5` 是 `float`，而任何并非裸数字的内容都保持为 `str`。若要
让看起来像数字的值保持为字符串，用 `::` 强制（`zip:: 01007`）。

Integer 的值域与原生扩展一致（64 位有符号）：超出 `i64` 的整数字面量
解析为 `str`，并通过原始 `::` 标记重新输出以保持字符串 —— 两个
backend 行为相同。

`dict` 保留插入顺序（Python 3.7+ 的保证），与 Ktav 的有序对象语义一致。

序列化是它的逆运算：

- Python `int` → 裸整数（包括任意精度的大整数；读回这样的字面量时
  会得到 `str` —— 见上）。
- Python `float` → 裸小数（小数点始终存在；`NaN` / `±Infinity` 会被
  拒绝 —— Ktav 不表示它们）。
- Python `tuple` 可作为数组接受，与 `list` 对称。
- `dict` 中的非 `str` 键会引发 `KtavEncodeError`。

