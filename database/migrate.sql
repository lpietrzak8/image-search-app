
SET @dbname = DATABASE();
SET @colexists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'posts' AND COLUMN_NAME = 'image_path'
);
SET @sql = IF(@colexists = 0,
    'ALTER TABLE posts ADD COLUMN image_path VARCHAR(512) NULL AFTER description',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


ALTER TABLE keywords MODIFY COLUMN name VARCHAR(255) NOT NULL;

SET @col1exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'blacklist_images' AND COLUMN_NAME = 'image_url'
);
SET @sql = IF(@col1exists = 0,
    'ALTER TABLE blacklist_images ADD COLUMN image_url VARCHAR(512) NULL AFTER source_url',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col2exists = (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'blacklist_images' AND COLUMN_NAME = 'description'
);
SET @sql = IF(@col2exists = 0,
    'ALTER TABLE blacklist_images ADD COLUMN description VARCHAR(512) NULL AFTER image_url',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


SET @oldexists = (
    SELECT COUNT(*) FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'blacklisted_images'
);
SET @newexists = (
    SELECT COUNT(*) FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'blacklist_images'
);
SET @sql = IF(@oldexists = 1 AND @newexists = 0,
    'RENAME TABLE blacklisted_images TO blacklist_images',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


SET @indexexists = (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'user_saved_photos' AND INDEX_NAME = 'unique_user_photo'
);
SET @sql = IF(@indexexists = 1,
    'ALTER TABLE user_saved_photos DROP INDEX unique_user_photo',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @indexexists2 = (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'user_saved_photos' AND INDEX_NAME = 'unique_user_photo'
);
SET @sql = IF(@indexexists2 = 0,
    'ALTER TABLE user_saved_photos ADD UNIQUE KEY unique_user_photo (user_id, post_id)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
