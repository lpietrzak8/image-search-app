CREATE TABLE IF NOT EXISTS posts (
    id INT NOT NULL AUTO_INCREMENT,
    author VARCHAR(64) NOT NULL,
    description VARCHAR(512) NOT NULL,
    image_path VARCHAR(512) NOT NULL,
    PRIMARY KEY (id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS keywords (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(64) NOT NULL,
    PRIMARY KEY (id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS post_keywords (
    post_id INT NOT NULL,
    keyword_id INT NOT NULL,
    PRIMARY KEY (post_id, keyword_id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blacklisted_images (
    id INT NOT NULL AUTO_INCREMENT,
    provider VARCHAR(32) NOT NULL,
    source_url VARCHAR(512) NOT NULL UNIQUE,
    status ENUM('suspended', 'blocked') NOT NULL DEFAULT 'suspended',
    reason VARCHAR(225),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;