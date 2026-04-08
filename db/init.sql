CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

CREATE TABLE IF NOT EXISTS sensor_readings (
    time                    TIMESTAMPTZ      NOT NULL,
    sensor_id               TEXT             NOT NULL,
    temperatura             DOUBLE PRECISION NOT NULL,
    humedad                 DOUBLE PRECISION NOT NULL,
    ph                      DOUBLE PRECISION NOT NULL,
    necesita_riego          BOOLEAN          NOT NULL DEFAULT FALSE,
    prediccion_confianza    DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

SELECT create_hypertable(
    'sensor_readings',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_sensor_time
    ON sensor_readings (sensor_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_riego_time
    ON sensor_readings (necesita_riego, time DESC)
    WHERE necesita_riego = TRUE;

CREATE OR REPLACE VIEW v_estadisticas_sensor AS
SELECT
    sensor_id,
    COUNT(*)                                       AS total_lecturas,
    ROUND(AVG(temperatura)::numeric, 2)            AS temp_promedio,
    ROUND(MIN(temperatura)::numeric, 2)            AS temp_min,
    ROUND(MAX(temperatura)::numeric, 2)            AS temp_max,
    ROUND(AVG(humedad)::numeric, 2)                AS humedad_promedio,
    ROUND(AVG(ph)::numeric, 3)                     AS ph_promedio,
    SUM(necesita_riego::int)                       AS alertas_riego,
    ROUND(
        100.0 * SUM(necesita_riego::int) / NULLIF(COUNT(*), 0),
        1
    )                                              AS pct_alertas
FROM sensor_readings
WHERE time >= NOW() - INTERVAL '24 hours'
GROUP BY sensor_id
ORDER BY sensor_id;

INSERT INTO sensor_readings
    (time, sensor_id, temperatura, humedad, ph, necesita_riego, prediccion_confianza)
VALUES
    (NOW() - INTERVAL '2 minutes', 'sensor-01', 24.5, 65.0, 6.8, FALSE, 0.92),
    (NOW() - INTERVAL '1 minute',  'sensor-02', 31.2, 35.0, 6.2, TRUE,  0.87),
    (NOW(),                         'sensor-03', 27.8, 58.0, 5.9, FALSE, 0.78);
