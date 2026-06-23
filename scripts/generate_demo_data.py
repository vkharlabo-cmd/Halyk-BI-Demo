#!/usr/bin/env python3
"""Generate deterministic brokerage demo data and dashboard aggregates."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
random.seed(20260622)


def write_csv(name, headers, rows):
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / name).open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def weighted(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def month_start(d):
    return date(d.year, d.month, 1)


def main():
    managers = [
        (1, "Aruzhan Sadykova", "Retail"),
        (2, "Dias Akhmetov", "Retail"),
        (3, "Alina Kim", "Premium"),
        (4, "Timur Bekov", "Premium"),
        (5, "Aigerim Toleu", "Digital"),
        (6, "Nursultan Imanov", "Digital"),
        (7, "Marat Zhaksy", "Corporate"),
        (8, "Dana Lee", "Corporate"),
    ]
    instruments = [
        (1, "Equity", "HSBK", "KASE"), (2, "Equity", "KZTK", "KASE"),
        (3, "Equity", "AAPL", "NASDAQ"), (4, "Equity", "NVDA", "NASDAQ"),
        (5, "Bond", "KZGB10Y", "KASE"), (6, "Bond", "US10Y", "OTC"),
        (7, "ETF", "SPY", "NYSE"), (8, "ETF", "QQQ", "NASDAQ"),
        (9, "FX", "USD/KZT", "FX"), (10, "FX", "EUR/USD", "FX"),
        (11, "Equity", "KZAP", "KASE"), (12, "ETF", "GLD", "NYSE"),
    ]
    clients, accounts = [], []
    start, end = date(2025, 1, 1), date(2026, 6, 21)
    channels = ["Mobile App", "Branch", "Referral", "Paid Search", "Partner"]
    segments = ["Mass", "Affluent", "Premium", "Corporate"]
    for cid in range(1, 321):
        reg = start + timedelta(days=random.randint(0, (end - start).days - 5))
        segment = weighted(segments, [60, 24, 12, 4])
        manager_id = random.randint(1, 8)
        channel = weighted(channels, [44, 16, 16, 14, 10])
        status = weighted(["Active", "Dormant", "Closed"], [76, 18, 6])
        clients.append((cid, reg.isoformat(), segment, manager_id, channel, status))
        open_date = reg + timedelta(days=random.randint(0, 12))
        accounts.append((10000 + cid, cid, open_date.isoformat(), weighted(["Standard", "Premium"], [82, 18]), "Open" if status != "Closed" else "Closed"))

    trades = []
    trade_id = 1
    monthly = defaultdict(lambda: defaultdict(float))
    for cid, reg_text, segment, _, _, status in clients:
        reg = date.fromisoformat(reg_text)
        if status == "Closed" and random.random() < 0.55:
            continue
        base = {"Mass": 4, "Affluent": 8, "Premium": 13, "Corporate": 18}[segment]
        count = max(0, int(random.gauss(base, max(2, base * 0.55))))
        for _ in range(count):
            trade_date = reg + timedelta(days=random.randint(1, max(2, (end - reg).days)))
            if trade_date > end:
                trade_date = end
            instrument_id = weighted(range(1, 13), [12, 7, 10, 9, 8, 5, 12, 10, 13, 5, 5, 4])
            multiplier = {"Mass": 1, "Affluent": 2.8, "Premium": 6.5, "Corporate": 14}[segment]
            seasonality = 1 + 0.18 * math.sin((trade_date.month - 1) / 12 * 2 * math.pi)
            growth = 1 + ((trade_date - start).days / (end - start).days) * 0.35
            amount = round(random.lognormvariate(10.7, 0.75) * multiplier * seasonality * growth, 2)
            commission_rate = weighted([0.0008, 0.0012, 0.0018, 0.0025], [28, 40, 24, 8])
            commission = round(amount * commission_rate, 2)
            side = weighted(["BUY", "SELL"], [54, 46])
            trades.append((trade_id, cid, trade_date.isoformat(), instrument_id, amount, commission, side))
            m = month_start(trade_date).isoformat()
            monthly[m]["turnover"] += amount
            monthly[m]["commission"] += commission
            monthly[m]["trades"] += 1
            trade_id += 1

    # Intentional DQ exceptions for the interview page.
    trades.extend([
        (trade_id, 9999, "2026-05-14", 1, 450000.0, 540.0, "BUY"),
        (trade_id + 1, 42, "2026-05-18", 999, 275000.0, 330.0, "SELL"),
        (trade_id + 2, 55, "2026-06-03", 3, 190000.0, -250.0, "BUY"),
    ])
    trades.append(trades[25])  # duplicate trade_id

    cash_ops = []
    op_id = 1
    for cid, reg_text, segment, *_ in clients:
        reg = date.fromisoformat(reg_text)
        n = random.randint(1, 6)
        for _ in range(n):
            op_date = reg + timedelta(days=random.randint(0, max(1, (end - reg).days)))
            kind = weighted(["DEPOSIT", "WITHDRAWAL"], [72, 28])
            factor = {"Mass": 1, "Affluent": 3, "Premium": 7, "Corporate": 16}[segment]
            amount = round(random.lognormvariate(11.0, 0.8) * factor, 2)
            cash_ops.append((op_id, 10000 + cid, cid, op_date.isoformat(), kind, amount))
            m = month_start(op_date).isoformat()
            monthly[m]["deposits" if kind == "DEPOSIT" else "withdrawals"] += amount
            op_id += 1
    cash_ops.append((op_id, 99999, 9999, "2026-06-09", "DEPOSIT", 950000.0))

    write_csv("managers.csv", ["manager_id", "manager_name", "department"], managers)
    write_csv("instruments.csv", ["instrument_id", "instrument_type", "ticker", "market"], instruments)
    write_csv("clients.csv", ["client_id", "registration_date", "client_segment", "manager_id", "acquisition_channel", "status"], clients)
    write_csv("accounts.csv", ["account_id", "client_id", "open_date", "account_type", "status"], accounts)
    write_csv("trades.csv", ["trade_id", "client_id", "trade_date", "instrument_id", "trade_amount", "commission", "operation_type"], trades)
    write_csv("cash_operations.csv", ["operation_id", "account_id", "client_id", "operation_date", "operation_type", "amount"], cash_ops)

    active_by_month = defaultdict(set)
    last_trade_by_client = {}
    instrument_turnover = defaultdict(float)
    manager_commission = defaultdict(float)
    client_map = {row[0]: row for row in clients}
    for _, cid, trade_date, iid, amount, commission, _ in trades[:-4]:
        m = trade_date[:7] + "-01"
        active_by_month[m].add(cid)
        last_trade_by_client[cid] = max(last_trade_by_client.get(cid, trade_date), trade_date)
        instrument_turnover[iid] += amount
        manager_commission[client_map[cid][3]] += commission
    # Client activity remains valid when only a non-client attribute has a DQ issue.
    # Exclude the orphan client, but retain valid clients with an instrument or commission error.
    for _, cid, trade_date, *_ in trades:
        if cid in client_map:
            last_trade_by_client[cid] = max(last_trade_by_client.get(cid, trade_date), trade_date)
    rows = []
    prev_commission = None
    for m in sorted(monthly):
        metrics = monthly[m]
        new_clients = sum(1 for c in clients if c[1][:7] == m[:7])
        commission = metrics["commission"]
        mom = None if prev_commission in (None, 0) else (commission / prev_commission - 1)
        rows.append({
            "month": m[:7], "active_clients": len(active_by_month[m]), "new_clients": new_clients,
            "trades": int(metrics["trades"]), "turnover": round(metrics["turnover"], 2),
            "commission": round(commission, 2), "deposits": round(metrics["deposits"], 2),
            "withdrawals": round(metrics["withdrawals"], 2),
            "net_inflow": round(metrics["deposits"] - metrics["withdrawals"], 2), "mom": mom,
        })
        prev_commission = commission
    latest = rows[-1]
    dashboard = {
        "as_of": end.isoformat(), "monthly": rows,
        "latest": latest,
        "total_clients": len(clients),
        "dormant_clients": sum(
            1
            for c in clients
            if c[0] not in last_trade_by_client
            or date.fromisoformat(last_trade_by_client[c[0]]) < end - timedelta(days=90)
        ),
        "first_trade_conversion": round(len({t[1] for t in trades[:-4]}) / len(accounts), 4),
        "instrument_turnover": [{"label": next(i[2] for i in instruments if i[0] == iid), "value": round(value, 2)} for iid, value in sorted(instrument_turnover.items(), key=lambda x: -x[1])[:8]],
        "manager_commission": [{"label": next(m[1] for m in managers if m[0] == mid), "value": round(value, 2)} for mid, value in sorted(manager_commission.items(), key=lambda x: -x[1])],
        "quality": [
            {"check": "Дубли идентификаторов сделок", "count": 1, "severity": "Критический", "css": "critical"},
            {"check": "Сделка без найденного клиента", "count": 1, "severity": "Критический", "css": "critical"},
            {"check": "Сделка без найденного инструмента", "count": 1, "severity": "Высокий", "css": "high"},
            {"check": "Отрицательная комиссия", "count": 1, "severity": "Высокий", "css": "high"},
            {"check": "Денежная операция без счёта или клиента", "count": 1, "severity": "Критический", "css": "critical"},
        ],
    }
    write_csv(
        "mart_brokerage_monthly.csv",
        ["month", "active_clients", "new_clients", "trades_count", "trading_turnover", "commission_revenue", "deposits", "withdrawals", "net_inflow", "mom_revenue_growth"],
        [(r["month"], r["active_clients"], r["new_clients"], r["trades"], r["turnover"], r["commission"], r["deposits"], r["withdrawals"], r["net_inflow"], "" if r["mom"] is None else round(r["mom"], 6)) for r in rows],
    )
    write_csv(
        "data_quality_checks.csv",
        ["check_name", "issue_count", "severity", "publication_rule"],
        [(q["check"], q["count"], q["severity"], "БЛОКИРОВАТЬ" if q["css"] == "critical" else "ПРЕДУПРЕЖДЕНИЕ") for q in dashboard["quality"]],
    )
    (ROOT / "dashboard").mkdir(exist_ok=True)
    (ROOT / "dashboard" / "dashboard_data.js").write_text("window.BROKERAGE_DATA = " + json.dumps(dashboard, ensure_ascii=False) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
