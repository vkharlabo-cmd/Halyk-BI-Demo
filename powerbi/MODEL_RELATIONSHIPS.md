# Модель данных Power BI

Используйте одностороннюю фильтрацию от стороны `1` к стороне `*`. Не включайте двунаправленную фильтрацию без отдельной причины.

| Сторона 1 | Сторона * | Активность |
|---|---|---|
| managers[manager_id] | clients[manager_id] | Активная |
| clients[client_id] | accounts[client_id] | Активная |
| clients[client_id] | trades[client_id] | Активная |
| accounts[account_id] | cash_operations[account_id] | Активная |
| instruments[instrument_id] | trades[instrument_id] | Активная |
| Календарь[Date] | trades[trade_date] | Активная |
| Календарь[Date] | cash_operations[operation_date] | Активная |
| Календарь[Date] | clients[registration_date] | Неактивная |
| Календарь[Date] | accounts[open_date] | Неактивная |

```text
managers 1 ── * clients 1 ── * accounts 1 ── * cash_operations
                     │
                     └─────── * trades * ── 1 instruments

Календарь 1 ── * trades
Календарь 1 ── * cash_operations
```

Почему это «звезда»: справочники используются для фильтрации и группировки, а таблицы событий содержат числовые показатели для суммирования.
