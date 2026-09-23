>>>>> lang=en
### 2. Don't reinvent the format in the bindings

These Python bindings are deliberately a thin wrapper. Parser / format
behaviour belongs in the Rust crate
([`ktav-lang/rust`](https://github.com/ktav-lang/rust)) — changing it
there updates every language binding at once. Only **Python-specific
ergonomics** (file-like wrappers, exception types, type stubs) belong
in this repo.

If your change requires a format change, start a discussion in
[`ktav-lang/spec`](https://github.com/ktav-lang/spec) first.

>>>>> lang=ru
### 2. Не изобретайте формат заново в биндингах

Эти Python-биндинги — намеренно тонкая обёртка. Поведение парсера и
формата принадлежит Rust-крейту
([`ktav-lang/rust`](https://github.com/ktav-lang/rust)) — изменение
там сразу обновляет все языковые биндинги. В этом репозитории живёт
только **Python-специфичная эргономика** (обёртки под файл-подобные
объекты, типы исключений, заглушки типов).

Если ваше изменение требует правки формата, начните с обсуждения в
[`ktav-lang/spec`](https://github.com/ktav-lang/spec).

>>>>> lang=zh
### 2. 不要在绑定层重新发明格式

这些 Python 绑定**有意**做成薄包装。解析器 / 格式行为属于 Rust crate
([`ktav-lang/rust`](https://github.com/ktav-lang/rust)) ——
在那里修改一次即可同时更新所有语言绑定。只有 **Python 特有的人体工学**
（类文件包装、异常类型、类型存根）才属于本仓库。

如果你的改动需要修改格式，请先去
[`ktav-lang/spec`](https://github.com/ktav-lang/spec) 发起讨论。

