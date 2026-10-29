CREATE TABLE managed_vehicles (
 id VARCHAR(64) NOT NULL PRIMARY KEY,
 payload JSON NOT NULL,
 status VARCHAR(20) NOT NULL,
 version BIGINT NOT NULL DEFAULT 1,
 updated_by BIGINT NULL,
 updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
);
CREATE TABLE managed_vehicle_changes (
 id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 vehicle_id VARCHAR(64) NOT NULL,
 actor_id BIGINT NOT NULL,
 previous_payload JSON NULL,
 next_payload JSON NOT NULL,
 previous_status VARCHAR(20) NULL,
 next_status VARCHAR(20) NOT NULL,
 created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 INDEX idx_vehicle_changes (vehicle_id, id)
);
