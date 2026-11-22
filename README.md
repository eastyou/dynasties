# dynasties

[![CI](https://github.com/eastyou/dynasties/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/dynasties/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

中国朝代时间轴：内置 19 个朝代 / 时期，按真实年代比例生成可打印的 SVG / HTML 时间轴，并可生成四选一测验、朝代排序和配对练习，适合历史课堂与自学使用。仅依赖 Python 标准库。

## 功能

- **朝代数据**：夏、商、西周、东周、秦、西汉、东汉、三国、西晋、东晋、南北朝、隋、唐、五代十国、北宋、南宋、元、明、清，共 19 项；每项含起止年份、都城、开国君主、代表成就与别名。
- **年代查询**：按名称 / 别名查详情，按年份定位朝代（过渡年归入新朝代），计算国祚。
- **时间轴**：`timeline_svg()` 按真实年代比例绘制横向色块，标签自动错行；`timeline_html()` 额外输出明细表，带 A4 打印样式。
- **练习生成**：四选一测验（都城 / 开国君主 / 起止年代）、4～5 个朝代的排序题、朝代—成就 / 都城配对题，均支持随机种子复现。
- **CLI 导出**：一条命令生成可直接打开、打印的 HTML 页面。

## 安装

需要 Python 3.9 或更高版本。

```bash
git clone https://github.com/eastyou/dynasties.git
cd dynasties
python -m pip install -e .
```

也可以不安装，直接在仓库根目录用 `python -m dynasties` 运行。

## CLI 示例

```bash
dynasties info 唐
```

```text
名称：唐
别名：唐朝、大唐
起止：618 年 — 907 年
持续时间：290 年（含首尾年份）
都城：长安（今陕西西安）
开国君主：李渊
代表成就：贞观之治与开元盛世，文化开放、商贸繁荣。
```

```bash
dynasties year 1000
```

```text
公元 1000 年：北宋（960 年 — 1127 年），都城：东京开封府（今河南开封），开国君主：赵匡胤。
```

```bash
dynasties span 唐
dynasties list
dynasties quiz --count 10 --seed 5 -o examples/quiz.html
dynasties ordering --count 8 --seed 3 -o examples/ordering.html
dynasties match --count 8 --seed 4 -o examples/match.html
dynasties timeline -o examples/timeline.html
```

导出命令会打印 `已生成：<路径>`。不带 `-o` 时直接输出到终端（`timeline` 输出 SVG）。

## 库用法

```python
from dynasties import all_dynasties, at_year, find_dynasty, format_years, span
from dynasties.render import timeline_html, timeline_svg

tang = find_dynasty("大唐")
print(tang.capital)                 # 长安（今陕西西安）
print(format_years(-221, -207))     # 公元前 221 年 — 公元前 207 年
print(at_year(1000).name)           # 北宋
print(span("唐"))                    # 290

print(len(all_dynasties()))         # 19
print(timeline_svg()[0:60])         # <svg xmlns=...
html = timeline_html(all_dynasties(), "中国朝代时间轴")
```

题目生成器返回结构化字典，可直接渲染或自行处理：

```python
from dynasties import match_items, ordering_items, quiz_items

quiz_items(10, seed=5)       # 四选一：question / options / answer_index / answer / explanation
ordering_items(8, seed=3)    # 排序：shuffled / answer / explanation
match_items(8, seed=4)       # 配对：[(朝代, 成就或都城), ...]
```

## 示例页面

- [朝代时间轴](examples/timeline.html)
- [四选一测验（含答案）](examples/quiz.html)
- [朝代排序练习（含答案）](examples/ordering.html)
- [朝代配对练习（含答案）](examples/match.html)

以上页面均由 CLI 真实生成，可浏览器打开或直接打印为 A4。

## 测试

项目使用标准库 `unittest`，共 **189** 个测试用例，覆盖数据校验、年份定位、题目生成、HTML 转义、打印样式、文件导出与错误处理。

```bash
/usr/bin/python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests -v
```

实测结果：

| 解释器 | 版本 | 结果 |
| --- | --- | --- |
| `/usr/bin/python3` | 3.9.6 | 运行 189 个测试，全部通过（OK） |
| `python3` | 3.15.2 | 运行 189 个测试，全部通过（OK） |

## 许可

MIT © 2026 eastyou
