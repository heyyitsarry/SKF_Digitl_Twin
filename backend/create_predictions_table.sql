-- Create predictions table to store ML inference results

CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reading_id INT NOT NULL,
    health_score DECIMAL(5,2),
    failure_risk DECIMAL(5,3),
    anomaly_score DECIMAL(10,6),
    status VARCHAR(20),
    reconstruction_error DECIMAL(10,6),
    threshold_p95 DECIMAL(10,6),
    threshold_max DECIMAL(10,6),
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_reading (reading_id),
    FOREIGN KEY (reading_id) REFERENCES spindlereadings(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_failure_risk (failure_risk),
    INDEX idx_predicted_at (predicted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
