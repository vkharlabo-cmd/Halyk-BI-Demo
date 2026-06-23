# Power Query: загрузка CSV

Сначала создайте текстовый параметр `RootPath` со значением `C:\HalykBI\data`. Затем создайте пустые запросы с указанными именами и вставьте код через «Расширенный редактор».

## clients

```powerquery
let
    Source = Csv.Document(File.Contents(RootPath & "\\clients.csv"), [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"client_id", Int64.Type}, {"registration_date", type date}, {"client_segment", type text}, {"manager_id", Int64.Type}, {"acquisition_channel", type text}, {"status", type text}})
in
    Types
```

## accounts

```powerquery
let
    Source = Csv.Document(File.Contents(RootPath & "\\accounts.csv"), [Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"account_id", Int64.Type}, {"client_id", Int64.Type}, {"open_date", type date}, {"account_type", type text}, {"status", type text}})
in
    Types
```

## trades

```powerquery
let
    Source = Csv.Document(File.Contents(RootPath & "\\trades.csv"), [Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"trade_id", Int64.Type}, {"client_id", Int64.Type}, {"trade_date", type date}, {"instrument_id", Int64.Type}, {"trade_amount", Currency.Type}, {"commission", Currency.Type}, {"operation_type", type text}})
in
    Types
```

## cash_operations

```powerquery
let
    Source = Csv.Document(File.Contents(RootPath & "\\cash_operations.csv"), [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"operation_id", Int64.Type}, {"account_id", Int64.Type}, {"client_id", Int64.Type}, {"operation_date", type date}, {"operation_type", type text}, {"amount", Currency.Type}})
in
    Types
```

## instruments

```powerquery
let
    Source = Csv.Document(File.Contents(RootPath & "\\instruments.csv"), [Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"instrument_id", Int64.Type}, {"instrument_type", type text}, {"ticker", type text}, {"market", type text}})
in
    Types
```

## managers

```powerquery
let
    Source = Csv.Document(File.Contents(RootPath & "\\managers.csv"), [Delimiter=",", Columns=3, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"manager_id", Int64.Type}, {"manager_name", type text}, {"department", type text}})
in
    Types
```

CSV-файлы `mart_brokerage_monthly.csv` и `data_quality_checks.csv` можно загрузить для сверки, но визуалы должны использовать исходные таблицы и DAX-меры. Тогда модель остаётся интерактивной и реагирует на фильтры.
