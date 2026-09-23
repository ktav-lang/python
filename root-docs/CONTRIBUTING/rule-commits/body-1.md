>>>>> lang=en
### 4. One concept per commit

Commits should be atomic: a bug fix and its test together, a feature
and its tests together, a rename on its own, a refactor on its own.
`git log --oneline` should read like a changelog. Don't prefix commit
messages with `feat:` / `fix:` — no conventional commits here.

>>>>> lang=ru
### 4. Одна концепция — один коммит

Коммиты атомарны: багфикс и его тест вместе, фича и её тесты вместе,
переименование отдельным коммитом, рефакторинг отдельным.
`git log --oneline` должен читаться как журнал изменений. Не
префиксуйте сообщения `feat:` / `fix:` — никаких conventional commits
здесь.

>>>>> lang=zh
### 4. 一个概念一个提交

提交应当原子化：bug 修复与其测试放在一起，功能与其测试放在一起，
重命名单独一次提交，重构单独一次提交。`git log --oneline`
读起来应像变更日志。不要给提交消息加 `feat:` / `fix:` 前缀 ——
这里不用 conventional commits。

