# 水下折射：深度、相机与后处理顺序

深水折射过头、焦散按帧推进、分屏法线不一致、折射穿过角色、compute 写入与后处理竞争、气泡被焦散盖住。本仓库固定水下合成的时序与数值。

- 领域：游戏、图形与多媒体
- 子方向：图形渲染
- 语言/框架：Python 3, pytest
- 初始状态：15 个参数化用例全部失败

## 目录结构

```
README.md
conftest.py
.gitignore
render/__init__.py
render/underwater_refraction.py
tests/test_underwater_refraction.py
```

## 需要修复的 10 个问题

1. 折射偏移按相机到水面距离衰减，深水不过度偏移
2. 焦散贴图按秒推进，帧率变化不改变动画速度
3. 水面法线按相机与视口分别生成，分屏法线一致
4. 折射光线做深度遮挡，不穿过角色
5. 焦散 compute 写入与后处理读取同帧同步
6. 后处理顺序固定为焦散在透明物体之前，气泡不被覆盖
7. 焦散强度按分辨率归一，窗口拉伸后亮度不漂移
8. 深度读取剔除水面自身，避免自折射
9. 平面反射相机与水下相机递归保护
10. 水下雾与焦散颜色分离，避免叠加偏青

## 15 条验收契约

    01. depth scaled refraction — `refraction_offset`
    02. time driven caustic — `caustic_uv`
    03. water normal normalized — `water_normal`
    04. refraction occluded — `refract_visible`
    05. compute read sync — `wait_compute`
    06. transparent after caustic — `pass_order`
    07. resolution independent caustic — `caustic_intensity`
    08. water self depth rejected — `reject_water_depth`
    09. reflection recursion guard — `reflection_depth`
    10. split fog and caustic — `split_water_color`
    11. snell refraction — `snell_refract`
    12. caustic phase wrap — `caustic_phase`
    13. water normal camera key — `normal_key`
    14. bubble composite order — `composite_order`
    15. separated underwater tint — `underwater_tint`

## 当前状态

`render/underwater_refraction.py` 只保留函数签名与文档字符串，所有函数体统一
`raise NotImplementedError`。`tests/test_underwater_refraction.py` 使用一个
`@pytest.mark.parametrize` 装载 15 条契约，初始全部失败且没有 collection error。

```bash
python -m pytest -q
```

预期输出包含 `15 failed`。实现 `render/underwater_refraction.py` 后，15 条契约应全部通过。
