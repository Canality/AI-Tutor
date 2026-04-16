"""
需求1 API测试脚本
测试连击状态与难度自适应调整功能
"""

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import json

BASE_URL = "http://localhost:8000"


def test_streak_update():
    if not HAS_REQUESTS:
        print("requests模块未安装，跳过API测试")
        return
    """测试连击状态更新API"""
    print("=== 测试需求1：连击状态更新API ===\n")
    
    user_id = 999  # 测试用户
    knowledge_point_id = 101
    
    # 测试1：连续答对3次（触发高光连击）
    print("测试1：连续答对3次（应触发高光连击）")
    for i in range(3):
        response = requests.post(
            f"{BASE_URL}/api/cognitive/streak/update",
            json={
                "user_id": user_id,
                "knowledge_point_id": knowledge_point_id,
                "is_correct": True
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  第{i+1}次答对:")
            print(f"    掌握度: {data['p_known']:.4f} (变化: {data['p_known_change']:+.4f})")
            print(f"    连对次数: {data['consecutive_correct']}")
            print(f"    难度范围: {data['difficulty_adjustment']['adjusted_range']}")
            
            if data['should_trigger_effect']:
                print(f"    -> 触发UI效果: {data['ui_effect']['icon']}")
                print(f"       Advisor话术: {data['ui_effect']['advisor_message']}")
        else:
            print(f"  错误: {response.status_code} - {response.text}")
    
    # 重置连击状态
    print("\n重置连击状态...")
    requests.post(f"{BASE_URL}/api/cognitive/streak/reset/{user_id}")
    
    # 测试2：连续答错2次（触发降级保护）
    print("\n测试2：连续答错2次（应触发降级保护）")
    for i in range(2):
        response = requests.post(
            f"{BASE_URL}/api/cognitive/streak/update",
            json={
                "user_id": user_id,
                "knowledge_point_id": knowledge_point_id,
                "is_correct": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  第{i+1}次答错:")
            print(f"    掌握度: {data['p_known']:.4f} (变化: {data['p_known_change']:+.4f})")
            print(f"    连错次数: {data['consecutive_wrong']}")
            print(f"    难度范围: {data['difficulty_adjustment']['adjusted_range']}")
            
            if data['should_trigger_effect']:
                print(f"    -> 触发UI效果: {data['ui_effect']['icon']}")
                print(f"       Advisor话术: {data['ui_effect']['advisor_message']}")
        else:
            print(f"  错误: {response.status_code} - {response.text}")
    
    # 重置连击状态
    print("\n重置连击状态...")
    requests.post(f"{BASE_URL}/api/cognitive/streak/reset/{user_id}")
    
    # 测试3：混合答题（对-对-错-对-对-对）
    print("\n测试3：混合答题（对-对-错-对-对-对）")
    answers = [True, True, False, True, True, True]
    for i, is_correct in enumerate(answers):
        response = requests.post(
            f"{BASE_URL}/api/cognitive/streak/update",
            json={
                "user_id": user_id,
                "knowledge_point_id": knowledge_point_id,
                "is_correct": is_correct
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            status = "答对" if is_correct else "答错"
            print(f"  第{i+1}次{status}: 连对={data['consecutive_correct']}, 连错={data['consecutive_wrong']}")
            
            if data['should_trigger_effect']:
                print(f"    -> 触发效果: {data['ui_effect']['effect_type']}")


def test_get_streak_state():
    if not HAS_REQUESTS:
        print("requests模块未安装，跳过API测试")
        return
    """测试获取连击状态API"""
    print("\n=== 测试获取连击状态API ===\n")
    
    user_id = 999
    
    response = requests.get(f"{BASE_URL}/api/cognitive/streak/state/{user_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"用户 {user_id} 的连击状态:")
        print(f"  连续正确: {data['consecutive_correct']}")
        print(f"  连续错误: {data['consecutive_wrong']}")
        print(f"  当前连击类型: {data['current_streak_type']}")
        print(f"  当前连击计数: {data['current_streak_count']}")
    else:
        print(f"错误: {response.status_code} - {response.text}")


def test_algorithm_directly():
    """直接测试算法模块"""
    print("\n=== 直接测试算法模块 ===\n")
    
    from algorithms.streak_handler import StreakHandler, StreakEffect
    
    handler = StreakHandler()
    user_id = 888
    theta = 0.5  # 学生能力值
    
    # 测试高光连击
    print("测试高光连击（连续正确3次）")
    for i in range(3):
        result = handler.process_answer(user_id, True, theta)
        print(f"  第{i+1}次:")
        print(f"    连对: {result['streak_state']['consecutive_correct']}")
        print(f"    难度范围: {result['difficulty_adjustment']['adjusted_range']}")
        if result['should_trigger_effect']:
            print(f"    -> 触发: {result['ui_effect']['effect_type']}")
    
    # 检查效果类型
    effect_type, count = handler.check_streak_effect(user_id)
    print(f"\n当前效果: {effect_type.value}, 连击数: {count}")
    
    # 测试降级保护
    handler.reset_streak(user_id)
    print("\n测试降级保护（连续错误2次）")
    for i in range(2):
        result = handler.process_answer(user_id, False, theta)
        print(f"  第{i+1}次:")
        print(f"    连错: {result['streak_state']['consecutive_wrong']}")
        print(f"    难度范围: {result['difficulty_adjustment']['adjusted_range']}")
        if result['should_trigger_effect']:
            print(f"    -> 触发: {result['ui_effect']['effect_type']}")


if __name__ == "__main__":
    print("=" * 60)
    print("需求1测试：基于连对/连错状态的实时UI交互与难度自适应调整")
    print("=" * 60)
    
    # 先直接测试算法
    test_algorithm_directly()
    
    # 然后测试API（如果服务正在运行）
    print("\n" + "=" * 60)
    print("尝试测试API（需要后端服务运行在localhost:8000）")
    print("=" * 60)
    
    try:
        test_streak_update()
        test_get_streak_state()
        print("\n=== 所有测试完成！ ===")
    except requests.exceptions.ConnectionError:
        print("\n后端服务未运行，跳过API测试")
        print("请启动服务: python main.py")
