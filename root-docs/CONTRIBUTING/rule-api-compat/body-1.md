>>>>> lang=en
### 3. Public API changes note compatibility

If you touch anything exported from `ktav` or `ktav._core`, say in the
PR description whether it is:

- **semver-compatible** (additions, looser types, doc changes); or
- **semver-breaking** (renamed / removed items, changed signatures,
  tightened types) — in which case the version bump lands in the next
  MINOR while we are pre-1.0.

Update the CHANGELOG source units under `root-docs/CHANGELOG/` (all
three `>>>>> lang=` blocks) in the same PR and regenerate the output.

>>>>> lang=ru
### 3. Изменения публичного API указывают совместимость

Если вы трогаете что-то экспортируемое из `ktav` или `ktav._core`, в
описании PR укажите, является ли это:

- **semver-совместимым** (добавления, ослабленные типы, правки
  документации); или
- **semver-ломающим** (переименование / удаление, изменение сигнатур,
  ужесточение типов) — в этом случае бамп версии попадёт в следующий
  MINOR, пока мы до 1.0.

Обновите CHANGELOG-юниты под `root-docs/CHANGELOG/` (все три блока
`>>>>> lang=`) в том же PR и перегенерируйте вывод.

>>>>> lang=zh
### 3. 公开 API 的变更注明兼容性

如果你改动 `ktav` 或 `ktav._core` 导出的任何内容，请在 PR 描述中说明它
属于：

- **semver 兼容**（新增、更宽松的类型、文档改动）；或
- **semver 破坏**（重命名 / 移除、签名变更、类型收紧）——
  这种情况下版本 bump 会落在下一个 MINOR，毕竟我们还在 1.0 之前。

在同一个 PR 中更新 `root-docs/CHANGELOG/` 下的 CHANGELOG 源单元
(全部三个 `>>>>> lang=` 块)并重新生成产物。

