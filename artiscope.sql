/*
 Navicat Premium Dump SQL

 Source Server         : gms
 Source Server Type    : MySQL
 Source Server Version : 80039 (8.0.39)
 Source Host           : localhost:3306
 Source Schema         : artiscope

 Target Server Type    : MySQL
 Target Server Version : 80039 (8.0.39)
 File Encoding         : 65001

 Date: 22/05/2025 16:52:20
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for user_image_processes
-- ----------------------------
DROP TABLE IF EXISTS `user_image_processes`;
CREATE TABLE `user_image_processes`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `input_oss_url` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `input_token` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `output_oss_url` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id` ASC) USING BTREE,
  CONSTRAINT `user_image_processes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_image_processes
-- ----------------------------
INSERT INTO `user_image_processes` VALUES (1, 1, 'test_user', 'https://artiscope.oss-cn-beijing.aliyuncs.com/images/user_1/20250521143753592699_original_1.jpg', 'plane', 'https://artiscope.oss-cn-beijing.aliyuncs.com/images/user_1/20250521143753913079_processed_1.jpg', '2025-05-21 14:37:54', '2025-05-21 14:37:54');
INSERT INTO `user_image_processes` VALUES (2, 1, 'test_user', 'https://artiscope.oss-cn-beijing.aliyuncs.com/images/user_1/20250522130014864924_original_1.jpg', NULL, 'https://artiscope.oss-cn-beijing.aliyuncs.com/images/user_1/20250522130015814985_processed_ascii_1_ascii.png', '2025-05-22 13:00:16', '2025-05-22 13:00:16');
INSERT INTO `user_image_processes` VALUES (3, 1, 'test_user', 'https://artiscope.oss-cn-beijing.aliyuncs.com/images/user_1/20250522130256611164_original_1.jpg', NULL, 'https://artiscope.oss-cn-beijing.aliyuncs.com/images/user_1/20250522130257344920_processed_ascii_1_ascii.png', '2025-05-22 13:02:57', '2025-05-22 13:02:57');

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户名（唯一）',
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '加密后的密码',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户账户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (1, 'test_user', 'scrypt:32768:8:1$9RVjVDBhTe33PNDN$80cac1827e544b77ca43d807a2d97f2a801662502aa0f30154dd537058cc21be3f7558cbc3a919b72042b81ec0aaf22d104fe6b9c45146fc7bfdd604789e9c7c', '2025-05-21 11:06:24', '2025-05-21 11:06:24');

SET FOREIGN_KEY_CHECKS = 1;
