"""水下折射：深度、相机与后处理顺序。

本模块固定水下合成的时序与数值，对应十个修复点：

1. 折射偏移按相机到水面的距离（水深）衰减，深水不过度偏移；
2. 焦散贴图按秒推进，帧率变化不改变动画速度；
3. 水面法线按相机/视口隔离生成，分屏两个视口各自一致；
4. 折射光线做深度遮挡，不穿过角色等前景物体；
5. 焦散 compute 写入与后处理读取同帧同步，杜绝空纹理；
6. 后处理顺序固定，焦散在透明物体之前，气泡不被覆盖；
7. 焦散强度按像素数归一，窗口拉伸后亮度不漂移；
8. 深度读取剔除水面自身，避免自折射；
9. 平面反射相机与水下相机递归保护；
10. 水下雾色与焦散色分离，避免叠加偏青。
"""

from __future__ import annotations

import math

# 固定的水下后处理/合成顺序：数值小的先执行。
# 焦散(10) 在透明物体(20) 之前，气泡(30) 在最后合成，因此不会被焦散盖住。
_PASS_ORDER = {
    "opaque": 0,
    "caustic": 10,
    "transparent": 20,
    "bubble": 30,
    "post": 40,
}


def refraction_offset(uv, normal, depth, strength):
    """按深度衰减的屏幕折射偏移。

    偏移量与法线、强度成正比，并除以 ``1 + depth``：相机到水面的距离
    越大（深水），同样法线造成的屏幕 UV 偏移越小，避免深水处折射过头。
    """
    u, v = uv
    nx, ny = normal
    scale = strength / (1.0 + depth)
    return (u + nx * scale, v + ny * scale)


def caustic_uv(uv, time_s, speed):
    """按秒驱动的焦散 UV 动画。

    位移只依赖流逝的秒数与速度，与帧数/帧率无关；v 方向以半速滚动，
    形成两层焦散交错的观感。
    """
    u, v = uv
    drift = time_s * speed
    return (u + drift, v + 0.5 * drift)


def water_normal(dx, dy, strength):
    """由高度梯度生成归一化水面法线。

    梯度按强度缩放后取负作为 xy 分量，z 分量朝上并整体归一化。
    每个相机/视口用各自的高度场调用本函数，再配合 :func:`normal_key`
    隔离缓存，分屏时两个视口不会共用同一份法线。
    """
    nx = -dx * strength
    ny = -dy * strength
    nz = 1.0
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    return (nx / length, ny / length, nz / length)


def refract_visible(scene_depth, water_depth, refracted_depth):
    """折射采样是否被场景遮挡。

    折射命中点（``refracted_depth``）必须位于水面之后；若场景深度
    （角色等前景）比折射命中点更近，说明折射光线在到达目标前被挡住，
    返回 ``False``，角色身上不会出现水波。
    """
    if refracted_depth <= water_depth:
        return False
    return scene_depth >= refracted_depth


def wait_compute(write_tick, read_tick):
    """compute 写入是否已对读取可见。

    只有读取方见到的 tick 不小于写入方完成的 tick 时，compute 产物
    才对后处理可见；否则后处理必须等待，避免读到空纹理。
    """
    return read_tick >= write_tick


def pass_order(name):
    """后处理 pass 的固定顺序（数值小者先执行）。"""
    return _PASS_ORDER[name]


def caustic_intensity(base, width, height, ref_w=1920, ref_h=1080):
    """按像素数归一的焦散强度。

    以参考分辨率的像素数为基准缩放，分辨率升高时强度同比下降，
    窗口拉伸后总能量（亮度）保持不漂移。
    """
    reference_pixels = ref_w * ref_h
    current_pixels = width * height
    return base * reference_pixels / current_pixels


def reject_water_depth(scene_depth, water_depth, bias=0.01):
    """剔除水面自身深度。

    场景深度落在水面深度的绝对+相对容差区间
    ``[water_depth - bias*(1+|water_depth|), water_depth + ...]``
    之内时视为水面自身，返回 ``True`` 予以剔除，避免水面采样到
    自己造成自折射。直接比较边界可避开近邻深度相减的浮点相消。
    """
    tolerance = bias * (1.0 + abs(water_depth))
    return water_depth - tolerance <= scene_depth <= water_depth + tolerance


def reflection_depth(recursion, max_depth):
    """反射递归是否允许继续。

    当前递归深度达到上限即停止，防止平面反射相机与水下相机互相
    递归渲染。
    """
    return recursion < max_depth


def split_water_color(color, tint):
    """拆出水下雾色与焦散色，返回 6 元组。

    ``tint`` 作为焦散分光比例：焦散色为 ``color * tint``，雾色为
    ``color * (1 - tint)``，二者独立返回（先雾后焦散），不再叠加成
    偏青的混合色。
    """
    fog = tuple(c * (1.0 - t) for c, t in zip(color, tint))
    caustic = tuple(c * t for c, t in zip(color, tint))
    return fog + caustic


def snell_refract(eta, cos_i):
    """Snell 折射，返回 (cos_t, total_internal_reflection)。

    ``eta`` 为透射侧与入射侧折射率之比。``sin²t > 1`` 时发生全反射，
    返回 ``(0.0, True)``；否则返回折射角余弦。
    """
    sin2_t = eta * eta * (1.0 - cos_i * cos_i)
    if sin2_t > 1.0:
        return 0.0, True
    return math.sqrt(1.0 - sin2_t), False


def caustic_phase(time_s, speed, period=1.0):
    """焦散相位循环。

    相位按秒推进并对周期取模，帧率变化只影响采样密度，不影响
    动画速度与循环周期。
    """
    return (time_s * speed) % period


def normal_key(camera_id, view_id):
    """水面法线的相机隔离键。

    不同相机、不同视口的法线缓存以 ``camera_id:view_id`` 区分，
    分屏左右视口不会互相覆盖法线。
    """
    return f"{camera_id}:{view_id}"


def composite_order(kind):
    """物体类型的水下合成顺序（数值小者先合成）。"""
    return _PASS_ORDER[kind]


def underwater_tint(caustic, fog, fog_weight):
    """按雾权重混合焦散与雾色。

    雾色与焦散色先在 :func:`split_water_color` 中分离，再按雾权重
    线性混合：``fog * w + caustic * (1 - w)``，保证水下色调可控、
    不会因叠加偏青。
    """
    return fog * fog_weight + caustic * (1.0 - fog_weight)
