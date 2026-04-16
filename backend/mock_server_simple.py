"""
AI Tutor V3 Mock API Server (Simple HTTP version)
无需FastAPI，使用Python内置HTTP服务器
支持需求1（连击处理）和需求10（技能树）
"""

import json
import http.server
import socketserver
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 导入算法模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from algorithms import (
    BKTModel, IRTModel, KIRTModel, QuestionParams,
    AdaptiveKFactor, MemoryDecay, ActualScoreCalculator,
    AnswerRecord, HintLevel,
    StreakHandler, get_streak_handler,
    SkillTreeBuilder, get_skill_tree_builder,
    HintButtonStateMachine, get_hint_button_sm
)

# 初始化算法模型
bkt_model = BKTModel()
irt_model = IRTModel()
kirt_model = KIRTModel()
adaptive_k = AdaptiveKFactor()
memory_decay = MemoryDecay()
actual_score_calc = ActualScoreCalculator()
streak_handler = get_streak_handler()
skill_tree_builder = get_skill_tree_builder()
hint_button_sm = get_hint_button_sm()

# Mock数据
mock_users = {
    1: {"user_id": 1, "username": "student_001", "theta": 0.5, "total_questions": 50, "correct_count": 35, "avg_mastery": 0.65},
    2: {"user_id": 2, "username": "student_002", "theta": -0.3, "total_questions": 20, "correct_count": 10, "avg_mastery": 0.45},
    3: {"user_id": 3, "username": "student_003", "theta": 1.2, "total_questions": 100, "correct_count": 85, "avg_mastery": 0.82},
}

mock_mastery = {
    (1, 101): {"p_known": 0.8, "level": "mastered"},
    (1, 102): {"p_known": 0.6, "level": "learning"},
    (1, 103): {"p_known": 0.3, "level": "weak"},
}


class MockAPIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")
    
    def _send_json(self, data: dict, status: int = 200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _send_error(self, message: str, status: int = 400):
        """发送错误响应"""
        self._send_json({"error": message}, status)
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        path = urllib.parse.urlparse(self.path).path
        
        # 根路径
        if path == "/":
            self._send_json({
                "message": "AI Tutor V3 Mock API (Simple)",
                "version": "3.0.0",
                "status": "running",
                "features": ["需求1-连击处理", "需求10-技能树"]
            })
            return
        
        # 健康检查
        if path == "/health":
            self._send_json({"status": "healthy"})
            return
        
        # 获取用户列表
        if path == "/api/users":
            self._send_json(list(mock_users.values()))
            return
        
        # 获取能力值
        if path.startswith("/api/cognitive/theta/"):
            try:
                user_id = int(path.split("/")[-1])
                if user_id not in mock_users:
                    self._send_error("User not found", 404)
                    return
                
                user = mock_users[user_id]
                total = user["total_questions"]
                correct = user["correct_count"]
                
                # 简化版IRT估计
                if total == 0:
                    theta = 0.0
                else:
                    accuracy = correct / total
                    theta = (accuracy - 0.5) * 4  # 映射到[-2, 2]
                
                self._send_json({
                    "user_id": user_id,
                    "theta": round(theta, 4),
                    "theta_irt": round(theta, 4),
                    "theta_bkt": round((user["avg_mastery"] - 0.5) * 4, 4),
                    "alpha": 0.8 if total > 10 else 0.3,
                    "theta_se": round(1.0 / ((total + 1) ** 0.5), 4),
                    "ci_lower": round(theta - 1.96 / ((total + 1) ** 0.5), 4),
                    "ci_upper": round(theta + 1.96 / ((total + 1) ** 0.5), 4)
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 获取难度范围
        if path.startswith("/api/cognitive/difficulty-range/"):
            try:
                user_id = int(path.split("/")[-1])
                theta = mock_users.get(user_id, {}).get("theta", 0.0)
                
                self._send_json({
                    "theta": theta,
                    "min_difficulty": round(theta - 0.5, 2),
                    "max_difficulty": round(theta + 0.5, 2),
                    "recommended_range": f"[{theta-0.5:+.1f}, {theta+0.5:+.1f}]"
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 获取诊断报告
        if path.startswith("/api/cognitive/report/"):
            try:
                user_id = int(path.split("/")[-1])
                user = mock_users.get(user_id, {})
                theta = user.get("theta", 0.0)
                
                self._send_json({
                    "user_id": user_id,
                    "ability": {
                        "theta": theta,
                        "theta_irt": theta,
                        "theta_bkt": (user.get("avg_mastery", 0.5) - 0.5) * 4,
                        "alpha": 0.8,
                        "theta_se": 0.14,
                        "ci_lower": theta - 0.27,
                        "ci_upper": theta + 0.27
                    },
                    "mastery_distribution": {
                        "mastered": 5,
                        "learning": 3,
                        "weak": 2,
                        "total": 10
                    },
                    "recommended_difficulty": {
                        "min": round(theta - 0.5, 2),
                        "max": round(theta + 0.5, 2)
                    },
                    "generated_at": datetime.now().isoformat()
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求1：获取连击状态
        if path.startswith("/api/cognitive/streak/state/"):
            try:
                user_id = int(path.split("/")[-1])
                state = streak_handler.get_user_streak_state(user_id)
                
                self._send_json({
                    "user_id": user_id,
                    "consecutive_correct": state.consecutive_correct,
                    "consecutive_wrong": state.consecutive_wrong,
                    "current_streak_type": state.current_streak_type.value,
                    "current_streak_count": state.current_streak_count
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求10：获取所有专题
        if path == "/api/cognitive/skill-tree/topics":
            try:
                topics = skill_tree_builder.get_all_topics()
                self._send_json({
                    "topics": topics,
                    "count": len(topics)
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求16：获取提示按钮状态
        if path.startswith("/api/cognitive/hint-button/state/"):
            try:
                user_id = int(path.split("/")[-1])
                
                result = hint_button_sm.get_full_state(user_id)
                
                self._send_json(result)
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 404
        self._send_error("Not found", 404)
    
    def do_POST(self):
        """处理POST请求"""
        path = urllib.parse.urlparse(self.path).path
        
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8')) if body else {}
        except json.JSONDecodeError:
            self._send_error("Invalid JSON")
            return
        
        # 更新掌握度（BKT）
        if path == "/api/cognitive/mastery/update":
            try:
                user_id = data.get("user_id")
                kp_id = data.get("knowledge_point_id")
                is_correct = data.get("is_correct")
                
                if None in [user_id, kp_id, is_correct]:
                    self._send_error("Missing required fields")
                    return
                
                # 获取当前掌握度
                key = (user_id, kp_id)
                if key in mock_mastery:
                    current_p = mock_mastery[key]["p_known"]
                else:
                    current_p = 0.5
                
                # BKT更新
                new_p = bkt_model.update(current_p, is_correct)
                level = bkt_model.get_mastery_level(new_p)
                
                # 保存
                mock_mastery[key] = {"p_known": new_p, "level": level}
                
                self._send_json({
                    "user_id": user_id,
                    "knowledge_point_id": kp_id,
                    "p_known": round(new_p, 4),
                    "mastery_level": level
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 计算Actual Score
        if path == "/api/cognitive/actual-score/calculate":
            try:
                record = AnswerRecord(
                    is_correct=data.get("is_correct", True),
                    hint_level=HintLevel(data.get("hint_level", 0)),
                    time_spent=data.get("time_spent", 60),
                    expected_time=data.get("expected_time", 60),
                    skip_reason=data.get("skip_reason")
                )
                
                score = actual_score_calc.calculate(record)
                
                hint_names = {0: "自主完成", 1: "方向提示", 2: "公式提示", 3: "步骤推导", 4: "完整答案"}
                
                self._send_json({
                    "actual_score": round(score, 4),
                    "hint_level_name": hint_names.get(data.get("hint_level", 0), "未知")
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求1：更新连击状态
        if path == "/api/cognitive/streak/update":
            try:
                user_id = data.get("user_id")
                kp_id = data.get("knowledge_point_id")
                is_correct = data.get("is_correct")
                
                if None in [user_id, kp_id, is_correct]:
                    self._send_error("Missing required fields")
                    return
                
                # 获取当前掌握度
                key = (user_id, kp_id)
                if key in mock_mastery:
                    current_p = mock_mastery[key]["p_known"]
                else:
                    current_p = 0.5
                
                # BKT更新
                new_p = bkt_model.update(current_p, is_correct)
                level = bkt_model.get_mastery_level(new_p)
                
                # 保存掌握度
                mock_mastery[key] = {"p_known": new_p, "level": level}
                
                # 需求1：处理连击状态
                user_theta = mock_users.get(user_id, {}).get("theta", 0.5)
                streak_result = streak_handler.process_answer(user_id, is_correct, user_theta)
                
                self._send_json({
                    "user_id": user_id,
                    "knowledge_point_id": kp_id,
                    "p_known": round(new_p, 4),
                    "p_known_change": round(new_p - current_p, 4),
                    "mastery_level": level,
                    "consecutive_correct": streak_result['streak_state']['consecutive_correct'],
                    "consecutive_wrong": streak_result['streak_state']['consecutive_wrong'],
                    "difficulty_adjustment": streak_result['difficulty_adjustment'],
                    "ui_effect": streak_result['ui_effect'],
                    "should_trigger_effect": streak_result['should_trigger_effect']
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求1：重置连击
        if path.startswith("/api/cognitive/streak/reset/"):
            try:
                user_id = int(path.split("/")[-1])
                state = streak_handler.reset_streak(user_id)
                
                self._send_json({
                    "user_id": user_id,
                    "message": "连击状态已重置",
                    "state": state.to_dict()
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求10：获取技能树
        if path == "/api/cognitive/skill-tree":
            try:
                user_id = data.get("user_id")
                topic = data.get("topic", "等差数列")
                
                # Mock用户掌握度
                mock_mastery_tree = {
                    "arith_001": 0.9,
                    "arith_002": 0.85,
                    "arith_003": 0.6,
                    "arith_004": 0.3,
                    "arith_005": 0.4,
                    "arith_006": 0.0,
                }
                
                user_tree = skill_tree_builder.build_user_skill_tree(topic, mock_mastery_tree)
                
                self._send_json({
                    "topic": user_tree.topic,
                    "nodes": {k: v.to_dict() for k, v in user_tree.nodes.items()},
                    "edges": user_tree.edges,
                    "total_nodes": user_tree.total_nodes
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求10：获取专题进度
        if path == "/api/cognitive/skill-tree/progress":
            try:
                user_id = data.get("user_id")
                topic = data.get("topic", "等差数列")
                
                mock_mastery_tree = {
                    "arith_001": 0.9,
                    "arith_002": 0.85,
                    "arith_003": 0.6,
                    "arith_004": 0.3,
                    "arith_005": 0.4,
                    "arith_006": 0.0,
                }
                
                progress = skill_tree_builder.calculate_topic_progress(topic, mock_mastery_tree)
                
                self._send_json(progress.to_dict())
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求10：获取推荐训练
        if path == "/api/cognitive/skill-tree/recommendations":
            try:
                user_id = data.get("user_id")
                topic = data.get("topic", "等差数列")
                limit = data.get("limit", 3)
                
                mock_mastery_tree = {
                    "arith_001": 0.9,
                    "arith_002": 0.85,
                    "arith_003": 0.6,
                    "arith_004": 0.3,
                    "arith_005": 0.4,
                    "arith_006": 0.0,
                }
                
                recommendations = skill_tree_builder.get_recommended_training(
                    topic, mock_mastery_tree, limit
                )
                
                self._send_json({
                    "topic": topic,
                    "recommendations": recommendations,
                    "count": len(recommendations)
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求16：点击提示按钮
        if path == "/api/cognitive/hint-button/click":
            try:
                user_id = data.get("user_id")
                
                result = hint_button_sm.click(user_id)
                
                self._send_json(result)
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求16：重置提示按钮
        if path == "/api/cognitive/hint-button/reset":
            try:
                user_id = data.get("user_id")
                
                result = hint_button_sm.reset(user_id)
                
                self._send_json(result)
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求20：获取每日特训包
        if path == "/api/cognitive/daily-pack":
            try:
                user_id = data.get("user_id")
                date = data.get("date")
                
                # Mock用户数据
                user_theta = 0.5
                user_mastery = {
                    "等差数列定义": 0.9,
                    "等差数列通项": 0.85,
                    "等差数列求和": 0.3,
                    "等比数列定义": 0.4,
                    "递推数列": 0.6,
                }
                review_queue = ["q001"]
                
                pack = daily_pack_generator.generate_pack(
                    user_id=user_id,
                    user_theta=user_theta,
                    user_mastery=user_mastery,
                    review_queue=review_queue,
                    date=date
                )
                
                self._send_json(pack.to_dict())
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 需求29：执行记忆衰减Cron任务
        if path == "/api/cognitive/cron/memory-decay":
            try:
                result = memory_decay_cron.execute_cron_job()
                self._send_json(result)
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 404
        self._send_error("Not found", 404)


def run_server(port=8001):
    """运行服务器"""
    with socketserver.TCPServer(("", port), MockAPIHandler) as httpd:
        print("=" * 60)
        print("AI Tutor V3 Mock API Server (Simple HTTP)")
        print("=" * 60)
        print(f"\nServer running at http://localhost:{port}")
        print("\nAvailable endpoints:")
        print("  GET  /                                       - Root")
        print("  GET  /health                                 - Health check")
        print("  GET  /api/users                              - List users")
        print("  POST /api/cognitive/mastery/update           - Update mastery (BKT)")
        print("  GET  /api/cognitive/theta/{user_id}          - Get theta (K-IRT)")
        print("  POST /api/cognitive/actual-score/calculate   - Calculate Actual Score")
        print("  GET  /api/cognitive/difficulty-range/{user_id} - Difficulty range")
        print("  GET  /api/cognitive/report/{user_id}         - Comprehensive report")
        print("  POST /api/cognitive/streak/update            - Update streak (需求1)")
        print("  GET  /api/cognitive/streak/state/{user_id}   - Get streak state (需求1)")
        print("  POST /api/cognitive/streak/reset/{user_id}   - Reset streak (需求1)")
        print("  POST /api/cognitive/skill-tree               - Get skill tree (需求10)")
        print("  POST /api/cognitive/skill-tree/progress      - Get topic progress (需求10)")
        print("  POST /api/cognitive/skill-tree/recommendations - Get recommendations (需求10)")
        print("  GET  /api/cognitive/skill-tree/topics        - Get all topics (需求10)")
        print("  POST /api/cognitive/hint-button/click        - Click hint button (需求16)")
        print("  POST /api/cognitive/hint-button/reset        - Reset hint button (需求16)")
        print("  GET  /api/cognitive/hint-button/state/{uid}  - Get hint button state (需求16)")
        print("  POST /api/cognitive/daily-pack               - Get daily 5-question pack (需求20)")
        print("  POST /api/cognitive/cron/memory-decay        - Execute memory decay cron (需求29)")
        print("  GET  /api/cognitive/cron/memory-decay/next   - Get next cron execution time (需求29)")
        print("\nPress Ctrl+C to stop")
        print("=" * 60 + "\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")


if __name__ == "__main__":
    run_server()
