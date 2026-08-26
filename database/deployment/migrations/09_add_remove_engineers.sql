SELECT id, alias, name, email, role, active
FROM ac_engineers
ORDER BY id;

SELECT id, alias, name, email, role, active
FROM  ac_engineers
WHERE UPPER(role) = 'SUPERVISOR'
ORDER BY id;


UPDATE engineers
SET active = 0
WHERE alias = 'olduser';

SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ac_engineers'
ORDER BY ORDINAL_POSITION;

INSERT INTO ac_engineers
(alias, name, email, role, level, active)
VALUES
('Ghening', 'George Hening', 'email', 'SUPERVISOR', 'SUPERVISOR', 1);