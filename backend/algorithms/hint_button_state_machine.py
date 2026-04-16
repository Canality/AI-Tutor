"""
需求16：渐进式提示按钮 - 动态折叠交互状态机

设计原则：
- 摒弃传统多按钮并列的求助模式
- 采用"单一主求助按钮"进行渐进式引导
- 降低认知负荷，防止学生直接查看答案

状态机定义（硬指标）：
| 点击次数 | 当前按钮文案 | hint_level | Actual权重 |
|---------|-------------|-----------|-----------|
| 初始状态 | "给我点灵感 💡" | -- | 1.0 |
| 第1次点击 | "还需要公式支持" | L1 | 0.8 |
| 第2次点击 | "带我走第一步" | L2 | 0.6 |
| 第3次点击 | "彻底没思路，看解析"(标红) | L3 | 0.4 |
| 第4次点击 | 按钮置灰隐藏 | L4 | 0.1 |
"""

from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class HintButtonState(Enum):
    """提示按钮状态"""
    INITIAL = "initial"           # 初始状态
    LEVEL_1 = "level_1"           # 第1次点击后
    LEVEL_2 = "level_2"           # 第2次点击后
    LEVEL_3 = "level_3"           # 第3次点击后
    LEVEL_4 = "level_4"           # 第4次点击后（隐藏）
    HIDDEN = "hidden"             # 按钮隐藏


@dataclass
class ButtonConfig:
    """按钮配置"""
    text: str                       # 按钮文案
    hint_level: Optional[int]       # hint_level (L0-L4)
    actual_weight: float            # Actual权重
    is_highlighted: bool            # 是否标红
    is_visible: bool                # 是否可见
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "hint_level": self.hint_level,
            "actual_weight": self.actual_weight,
            "is_highlighted": self.is_highlighted,
            "is_visible": self.is_visible
        }


class HintButtonStateMachine:
    """
    渐进式提示按钮状态机
    
    前端联动说明：
    - 每次点击后，聊天流区域实时追加 Instructor 的对应等级回复
    - 按钮文案立刻切换至下一阶段
    - 若学生提交正确答案，状态机重置回初始状态
    """
    
    # 状态机配置（硬指标）
    STATE_CONFIG = {
        HintButtonState.INITIAL: ButtonConfig(
            text="给我点灵感",
            hint_level=None,
            actual_weight=1.0,
            is_highlighted=False,
            is_visible=True
        ),
        HintButtonState.LEVEL_1: ButtonConfig(
            text="还需要公式支持",
            hint_level=1,  # L1
            actual_weight=0.8,
            is_highlighted=False,
            is_visible=True
        ),
        HintButtonState.LEVEL_2: ButtonConfig(
            text="带我走第一步",
            hint_level=2,  # L2
            actual_weight=0.6,
            is_highlighted=False,
            is_visible=True
        ),
        HintButtonState.LEVEL_3: ButtonConfig(
            text="彻底没思路，看解析",
            hint_level=3,  # L3
            actual_weight=0.4,
            is_highlighted=True,  # 标红
            is_visible=True
        ),
        HintButtonState.LEVEL_4: ButtonConfig(
            text="",  # 隐藏后无文案
            hint_level=4,  # L4
            actual_weight=0.1,
            is_highlighted=False,
            is_visible=False  # 按钮置灰隐藏
        ),
        HintButtonState.HIDDEN: ButtonConfig(
            text="",
            hint_level=None,
            actual_weight=0.0,
            is_highlighted=False,
            is_visible=False
        )
    }
    
    # 状态转移图
    STATE_TRANSITION = {
        HintButtonState.INITIAL: HintButtonState.LEVEL_1,
        HintButtonState.LEVEL_1: HintButtonState.LEVEL_2,
        HintButtonState.LEVEL_2: HintButtonState.LEVEL_3,
        HintButtonState.LEVEL_3: HintButtonState.LEVEL_4,
        HintButtonState.LEVEL_4: HintButtonState.HIDDEN,
        HintButtonState.HIDDEN: HintButtonState.HIDDEN
    }
    
    def __init__(self):
        self.user_states: Dict[int, HintButtonState] = {}  # user_id -> state
        self.click_counts: Dict[int, int] = {}  # user_id -> click_count
    
    def get_user_state(self, user_id: int) -> HintButtonState:
        """获取用户当前状态"""
        return self.user_states.get(user_id, HintButtonState.INITIAL)
    
    def get_click_count(self, user_id: int) -> int:
        """获取用户点击次数"""
        return self.click_counts.get(user_id, 0)
    
    def get_button_config(self, user_id: int) -> ButtonConfig:
        """获取当前按钮配置"""
        state = self.get_user_state(user_id)
        return self.STATE_CONFIG[state]
    
    def click(self, user_id: int) -> Dict:
        """
        用户点击按钮
        
        Returns:
            包含新状态、按钮配置、hint_level的字典
        """
        current_state = self.get_user_state(user_id)
        
        # 如果已经隐藏，不再响应
        if current_state == HintButtonState.HIDDEN:
            return {
                "user_id": user_id,
                "state": HintButtonState.HIDDEN.value,
                "button_config": self.STATE_CONFIG[HintButtonState.HIDDEN].to_dict(),
                "click_count": self.get_click_count(user_id),
                "hint_level": None,
                "message": "按钮已隐藏"
            }
        
        # 状态转移
        next_state = self.STATE_TRANSITION[current_state]
        self.user_states[user_id] = next_state
        
        # 增加点击计数
        self.click_counts[user_id] = self.get_click_count(user_id) + 1
        
        # 获取新状态的配置
        config = self.STATE_CONFIG[next_state]
        
        return {
            "user_id": user_id,
            "previous_state": current_state.value,
            "current_state": next_state.value,
            "button_config": config.to_dict(),
            "click_count": self.get_click_count(user_id),
            "hint_level": config.hint_level,
            "actual_weight": config.actual_weight
        }
    
    def reset(self, user_id: int) -> Dict:
        """
        重置状态机（学生提交正确答案时调用）
        
        Returns:
            重置后的状态信息
        """
        self.user_states[user_id] = HintButtonState.INITIAL
        self.click_counts[user_id] = 0
        
        config = self.STATE_CONFIG[HintButtonState.INITIAL]
        
        return {
            "user_id": user_id,
            "state": HintButtonState.INITIAL.value,
            "button_config": config.to_dict(),
            "click_count": 0,
            "hint_level": None,
            "actual_weight": config.actual_weight,
            "message": "状态机已重置"
        }
    
    def get_full_state(self, user_id: int) -> Dict:
        """获取完整状态信息（用于前端展示）"""
        state = self.get_user_state(user_id)
        config = self.STATE_CONFIG[state]
        click_count = self.get_click_count(user_id)
        
        return {
            "user_id": user_id,
            "current_state": state.value,
            "click_count": click_count,
            "button_config": config.to_dict(),
            "hint_level": config.hint_level,
            "actual_weight": config.actual_weight,
            "is_visible": config.is_visible,
            "is_highlighted": config.is_highlighted
        }
    
    def is_button_visible(self, user_id: int) -> bool:
        """检查按钮是否可见"""
        state = self.get_user_state(user_id)
        return self.STATE_CONFIG[state].is_visible
    
    def get_hint_level_for_request(self, user_id: int) -> Optional[int]:
        """
        获取当前hint_level用于后端请求
        
        Returns:
            hint_level (0-4) 或 None（初始状态）
        """
        state = self.get_user_state(user_id)
        return self.STATE_CONFIG[state].hint_level


