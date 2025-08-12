# Eclipse Ditto RQL Support Matrix

## ✅ SUPPORTED CASES (RQL in Ditto)

| Query Type             | Example                                  | Notes                         |
|------------------------|------------------------------------------|-------------------------------|
| Property equality      | `eq(features/x/properties/y,true)`       | Works with any path           |
| Logical conditions     | `and(...)`, `or(...)`, `not(...)`        | Arbitrarily nested            |
| Comparisons            | `gt`, `lt`, `ge`, `le`, `ne`             | On numeric, string, timestamp |
| Existence              | `exists(features/x/properties/y)`        | Scalar or object properties   |
| Path indexing (arrays) | `features/zones/0/width`                 | Only fixed index              |
| Regular expressions    | `matches(attributes/id,'^camera.*')`     | Simple patterns only          |

---

## 🟡 PARTIALLY SUPPORTED CASES

| Case                      | Notes                                     | Workaround                        |
|---------------------------|-------------------------------------------|-----------------------------------|
| Array access              | Only fixed index, like `/0/field`         | Pre-process to extract summary    |
| Flattened nested object   | Works if flattened during ingestion       | See `intrusionEvent.timestamp`    |
| Array length check        | Not directly supported                    | Add a `zonesCount` attribute      |
| Timestamp comparison      | Only when in scalar fields                | Flatten or precompute timestamps  |
| Type coercion             | Inconsistent behavior                     | Avoid mixed types in schema       |

---

## ❌ NOT SUPPORTED CASES

| Query Type                 | Example                                          | Why Not                                  |
|----------------------------|--------------------------------------------------|------------------------------------------|
| JSONPath-style filtering   | `zones[?(@.width>0.5)]`                          | Ditto RQL parser does not support it     |
| Deep array scan            | `gt(intrusionEvents[*].timestamp,'2025-07-22')`  | No `[*]` wildcard support                |
| Subdocument pattern match  | `eq(address,{city: 'X'})`                        | No deep object structure match           |
| Dynamic array field access | `zones[zone.id='zone-1']`                        | Not parseable in RQL                     |
| Math / aggregations        | `avg(zones[].width)`                             | No aggregation support                   |
| Multi-array filter chaining| Nested `exists` with inner filters               | Parsing fails                            |

---

## ✅ Recommended Patterns (for unsupported cases)

To enable queries that are not directly supported, pre-process or augment your data model:

| Need                      | Add Preprocessed Field                    |
|---------------------------|-------------------------------------------|
| Check if any zone is wide | `attributes/hasWideZone = true`           |
| Last intrusion timestamp  | `attributes/lastIntrusionTimestamp = ...` |
| Intrusion zone ID         | `attributes/lastIntrusionZone = 'zone-2'` |
| Has recent intrusion      | `attributes/hasRecentIntrusion = true`    |

---

# ⚠️ Potentially Dangerous RQL Queries in Eclipse Ditto

These queries, while valid, can negatively impact performance due to how Ditto translates RQL into MongoDB queries.

| Type | RQL Query | Why It's Dangerous |
|------|-----------|---------------------|
| **Full wildcard** | `filter=exists(features/*)` | Scans all feature documents; wildcard is expensive. |
| **Deep wildcard** | `filter=exists(features/**/timestamp)` | Recursively searches timestamp in all nested objects. High CPU/memory. |
| **Unbounded search** | `filter=gt(attributes/timestamp,'1900-01-01T00:00:00Z')` | Forces full collection scan if no index on timestamp. |
| **Large `in()` sets** | `filter=in(attributes/type, ['a', 'b', ..., 'z', ..., 'zz'])` | Long `$in` clauses degrade query planner performance. |
| **Regex or partial string match** | `filter=like(attributes/location, '*ice*')` | No index support for wildcard-start regex. Slows DB heavily. |
| **Unindexed sort** (if applicable via API options) | `?sort=features/health/properties/uptimeSeconds` | Mongo will resort to memory sort if field isn’t indexed. |
| **Array element scan** | `filter=exists(features/analytics/properties/intrusionEvents[?(@.zone='zone-2' && @.timestamp > '2025-07-22T00:00:00Z')])` | Nested array traversal with logical conditions can be expensive. |
| **No pagination** | `GET /search/things?option=size(100000)` | Loads huge datasets in one call; can OOM MongoDB or Ditto. |
| **Recursive object search** | `filter=exists(features/**)` | Recursive filter through all objects, bad on large models. |
| **Multiple deep filters with AND/OR** | `and(eq(features/health/properties/cpuLoad, 99.9), exists(features/motionDetection/properties/zones[?(@.width > 0.01)]), eq(features/analytics/properties/peopleCount/today, 9999))` | Complex filter trees result in expensive aggregation pipelines. |

---