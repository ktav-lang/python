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