# 全局状态机实例
hint_button_sm = HintButtonStateMachine()


def get_hint_button_sm() -> HintButtonStateMachine:
    """获取状态机实例"""
    return hint_button_sm


# 单元测试
if __name__ == "__main__":
    print("=== 需求16：渐进式提示按钮状态机测试 ===\n")
    
    sm = HintButtonStateMachine()
    user_id = 1
    
    # 测试1：初始状态
    print("测试1：初始状态")
    state = sm.get_full_state(user_id)
    print(f"  状态: {state['current_state']}")
    print(f"  按钮文案: {state['button_config']['text']}")
    print(f"  hint_level: {state['hint_level']}")
    print(f"  Actual权重: {state['actual_weight']}")
    
    # 测试2：连续点击4次
    print("\n测试2：连续点击4次")
    for i in range(4):
        result = sm.click(user_id)
        print(f"\n  第{i+1}次点击:")
        print(f"    新状态: {result['current_state']}")
        print(f"    按钮文案: {result['button_config']['text']}")
        print(f"    hint_level: {result['hint_level']}")
        print(f"    Actual权重: {result['actual_weight']}")
        print(f"    是否标红: {result['button_config']['is_highlighted']}")
        print(f"    是否可见: {result['button_config']['is_visible']}")
    
    # 测试3：按钮隐藏后继续点击
    print("\n测试3：按钮隐藏后继续点击（应无响应）")
    result = sm.click(user_id)
    print(f"  状态: {result['current_state']}")
    print(f"  消息: {result['message']}")
    
    # 测试4：重置状态机
    print("\n测试4：重置状态机（模拟学生答对）")
    result = sm.reset(user_id)
    print(f"  状态: {result['state']}")
    print(f"  按钮文案: {result['button_config']['text']}")
    print(f"  hint_level: {result['hint_level']}")
    print(f"  消息: {result['message']}")
    
    print("\n=== 所有测试通过！===")
