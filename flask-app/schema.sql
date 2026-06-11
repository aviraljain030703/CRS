-- ============================================================
-- Smart Digital Complaint Management System — MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS cms_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE cms_db;

-- ── Users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(120)  NOT NULL,
  email         VARCHAR(150)  NOT NULL UNIQUE,
  student_id    VARCHAR(20)   UNIQUE,
  department    VARCHAR(100),
  phone         VARCHAR(20),
  password_hash VARCHAR(255)  NOT NULL,
  role          ENUM('student','admin') NOT NULL DEFAULT 'student',
  is_active     TINYINT(1)    NOT NULL DEFAULT 1,
  created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_email (email),
  INDEX idx_role  (role)
) ENGINE=InnoDB;

-- ── Complaints ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  complaint_number VARCHAR(40)   NOT NULL UNIQUE,
  user_id          INT           NOT NULL,
  title            VARCHAR(200)  NOT NULL,
  description      TEXT          NOT NULL,
  category         VARCHAR(50)   NOT NULL DEFAULT 'Other',
  priority         ENUM('Low','Medium','High','Critical') NOT NULL DEFAULT 'Low',
  status           ENUM('Pending','In Progress','Resolved','Rejected','Escalated') NOT NULL DEFAULT 'Pending',
  attachment       VARCHAR(300),
  assigned_to      INT,
  admin_response   TEXT,
  resolved_at      DATETIME,
  created_at       DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id)     REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_user_id  (user_id),
  INDEX idx_status   (status),
  INDEX idx_category (category),
  INDEX idx_priority (priority),
  INDEX idx_created  (created_at)
) ENGINE=InnoDB;

-- ── Complaint Logs ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaint_logs (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  complaint_id INT          NOT NULL,
  old_status   VARCHAR(30),
  new_status   VARCHAR(30)  NOT NULL,
  updated_by   VARCHAR(120) NOT NULL,
  remarks      TEXT,
  timestamp    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
  INDEX idx_complaint_id (complaint_id)
) ENGINE=InnoDB;

-- ── Notifications ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
  id                INT AUTO_INCREMENT PRIMARY KEY,
  user_id           INT          NOT NULL,
  title             VARCHAR(200) NOT NULL,
  message           TEXT         NOT NULL,
  notification_type VARCHAR(20)  NOT NULL DEFAULT 'info',
  is_read           TINYINT(1)   NOT NULL DEFAULT 0,
  created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id),
  INDEX idx_is_read (is_read)
) ENGINE=InnoDB;
