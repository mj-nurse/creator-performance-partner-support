DROP TABLE IF EXISTS support_cases;
DROP TABLE IF EXISTS monthly_performance;
DROP TABLE IF EXISTS creators;

CREATE TABLE creators (
    creator_id TEXT PRIMARY KEY,
    join_date TEXT NOT NULL,
    region TEXT NOT NULL,
    category TEXT NOT NULL,
    partner_tier TEXT NOT NULL
);

CREATE TABLE monthly_performance (
    creator_id TEXT NOT NULL,
    performance_month TEXT NOT NULL,
    uploads INTEGER NOT NULL CHECK (uploads >= 0),
    views INTEGER NOT NULL CHECK (views >= 0),
    watch_hours REAL NOT NULL CHECK (watch_hours >= 0),
    new_subscribers INTEGER NOT NULL CHECK (new_subscribers >= 0),
    PRIMARY KEY (creator_id, performance_month),
    FOREIGN KEY (creator_id) REFERENCES creators(creator_id)
);

CREATE TABLE support_cases (
    case_id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,
    opened_date TEXT NOT NULL,
    case_type TEXT NOT NULL,
    case_channel TEXT NOT NULL,
    resolution_hours REAL,
    first_contact_resolved INTEGER NOT NULL CHECK (first_contact_resolved IN (0, 1)),
    satisfaction_score INTEGER CHECK (satisfaction_score BETWEEN 1 AND 5),
    case_status TEXT NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES creators(creator_id)
);
