-- AI Tutor 项目完整数据库表结构
-- 包含所有表的创建语句

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `email` VARCHAR(100) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 题目表
CREATE TABLE IF NOT EXISTS `questions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `content` TEXT NOT NULL,
  `answer` TEXT DEFAULT NULL,
  `difficulty` INT DEFAULT NULL,
  `knowledge_points` JSON DEFAULT NULL,
  `problem_type` VARCHAR(50) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_difficulty` (`difficulty`),
  KEY `idx_problem_type` (`problem_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 学习记录表
CREATE TABLE IF NOT EXISTS `learning_records` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `question_id` INT NOT NULL,
  `is_correct` BOOLEAN DEFAULT NULL,
  `user_answer` TEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_question_id` (`question_id`),
  KEY `idx_is_correct` (`is_correct`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_learning_record_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_learning_record_question` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 学生画图表
CREATE TABLE IF NOT EXISTS `user_profiles` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `knowledge_mastery` JSON DEFAULT NULL,
  `weak_points` JSON DEFAULT NULL,
  `total_questions` INT DEFAULT 0,
  `correct_count` INT DEFAULT 0,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`),
  CONSTRAINT `fk_user_profile_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 聊天会话表
CREATE TABLE IF NOT EXISTS `chat_sessions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `session_name` VARCHAR(255) DEFAULT NULL,
  `start_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_time` DATETIME DEFAULT NULL,
  `status` VARCHAR(20) DEFAULT 'active',
  `total_messages` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_start_time` (`start_time`),
  CONSTRAINT `fk_chat_session_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 聊天消息表
CREATE TABLE IF NOT EXISTS `chat_messages` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `session_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `role` ENUM('user', 'assistant') NOT NULL,
  `content` TEXT NOT NULL,
  `message_type` ENUM('text', 'image', 'file') DEFAULT 'text',
  `image_path` VARCHAR(500) DEFAULT NULL,
  `file_path` VARCHAR(500) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_solution` BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_role` (`role`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_is_solution` (`is_solution`),
  CONSTRAINT `fk_chat_message_session` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_chat_message_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 解题步骤表
CREATE TABLE IF NOT EXISTS `solution_steps` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `message_id` INT NOT NULL,
  `step_number` INT NOT NULL,
  `step_content` TEXT NOT NULL,
  `knowledge_point` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_message_id` (`message_id`),
  KEY `idx_step_number` (`step_number`),
  CONSTRAINT `fk_solution_step_message` FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识点表
CREATE TABLE IF NOT EXISTS `knowledge_points` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `parent_id` INT DEFAULT NULL,
  `level` INT DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  KEY `idx_parent_id` (`parent_id`),
  KEY `idx_level` (`level`),
  CONSTRAINT `fk_knowledge_point_parent` FOREIGN KEY (`parent_id`) REFERENCES `knowledge_points` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 题目-知识点关联表
CREATE TABLE IF NOT EXISTS `question_knowledge_points` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `question_id` INT NOT NULL,
  `knowledge_point_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_question_knowledge` (`question_id`, `knowledge_point_id`),
  KEY `idx_question_id` (`question_id`),
  KEY `idx_knowledge_point_id` (`knowledge_point_id`),
  CONSTRAINT `fk_qkp_question` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_qkp_knowledge_point` FOREIGN KEY (`knowledge_point_id`) REFERENCES `knowledge_points` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 学生-知识点掌握度表
CREATE TABLE IF NOT EXISTS `user_knowledge_mastery` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `knowledge_point_id` INT NOT NULL,
  `mastery_level` INT DEFAULT 0,
  `practice_count` INT DEFAULT 0,
  `correct_count` INT DEFAULT 0,
  `last_practiced_at` DATETIME DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_knowledge` (`user_id`, `knowledge_point_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_knowledge_point_id` (`knowledge_point_id`),
  KEY `idx_mastery_level` (`mastery_level`),
  CONSTRAINT `fk_ukm_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ukm_knowledge_point` FOREIGN KEY (`knowledge_point_id`) REFERENCES `knowledge_points` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初始化知识点数据
INSERT INTO `knowledge_points` (`name`, `description`, `parent_id`, `level`) VALUES
('数列', '数学中的数列概念和性质', NULL, 1),
('等差数列', '等差数列的定义、通项公式和求和公式', 1, 2),
('等比数列', '等比数列的定义、通项公式和求和公式', 1, 2),
('数列求和', '各种数列的求和方法', 1, 2),
('递推数列', '通过递推关系定义的数列', 1, 2),
('等差数列通项公式', '等差数列的通项公式 an = a1 + (n-1)d', 2, 3),
('等差数列求和公式', '等差数列的前n项和公式 Sn = n(a1 + an)/2', 2, 3),
('等比数列通项公式', '等比数列的通项公式 an = a1 * r^(n-1)', 3, 3),
('等比数列求和公式', '等比数列的前n项和公式 Sn = a1(1-r^n)/(1-r)', 3, 3),
('裂项相消法', '数列求和的裂项相消方法', 4, 3),
('错位相减法', '数列求和的错位相减方法', 4, 3),
('数学归纳法', '证明数列性质的数学归纳法', 1, 3);
