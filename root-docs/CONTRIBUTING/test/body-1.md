>>>>> lang=en
### Test

```
make test                          # full suite
pytest -v -k multiline             # filter by name
pytest -v tests/parse/test_loads.py  # single file
```

The `test_conformance.py` module runs the cross-language fixture suite
from `ktav-lang/spec`, hardcoded at `<repo>/spec/versions/0.8/tests`
(the `spec` git submodule). When the submodule is unpopulated,
conformance tests **skip** rather than fail.

The conformance suite is parametrized over both backends: the same
fixtures run against the native extension and against `ktav.pure`. CI
additionally runs a dedicated `pure-mode` job that builds the pure
wheel from `packaging/pure` and installs it into a fresh venv
(`KTAV_REQUIRE_PURE=1`;
`tests/conftest.py` fails the job if `ktav._core` is importable) and
drives the installed package through the full corpus via
`scripts/check_installed_pure.py`.

>>>>> lang=ru
### Тесты

```
make test                          # full suite
pytest -v -k multiline             # filter by name
pytest -v tests/parse/test_loads.py  # single file
```

Модуль `test_conformance.py` запускает набор кросс-языковых фикстур
из `ktav-lang/spec`, путь захардкожен как `<repo>/spec/versions/0.8/tests`
(git submodule `spec`). Когда submodule не подтянут,
conformance-тесты **пропускаются**, а не падают.

Conformance-набор параметризован по обоим backend-ам: одни и те же
fixtures прогоняются и через нативное расширение, и через `ktav.pure`.
CI дополнительно запускает отдельную job `pure-mode`, которая собирает
pure wheel из `packaging/pure` и ставит его в свежий venv
(`KTAV_REQUIRE_PURE=1`;
`tests/conftest.py` роняет job, если `ktav._core` импортируется) и
прогоняет установленный пакет через весь корпус скриптом
`scripts/check_installed_pure.py`.

>>>>> lang=zh
### 测试

```
make test                          # full suite
pytest -v -k multiline             # filter by name
pytest -v tests/parse/test_loads.py  # single file
```

`test_conformance.py` 模块运行来自 `ktav-lang/spec` 的跨语言夹具套件，
路径硬编码为 `<repo>/spec/versions/0.8/tests`（git submodule `spec`）。
当 submodule 未填充时，一致性测试会**跳过**而非失败。

一致性测试套件按两个 backend 参数化：同一批 fixtures 会分别通过原生
扩展和 `ktav.pure` 运行。CI 另外运行一个专门的 `pure-mode` job，先从
`packaging/pure` 构建纯 wheel 并安装到全新 venv（`KTAV_REQUIRE_PURE=1`；若 `ktav._core`
可导入，`tests/conftest.py` 会让该 job 失败），并通过
`scripts/check_installed_pure.py` 用完整语料库驱动已安装的包。

