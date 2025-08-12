# TD best practices

## How `/search/things` Works
- It searches indexed JSON fields from Things.

- Supports RQL filters on:
    - attributes
    - features.<featureName>.properties

- It does not support:
    - Searching inside thingId subparts (without full value)
    - Deeply nested arrays/objects
    - Non-indexed fields
    - Mongo-specific operators or arbitrary JavaScript queries

## 🔴 What to Avoid in Thing JSON for RQL Search Performance

1. Deeply Nested Structures: __Ditto cannot index deeply into nested objects.__
2. Arrays with Complex Objects: __RQL can’t query inside array of objects.__
3. Large or Sparse Boolean Flags: Lots of optional booleans (like in CardAPI) increase storage bloat and provide low filter value unless tightly controlled. 
4. Very Large Feature Blocks
5. Dynamic Keys: __Static RQL queries will not be able to search consistently across variable feature names__
6. Dates as Strings with Off Formats: __RQL does not support full datetime parsing unless it's in ISO 8601 UTC format.__

## ⚠️ What is Not Supported by Ditto RQL
| RQL Limitation                                       | Details                                                       |
| ---------------------------------------------------- | ------------------------------------------------------------- |
| No querying inside array of objects                  | Can't filter on `array[i].field eq value`                     |
| No full-text search                                  | Only exact or regex match, no fuzzy/partial token search      |
| No multi-level AND/OR inside array filters           | Nested logic inside arrays isn't supported                    |
| No support for custom expressions or computed fields | Can't filter on `attr1 + attr2 > 100`                         |
| No joins or subqueries                               | All queries are over a **single Thing**, no cross-Thing logic |
| No deep regex support                                | Only flat path regex matching                                 |
| No access to policy metadata                         | Can't search based on ACLs or assigned policies               |
| No `like`, `contains`, `startsWith`                  | Only `eq`, `ne`, `gt`, `lt`, `regex`, etc.                    |


## ✅ Best Practices Summary

| Category                 | Best Practice                                                    |
| ------------------------ | ---------------------------------------------------------------- |
| Structure depth          | Keep `features.*.properties.*` max 2 levels deep                 |
| Array contents           | Use flat strings or primitive values                             |
| Keys                     | Avoid dynamic keys, use fixed schema                             |
| Queryable fields         | Precompute or flatten into `attributes` or `feature.properties`  |
| Voluminous fields        | Offload to separate config document or reference                 |
| Date/time values         | Always use ISO 8601 UTC strings                                  |
| Enum-like flags          | Use string lists, not tons of booleans                           |
| Repeated pattern configs | Store once and reuse via references (if identical across Things) |
