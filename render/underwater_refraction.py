"""水下折射：深度、相机与后处理顺序：待实现的核心模块。"""

from __future__ import annotations


def refraction_offset(uv, normal, depth, strength):
    """按深度衰减的屏幕折射偏移。"""
    raise NotImplementedError

def caustic_uv(uv, time_s, speed):
    """按秒驱动的焦散 UV 动画。"""
    raise NotImplementedError

def water_normal(dx, dy, strength):
    """由高度梯度生成归一化水面法线。"""
    raise NotImplementedError

def refract_visible(scene_depth, water_depth, refracted_depth):
    """折射采样是否被场景遮挡。"""
    raise NotImplementedError

def wait_compute(write_tick, read_tick):
    """compute 写入是否已对读取可见。"""
    raise NotImplementedError

def pass_order(name):
    """后处理 pass 的固定顺序。"""
    raise NotImplementedError

def caustic_intensity(base, width, height, ref_w=1920, ref_h=1080):
    """按像素数归一的焦散强度。"""
    raise NotImplementedError

def reject_water_depth(scene_depth, water_depth, bias=0.01):
    """剔除水面自身深度。"""
    raise NotImplementedError

def reflection_depth(recursion, max_depth):
    """反射递归是否允许继续。"""
    raise NotImplementedError

def split_water_color(color, tint):
    """拆出水下雾色与焦散色，返回 6 元组。"""
    raise NotImplementedError

def snell_refract(eta, cos_i):
    """Snell 折射，返回 (cos_t, total_internal_reflection)。"""
    raise NotImplementedError

def caustic_phase(time_s, speed, period=1.0):
    """焦散相位循环。"""
    raise NotImplementedError

def normal_key(camera_id, view_id):
    """水面法线的相机隔离键。"""
    raise NotImplementedError

def composite_order(kind):
    """物体类型的水下合成顺序。"""
    raise NotImplementedError

def underwater_tint(caustic, fog, fog_weight):
    """按雾权重混合焦散与雾色。"""
    raise NotImplementedError
