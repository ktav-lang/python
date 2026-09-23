>>>>> lang=en

## [0.1.2] — 2026-05-03

### Changed

- **Picked up `ktav 0.1.5`** — the upstream Rust crate's structured
  errors API (`Error::Structured(ErrorKind)` with byte-offset spans),
  retroactive `#[non_exhaustive]` on the error enums, and the public
  `ktav::thin` event-based parser. The PyO3 binding's user-visible
  behaviour is unchanged: `KtavDecodeError` / `KtavEncodeError` still
  carry the same human-readable messages (Display strings for the
  seven canonical categories are byte-identical to ktav 0.1.4).
  Mapping `ktav::ErrorKind` to a structured Python exception
  hierarchy (`MissingSeparatorSpace`, `DuplicateKey`, etc.) is
  separate follow-up work tracked in the workspace's
  [`STRUCTURED_ERRORS.md`](https://github.com/ktav-lang/.github/blob/main/STRUCTURED_ERRORS.md).

PyPI: `ktav==0.1.2`.

>>>>> lang=ru

## [0.1.2] — 2026-05-03

### Changed

- **Подхвачен `ktav 0.1.5`** — в upstream Rust crate появился API
  структурированных ошибок (`Error::Structured(ErrorKind)` со
  span'ами в байтовых смещениях), retroactive `#[non_exhaustive]` на
  error-enum'ах и публичный event-based парсер `ktav::thin`. Поведение
  PyO3-биндинга, видимое пользователю, не меняется:
  `KtavDecodeError` / `KtavEncodeError` по-прежнему несут те же
  человекочитаемые сообщения (Display-строки для семи канонических
  категорий byte-identical к ktav 0.1.4). Маппинг `ktav::ErrorKind` на
  структурированную Python-иерархию исключений
  (`MissingSeparatorSpace`, `DuplicateKey` и т.д.) — отдельная
  follow-up задача, описанная в workspace'овском
  [`STRUCTURED_ERRORS.md`](https://github.com/ktav-lang/.github/blob/main/STRUCTURED_ERRORS.md).

PyPI: `ktav==0.1.2`.

>>>>> lang=zh

## [0.1.2] — 2026-05-03

### Changed

- **采用 `ktav 0.1.5`**——上游 Rust crate 引入了结构化错误 API
  (`Error::Structured(ErrorKind)`,带字节偏移 span)、对错误枚举追溯
  应用的 `#[non_exhaustive]`,以及公开的事件驱动解析器 `ktav::thin`。
  PyO3 绑定对用户可见的行为没有变化:`KtavDecodeError` /
  `KtavEncodeError` 仍携带相同的人类可读消息(七个标准类别的 Display
  字符串与 ktav 0.1.4 完全字节相同)。将 `ktav::ErrorKind` 映射到
  结构化的 Python 异常层级(`MissingSeparatorSpace`、`DuplicateKey`
  等)是单独的后续工作,记录在 workspace 的
  [`STRUCTURED_ERRORS.md`](https://github.com/ktav-lang/.github/blob/main/STRUCTURED_ERRORS.md)。

PyPI: `ktav==0.1.2`。

