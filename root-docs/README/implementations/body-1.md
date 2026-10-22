>>>>> lang=en
## Other Ktav implementations

- [`spec`](https://github.com/ktav-lang/spec) — specification + conformance suite
- [`rust`](https://github.com/ktav-lang/rust) — reference Rust crate (`cargo add ktav`); these Python bindings are a thin PyO3 wrapper around it
- [`csharp`](https://github.com/ktav-lang/csharp) — C# / .NET (`dotnet add package Ktav`)
- [`golang`](https://github.com/ktav-lang/golang) — Go (`go get github.com/ktav-lang/golang`)
- [`java`](https://github.com/ktav-lang/java) — Java / JVM (`io.github.ktav-lang:ktav` on Maven Central)
- [`js`](https://github.com/ktav-lang/js) — JS / TS (`npm install @ktav-lang/ktav`)
- [`php`](https://github.com/ktav-lang/php) — PHP (`composer require ktav-lang/ktav`)

Two backends ship in this package. The **native** backend is the
default: the top-level `ktav` API is a thin PyO3 wrapper around the
Rust core (0.8.1). The **pure** backend, `ktav.pure`, is a complete
parser and generator in pure Python — no compiled extension required.
There is no global backend flag and no silent fallback: you choose a
backend by importing it, and CI asserts byte-identical canonical
output across both. The pure backend also ships as the universal pure
wheel (`ktav-0.8.1-py3-none-any.whl`), published alongside the native
platform wheels.

>>>>> lang=ru
## Другие реализации Ktav

- [`spec`](https://github.com/ktav-lang/spec) — спецификация + conformance-тесты
- [`rust`](https://github.com/ktav-lang/rust) — эталонный Rust crate (`cargo add ktav`); этот Python-биндинг — тонкая PyO3-обёртка над ним
- [`csharp`](https://github.com/ktav-lang/csharp) — C# / .NET (`dotnet add package Ktav`)
- [`golang`](https://github.com/ktav-lang/golang) — Go (`go get github.com/ktav-lang/golang`)
- [`java`](https://github.com/ktav-lang/java) — Java / JVM (`io.github.ktav-lang:ktav` на Maven Central)
- [`js`](https://github.com/ktav-lang/js) — JS / TS (`npm install @ktav-lang/ktav`)
- [`php`](https://github.com/ktav-lang/php) — PHP (`composer require ktav-lang/ktav`)

В этот пакет входят два backend-а. **Нативный** — по умолчанию:
API верхнего уровня `ktav` — это тонкая PyO3-обёртка над Rust-ядром
(0.8.1). **Чистый** backend, `ktav.pure`, — полноценные парсер и
генератор на чистом Python, без скомпилированного расширения.
Глобального флага выбора backend нет, тихого fallback тоже нет:
backend выбирается импортом, а CI проверяет побайтовую идентичность
канонического вывода обоих. Чистый backend поставляется также в виде
универсального pure wheel (`ktav-0.8.1-py3-none-any.whl`),
публикуемого рядом с нативными платформенными wheel-ами.

>>>>> lang=zh
## 其他 Ktav 实现

- [`spec`](https://github.com/ktav-lang/spec) —— 规范 + 一致性测试套件
- [`rust`](https://github.com/ktav-lang/rust) —— 参考 Rust crate (`cargo add ktav`)；本 Python 绑定是包在其外的薄 PyO3 包装
- [`csharp`](https://github.com/ktav-lang/csharp) —— C# / .NET (`dotnet add package Ktav`)
- [`golang`](https://github.com/ktav-lang/golang) —— Go (`go get github.com/ktav-lang/golang`)
- [`java`](https://github.com/ktav-lang/java) —— Java / JVM（`io.github.ktav-lang:ktav`，Maven Central）
- [`js`](https://github.com/ktav-lang/js) —— JS / TS (`npm install @ktav-lang/ktav`)
- [`php`](https://github.com/ktav-lang/php) —— PHP (`composer require ktav-lang/ktav`)

本包内置两个 backend。**原生** backend 是默认项：顶层 `ktav` API 是
包在 Rust 核心（0.8.1）外的薄 PyO3 包装。**纯** backend `ktav.pure`
则是纯 Python 实现的完整解析器与生成器，无需编译扩展。没有全局
backend 开关，也没有静默回退：导入哪个模块就选用哪个 backend，CI
会断言两个 backend 的规范输出字节完全一致。纯 backend 同时也以通用纯
wheel（`ktav-0.8.1-py3-none-any.whl`）的形式发布，与各原生平台 wheel
一同上线。

