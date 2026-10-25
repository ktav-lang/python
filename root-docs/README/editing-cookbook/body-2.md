>>>>> lang=en
#### 2. Literal dots: textual path or segments

The quoted source key is literally `a.b`. The textual path escapes its dot; the segments call passes the decoded key directly. Both calls return the same result.

```python
source = "\"a.b\": {port: 80}\n"
updated = ktav.edit_value(source, "a\\.b.port", 90)
same = ktav.edit_value_segments(source, ["a.b", "port"], 90)
```

Result:

```ktav
"a.b": {port: 90}
```

#### 3. A leaf inside a mixed-form array

`0` is an array index here. Inside an Object, the same segment would address the key named `0`; untouched containers remain inline.

```python
source = "servers: [{host: old, keep: yes}, standby]\n"
updated = ktav.edit_value_segments(source, ["servers", "0", "host"], "new")
```

Result:

>>>>> lang=ru
#### 2. Буквальные точки: текстовый путь или сегменты

Ключ исходника в кавычках буквально называется `a.b`. В текстовом пути точка экранируется; API сегментов получает декодированное имя напрямую. Оба вызова возвращают одинаковый результат.

```python
source = "\"a.b\": {port: 80}\n"
updated = ktav.edit_value(source, "a\\.b.port", 90)
same = ktav.edit_value_segments(source, ["a.b", "port"], 90)
```

Результат:

```ktav
"a.b": {port: 90}
```

#### 3. Лист внутри массива со смешанными формами

Здесь `0` — индекс массива. В объекте такой же сегмент обозначал бы ключ с именем `0`; нетронутые контейнеры остаются inline.

```python
source = "servers: [{host: old, keep: yes}, standby]\n"
updated = ktav.edit_value_segments(source, ["servers", "0", "host"], "new")
```

Результат:

>>>>> lang=zh
#### 2. 字面点号：文本路径或路径段

源码中带引号的键名就是 `a.b`。文本路径需要转义点号；路径段 API 直接接收解码后的键名。两个调用返回相同结果。

```python
source = "\"a.b\": {port: 80}\n"
updated = ktav.edit_value(source, "a\\.b.port", 90)
same = ktav.edit_value_segments(source, ["a.b", "port"], 90)
```

结果:

```ktav
"a.b": {port: 90}
```

#### 3. 修改混合形式数组中的叶子值

此处 `0` 是数组索引；在对象中，同一个路径段表示名称为 `0` 的键。未修改的容器保持行内形式。

```python
source = "servers: [{host: old, keep: yes}, standby]\n"
updated = ktav.edit_value_segments(source, ["servers", "0", "host"], "new")
```

结果:

