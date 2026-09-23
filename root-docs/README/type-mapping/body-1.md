>>>>> lang=en
## Type mapping

| Ktav                 | Python   |
|----------------------|----------|
| `null`               | `None`   |
| `true` / `false`     | `bool`   |
| bare integer         | `int`    |
| bare decimal         | `float`  |
| other scalar         | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav types numbers by **lexical form** — a bare `port: 8080` is an
`int`, `ratio: 0.5` a `float`, and anything that isn't a bare number
stays a `str`. Force a numeric-looking value to stay a string with
`::` (`zip:: 01007`).

`dict` preserves insertion order (Python 3.7+ guarantee), matching the
ordered-object semantics of Ktav.

Serialisation is the inverse:

- Python `int` → bare integer (including arbitrary-precision bigints).
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
| голое целое          | `int`    |
| голое десятичное     | `float`  |
| прочий скаляр        | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav типизирует числа по **лексической форме** — голый `port: 8080`
это `int`, `ratio: 0.5` — `float`, а всё, что не является голым
числом, остаётся `str`. Чтобы число-подобное значение осталось
строкой, форсируйте его через `::` (`zip:: 01007`).

`dict` сохраняет порядок вставки (гарантия Python 3.7+), что совпадает с
семантикой упорядоченных объектов Ktav.

Сериализация — обратное соответствие:

- Python `int` → голое целое (в том числе bigint произвольной точности).
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
| 裸整数               | `int`    |
| 裸小数               | `float`  |
| 其他标量             | `str`    |
| `[ ... ]`            | `list`   |
| `{ ... }`            | `dict`   |

Ktav 按**词法形式**为数字定型 —— 裸写的 `port: 8080` 是 `int`，
`ratio: 0.5` 是 `float`，而任何并非裸数字的内容都保持为 `str`。若要
让看起来像数字的值保持为字符串，用 `::` 强制（`zip:: 01007`）。

`dict` 保留插入顺序（Python 3.7+ 的保证），与 Ktav 的有序对象语义一致。

序列化是它的逆运算：

- Python `int` → 裸整数（包括任意精度的大整数）。
- Python `float` → 裸小数（小数点始终存在；`NaN` / `±Infinity` 会被
  拒绝 —— Ktav 不表示它们）。
- Python `tuple` 可作为数组接受，与 `list` 对称。
- `dict` 中的非 `str` 键会引发 `KtavEncodeError`。

