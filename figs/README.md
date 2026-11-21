# 小论文图件

三张图由 `make_figs.py` 生成，**图内标签为英文、Arial**，输出为 SVG（矢量）与 PDF（Edge headless 打印，190 mm 宽）。

- `fig1_pipeline.svg`：事件级注入与处理暴露核验流程（示意图）。
- `fig2_support.svg`：内容回放窗内有效内点数；数据来自 `第4-5章_判别与恢复/f_stage/pull/<tag>/safety_risk.csv`。
- `fig3_output_hold.svg`：在线输出弃权的发布包络（对数轴）；数据来自 `第4-5章_判别与恢复/a_stage/a_results.csv`。

重新生成 SVG：

```bash
PYTHONIOENCODING=utf-8 python 论文部分/figs/make_figs.py
```

注意：脚本只依赖标准库；不依赖 matplotlib。图 2 的基线带取同一运行 `t<29 s` 或 `t>33 s` 的四分位区间，阴影为 `[30,32)` s 注入窗。图 3 中 B 组未恢复，包络仍为 5.3 m，不能解读为输出弃权生效。
