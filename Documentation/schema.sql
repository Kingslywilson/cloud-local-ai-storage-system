-- ============================================================================
-- Gradious AI-Enhanced Cloud Storage & Sharing Platform
-- Database Schema DDL for MySQL Server 8.0+
-- Database: gradious_cloud
-- ============================================================================

CREATE DATABASE IF NOT EXISTS gradious_cloud DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gradious_cloud;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Folders Table
CREATE TABLE IF NOT EXISTS folders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_folders_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Files Table
CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    folder_id INT DEFAULT NULL,
    original_name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100) DEFAULT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL,
    INDEX idx_files_user (user_id),
    INDEX idx_files_folder (folder_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. File Shares Table
CREATE TABLE IF NOT EXISTS file_shares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    user_id INT NOT NULL,
    share_token VARCHAR(255) NOT NULL UNIQUE,
    share_type VARCHAR(50) NOT NULL DEFAULT 'public',
    shared_with_email VARCHAR(150) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME DEFAULT NULL,
    is_active INT NOT NULL DEFAULT 1,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_shares_token (share_token),
    INDEX idx_shares_file (file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. AI & ML Analysis Table
CREATE TABLE IF NOT EXISTS ai_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    summary VARCHAR(2000) DEFAULT NULL,
    description VARCHAR(2000) DEFAULT NULL,
    tags VARCHAR(1000) DEFAULT NULL,
    insights VARCHAR(3000) DEFAULT NULL,
    ml_category VARCHAR(100) DEFAULT NULL,
    ml_confidence FLOAT DEFAULT NULL,
    is_suspicious INT DEFAULT 0,
    suspicious_confidence FLOAT DEFAULT NULL,
    suspicious_details VARCHAR(1000) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    INDEX idx_ai_file (file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_id INT DEFAULT NULL,
    action VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) DEFAULT NULL,
    details VARCHAR(500) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE SET NULL,
    INDEX idx_activity_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
