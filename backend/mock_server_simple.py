"""
AI Tutor V3 Mock API Server (Simple HTTP version)
无需FastAPI，使用Python内置HTTP服务器
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
    AnswerRecord, HintLevel
)

# 初始化算法模型
bkt_model = BKTModel()
irt_model = IRTModel()
kirt_model = KIRTModel()
adaptive_k = AdaptiveKFactor()
memory_decay = MemoryDecay()
actual_score_calc = ActualScoreCalculator()

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
                "status": "running"
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
                theta_irt = irt_model.estimate_theta_simple(user["correct_count"], user["total_questions"])
                # BKT映射：将掌握度映射到theta范围
                theta_bkt = -3.0 + 6.0 * user["avg_mastery"]
                theta_bkt = max(-3.0, min(3.0, theta_bkt))
                theta_final = kirt_model.estimate_theta_final(theta_irt, theta_bkt, user["total_questions"])
                alpha = kirt_model.compute_alpha(user["total_questions"])
                
                self._send_json({
                    "user_id": user_id,
                    "theta": round(theta_final, 4),
                    "theta_irt": round(theta_irt, 4),
                    "theta_bkt": round(theta_bkt, 4),
                    "alpha": alpha
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 获取推荐难度范围
        if path.startswith("/api/cognitive/difficulty-range/"):
            try:
                user_id = int(path.split("/")[-1])
                if user_id not in mock_users:
                    self._send_error("User not found", 404)
                    return
                
                theta = mock_users[user_id]["theta"]
                min_diff, max_diff = irt_model.get_recommended_difficulty_range(theta)
                
                self._send_json({
                    "user_id": user_id,
                    "theta": theta,
                    "min_difficulty": min_diff,
                    "max_difficulty": max_diff
                })
            except Exception as e:
                self._send_error(str(e))
            return
        
        # 获取综合报告
        if path.startswith("/api/cognitive/report/"):
            try:
                user_id = int(path.split("/")[-1])
                if user_id not in mock_users:
                    self._send_error("User not found", 404)
                    return
                
                # 统计掌握度
                mastered = learning = weak = 0
                for key, data in mock_mastery.items():
                    if key[0] == user_id:
                        if data["level"] == "mastered":
                            mastered += 1
                        elif data["level"] == "learning":
                            learning += 1
                        else:
                            weak += 1
                
                self._send_json({
                    "user_id": user_id,
                    "mastery_distribution": {
                        "mastered": mastered,
                        "learning": learning,
                        "weak": weak,
                        "total": mastered + learning + weak
                    },
                    "generated_at": datetime.now().isoformat()
                })
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
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_error("Invalid JSON")
            return
        
        # 更新掌握度
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
        print("\nPress Ctrl+C to stop")
        print("=" * 60 + "\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")


if __name__ == "__main__":
    run_server()
