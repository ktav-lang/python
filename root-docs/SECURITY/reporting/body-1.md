>>>>> lang=en
## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Email **phpcraftdream@gmail.com** with:

- A short description of the vulnerability.
- Steps or a snippet to reproduce it (Ktav input that triggers the
  behaviour, the affected API — `loads` / `dumps` / file variants,
  expected vs actual).
- The ktav version you observed it on (`pip show ktav` output is
  usually enough), plus the OS / Python version so we know which
  abi3 wheel was in use.
- Your disclosure timeline preference, if you have one.

You should get an acknowledgement within **72 hours**. A published
fix typically follows within **a week** for high-impact issues, longer
if the fix needs to coordinate with the Rust crate or the format spec.

>>>>> lang=ru
## Сообщение об уязвимости

**Пожалуйста, не открывайте публичный issue по проблемам безопасности.**

Напишите на **phpcraftdream@gmail.com** и укажите:

- Краткое описание уязвимости.
- Шаги или фрагмент для воспроизведения (вход Ktav, запускающий
  поведение, затронутый API — `loads` / `dumps` / файловые варианты,
  ожидаемое против фактического).
- Версию, на которой вы наблюдали проблему (обычно достаточно вывода
  `pip show ktav`), плюс версию OS / Python — чтобы понять, какой
  abi3-wheel использовался.
- Предпочитаемый таймлайн раскрытия, если он у вас есть.

Подтверждение вы получите в течение **72 часов**. Опубликованный фикс
обычно следует в течение **недели** для высокоприоритетных проблем,
дольше — если фикс нужно согласовать с Rust-крейтом или со спецификацией
формата.

>>>>> lang=zh
## 上报漏洞

**请不要为安全问题开公开 issue。**

请发邮件至 **phpcraftdream@gmail.com**，并提供：

- 对漏洞的简短描述。
- 复现步骤或代码片段（触发该行为的 Ktav 输入、受影响的 API ——
  `loads` / `dumps` / 文件变体，预期与实际）。
- 观察到问题时所用的版本（通常 `pip show ktav` 的输出就够了），
  以及 OS / Python 版本 —— 以便确认当时用的是哪个 abi3 wheel。
- 你偏好的披露时间线（如有）。

你应在 **72 小时**内收到确认。对于高影响问题，已发布的修复通常在
**一周**内跟进；若修复需要与 Rust crate 或格式规范协同推进，则可能
更久。

