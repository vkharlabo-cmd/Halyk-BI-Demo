-- Brokerage Executive BI Dashboard — PostgreSQL reference implementation
-- Grain: one row per calendar month in mart_brokerage_monthly.

CREATE SCHEMA IF NOT EXISTS demo_brokerage;
SET search_path TO demo_brokerage;

CREATE TABLE clients (
    client_id bigint PRIMARY KEY,
    registration_date date NOT NULL,
    client_segment text NOT NULL,
    manager_id bigint,
    acquisition_channel text NOT NULL,
    status text NOT NULL
);

CREATE TABLE accounts (
    account_id bigint PRIMARY KEY,
    client_id bigint,
    open_date date NOT NULL,
    account_type text NOT NULL,
    status text NOT NULL
);

CREATE TABLE instruments (
    instrument_id bigint PRIMARY KEY,
    instrument_type text NOT NULL,
    ticker text NOT NULL,
    market text NOT NULL
);

CREATE TABLE managers (
    manager_id bigint PRIMARY KEY,
    manager_name text NOT NULL,
    department text NOT NULL
);

CREATE TABLE trades (
    trade_id bigint,
    client_id bigint,
    trade_date date NOT NULL,
    instrument_id bigint,
    trade_amount numeric(18,2) NOT NULL,
    commission numeric(18,2) NOT NULL,
    operation_type text NOT NULL
);

CREATE TABLE cash_operations (
    operation_id bigint PRIMARY KEY,
    account_id bigint,
    client_id bigint,
    operation_date date NOT NULL,
    operation_type text NOT NULL,
    amount numeric(18,2) NOT NULL
);

-- Production load pattern (run from psql, adjusting the local path):
-- \copy clients FROM 'data/clients.csv' CSV HEADER;
-- \copy accounts FROM 'data/accounts.csv' CSV HEADER;
-- \copy instruments FROM 'data/instruments.csv' CSV HEADER;
-- \copy managers FROM 'data/managers.csv' CSV HEADER;
-- \copy trades FROM 'data/trades.csv' CSV HEADER;
-- \copy cash_operations FROM 'data/cash_operations.csv' CSV HEADER;

CREATE OR REPLACE VIEW vw_client_first_trade AS
SELECT client_id, MIN(trade_date) AS first_trade_date
FROM trades
GROUP BY client_id;

CREATE MATERIALIZED VIEW mart_brokerage_monthly AS
WITH months AS (
    SELECT generate_series(
        date_trunc('month', MIN(d))::date,
        date_trunc('month', MAX(d))::date,
        interval '1 month'
    )::date AS month
    FROM (
        SELECT registration_date AS d FROM clients
        UNION ALL SELECT trade_date FROM trades
        UNION ALL SELECT operation_date FROM cash_operations
    ) dates
),
trade_kpi AS (
    SELECT
        date_trunc('month', trade_date)::date AS month,
        COUNT(DISTINCT client_id) AS active_clients,
        COUNT(*) AS trades_count,
        SUM(trade_amount) AS trading_turnover,
        SUM(commission) AS commission_revenue
    FROM trades
    GROUP BY 1
),
client_kpi AS (
    SELECT date_trunc('month', registration_date)::date AS month,
           COUNT(*) AS new_clients
    FROM clients
    GROUP BY 1
),
cash_kpi AS (
    SELECT
        date_trunc('month', operation_date)::date AS month,
        SUM(amount) FILTER (WHERE operation_type = 'DEPOSIT') AS deposits,
        SUM(amount) FILTER (WHERE operation_type = 'WITHDRAWAL') AS withdrawals
    FROM cash_operations
    GROUP BY 1
),
base AS (
    SELECT
        m.month,
        COALESCE(t.active_clients, 0) AS active_clients,
        COALESCE(c.new_clients, 0) AS new_clients,
        COALESCE(t.trades_count, 0) AS trades_count,
        COALESCE(t.trading_turnover, 0) AS trading_turnover,
        COALESCE(t.commission_revenue, 0) AS commission_revenue,
        COALESCE(k.deposits, 0) AS deposits,
        COALESCE(k.withdrawals, 0) AS withdrawals
    FROM months m
    LEFT JOIN trade_kpi t USING (month)
    LEFT JOIN client_kpi c USING (month)
    LEFT JOIN cash_kpi k USING (month)
)
SELECT
    month,
    active_clients,
    new_clients,
    trades_count,
    trading_turnover,
    commission_revenue,
    commission_revenue / NULLIF(active_clients, 0) AS avg_commission_per_active_client,
    deposits,
    withdrawals,
    deposits - withdrawals AS net_inflow,
    (commission_revenue - LAG(commission_revenue) OVER (ORDER BY month))
        / NULLIF(LAG(commission_revenue) OVER (ORDER BY month), 0) AS mom_revenue_growth
FROM base
ORDER BY month;

-- Conversion: opened account -> at least one trade.
CREATE OR REPLACE VIEW vw_first_trade_conversion AS
SELECT
    COUNT(DISTINCT a.account_id) AS opened_accounts,
    COUNT(DISTINCT a.account_id) FILTER (WHERE f.first_trade_date IS NOT NULL) AS accounts_with_first_trade,
    COUNT(DISTINCT a.account_id) FILTER (WHERE f.first_trade_date IS NOT NULL)::numeric
        / NULLIF(COUNT(DISTINCT a.account_id), 0) AS first_trade_conversion
FROM accounts a
LEFT JOIN vw_client_first_trade f USING (client_id);

-- Dormant = no trade during the last 90 days relative to the dataset max date.
CREATE OR REPLACE VIEW vw_dormant_clients AS
WITH anchor AS (SELECT MAX(trade_date) AS as_of_date FROM trades),
last_trade AS (
    SELECT client_id, MAX(trade_date) AS last_trade_date
    FROM trades
    GROUP BY client_id
)
SELECT c.client_id, c.client_segment, c.manager_id, l.last_trade_date
FROM clients c
CROSS JOIN anchor a
LEFT JOIN last_trade l USING (client_id)
WHERE l.last_trade_date IS NULL OR l.last_trade_date < a.as_of_date - interval '90 days';

-- Data quality control plane. Non-zero issue_count requires investigation.
CREATE OR REPLACE VIEW vw_data_quality_checks AS
SELECT 'duplicate_trade_id' AS check_name, COUNT(*) AS issue_count, 'Critical' AS severity
FROM (SELECT trade_id FROM trades GROUP BY trade_id HAVING COUNT(*) > 1) x
UNION ALL
SELECT 'trade_without_client', COUNT(*), 'Critical'
FROM trades t LEFT JOIN clients c USING (client_id) WHERE c.client_id IS NULL
UNION ALL
SELECT 'trade_without_instrument', COUNT(*), 'High'
FROM trades t LEFT JOIN instruments i USING (instrument_id) WHERE i.instrument_id IS NULL
UNION ALL
SELECT 'negative_commission', COUNT(*), 'High'
FROM trades WHERE commission < 0
UNION ALL
SELECT 'cash_operation_without_account', COUNT(*), 'Critical'
FROM cash_operations o LEFT JOIN accounts a USING (account_id) WHERE a.account_id IS NULL;

CREATE INDEX IF NOT EXISTS ix_trades_month_client ON trades (trade_date, client_id);
CREATE INDEX IF NOT EXISTS ix_trades_instrument ON trades (instrument_id);
CREATE INDEX IF NOT EXISTS ix_cash_ops_date_client ON cash_operations (operation_date, client_id);

-- Refresh after each successful ETL load:
-- REFRESH MATERIALIZED VIEW mart_brokerage_monthly;
