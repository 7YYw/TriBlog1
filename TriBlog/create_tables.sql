-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS triblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 选择要使用的数据库
USE blogdb;

-- 删除现有表（如果存在）- 仅用于开发环境方便重建
DROP TABLE IF EXISTS CommentModel;
DROP TABLE IF EXISTS BlogPostModel;
DROP TABLE IF EXISTS UserModel;

-- 创建用户表 (UserModel)
CREATE TABLE UserModel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,    -- 用户名，唯一且非空
    password VARCHAR(255) NOT NULL,           -- 存储哈希后的密码，非空
    email VARCHAR(255) UNIQUE,                -- 邮箱，允许为空，但如果填写则必须唯一
    phone VARCHAR(50),                        -- 电话，允许为空
    bio TEXT,                                 -- 个人简介，允许为空
    avatar VARCHAR(255),                      -- 头像URL或文件路径，允许为空
    region VARCHAR(100),                      -- 所属地区，允许为空
    is_admin INT DEFAULT 0,                   -- 是否是管理员，默认0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 用户创建时间
);

-- 创建博客文章表 (BlogPostModel) - 不变
CREATE TABLE BlogPostModel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES UserModel(id) ON DELETE CASCADE
);

-- 创建评论表 (CommentModel) - 不变 (如果你打算实现评论功能)
CREATE TABLE CommentModel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    user_id INT NOT NULL, -- 假设评论必须是登录用户发表
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES BlogPostModel(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES UserModel(id) ON DELETE CASCADE
);

-- 可以添加一些初始数据（可选）
-- INSERT INTO UserModel (username, password, email, phone, bio, avatar, region, is_admin) VALUES (...);
-- INSERT INTO BlogPostModel (user_id, title, content) VALUES (...);
-- INSERT INTO CommentModel (post_id, user_id, content) VALUES (...);
