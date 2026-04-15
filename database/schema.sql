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

-- ==================== V3 扩展字段 ====================

-- learning_records 表扩展
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `source_type` VARCHAR(50) NOT NULL DEFAULT 'recommended';
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `custom_question_data` JSON NULL;
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `ai_feedback` TEXT NULL;
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `recommendation_session_id` VARCHAR(100) NULL;
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `recommendation_algorithm_version` VARCHAR(50) NULL;
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `hint_count` INT DEFAULT 0;
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `time_spent` INT NULL;
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `skip_reason` VARCHAR(20) NULL;
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `theta_before` FLOAT NULL;
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `theta_after` FLOAT NULL;
ALTER TABLE `learning_records` ADD COLUMN IF NOT EXISTS `mastery_updates` JSON NULL;

-- user_profiles 表扩展
ALTER TABLE `user_profiles` ADD COLUMN IF NOT EXISTS `theta_se` FLOAT NULL;
ALTER TABLE `user_profiles` ADD COLUMN IF NOT EXISTS `theta_ci_lower` FLOAT NULL;
ALTER TABLE `user_profiles` ADD COLUMN IF NOT EXISTS `theta_ci_upper` FLOAT NULL;
ALTER TABLE `user_profiles` ADD COLUMN IF NOT EXISTS `avg_mastery` FLOAT NULL;
ALTER TABLE `user_profiles` ADD COLUMN IF NOT EXISTS `weak_kp_count` INT DEFAULT 0;
ALTER TABLE `user_profiles` ADD COLUMN IF NOT EXISTS `learning_style` VARCHAR(20) NULL;
ALTER TABLE `user_profiles` ADD COLUMN IF NOT EXISTS `mastery_strategy` VARCHAR(20) DEFAULT 'simple';

-- user_knowledge_mastery 表扩展(BKT参数)
ALTER TABLE `user_knowledge_mastery` ADD COLUMN IF NOT EXISTS `p_guess` FLOAT DEFAULT 0.2;
ALTER TABLE `user_knowledge_mastery` ADD COLUMN IF NOT EXISTS `p_slip` FLOAT DEFAULT 0.1;
ALTER TABLE `user_knowledge_mastery` ADD COLUMN IF NOT EXISTS `p_known` FLOAT DEFAULT 0.5;
ALTER TABLE `user_knowledge_mastery` ADD COLUMN IF NOT EXISTS `consecutive_correct` INT DEFAULT 0;
ALTER TABLE `user_knowledge_mastery` ADD COLUMN IF NOT EXISTS `consecutive_wrong` INT DEFAULT 0;

-- ==================== V3 新增表 ====================

CREATE TABLE IF NOT EXISTS `user_ability_history` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `theta` FLOAT NOT NULL,
  `theta_se` FLOAT DEFAULT NULL,
  `theta_ci_lower` FLOAT DEFAULT NULL,
  `theta_ci_upper` FLOAT DEFAULT NULL,
  `avg_mastery` FLOAT DEFAULT NULL,
  `weak_kp_count` INT DEFAULT 0,
  `total_questions` INT DEFAULT 0,
  `correct_count` INT DEFAULT 0,
  `recorded_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_time` (`user_id`, `recorded_at`),
  CONSTRAINT `fk_uah_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `mistake_book` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `question_id` INT NOT NULL,
  `error_count` INT DEFAULT 1,
  `first_error_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_error_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `mastered` BOOLEAN DEFAULT FALSE,
  `mastered_at` DATETIME DEFAULT NULL,
  `review_count` INT DEFAULT 0,
  `last_review_at` DATETIME DEFAULT NULL,
  `next_review_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_question` (`user_id`, `question_id`),
  KEY `idx_user_mastered` (`user_id`, `mastered`),
  KEY `idx_next_review` (`user_id`, `next_review_at`),
  CONSTRAINT `fk_mistake_book_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_mistake_book_question` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `favorites` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `question_id` INT NOT NULL,
  `folder_name` VARCHAR(50) NOT NULL DEFAULT '默认收藏夹',
  `note` TEXT DEFAULT NULL,
  `tags` JSON DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_question` (`user_id`, `question_id`),
  KEY `idx_user_folder` (`user_id`, `folder_name`),
  CONSTRAINT `fk_favorite_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_favorite_question` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user_interaction_logs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `session_id` VARCHAR(100) DEFAULT NULL,
  `interaction_type` VARCHAR(50) NOT NULL,
  `question_id` INT DEFAULT NULL,
  `knowledge_points` JSON DEFAULT NULL,
  `difficulty` INT DEFAULT NULL,
  `content` TEXT DEFAULT NULL,
  `metadata` JSON DEFAULT NULL,
  `sentiment_tag` VARCHAR(20) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_time` (`user_id`, `created_at`),
  KEY `idx_session` (`session_id`),
  CONSTRAINT `fk_interaction_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_interaction_question` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE SET NULL
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
