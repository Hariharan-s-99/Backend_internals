-----

# 🧠 WiredTiger Storage Engine Summary: The Complete Picture

WiredTiger is MongoDB's default storage engine, designed for high concurrency, performance, and compression, built on **B+ Tree** structures and **MVCC**.

-----

## 1\. Core Storage Architecture: Everything is a B+ Tree 🌳

Each **collection** and **index** is an independent B+ Tree, stored in its own separate `.wt` file.

| Component | B+ Tree Role | Key Stored (Ordered By) | Value Stored |
| :--- | :--- | :--- | :--- |
| **Collection (Data)** | Stores document data. | Document's **`_id`** | The **full BSON document** |
| **Index (Any Type)** | Stores sorted keys. | Indexed field value(s) | Pointer to the document's `_id` |

### A. Internal WiredTiger Identifiers (The Catalog)

MongoDB maps human-readable names to these internal WiredTiger files, managed within the internal `_mdb_catalog`. **Each B+ Tree gets a unique file ID.**

**Example Mapping (Using Collection: `test.userrs`):**

```json
{
  "ns": "test.userrs",
  "ident": "collection-0-4581230007890123456",
  "idxIdent": {
    "_id_": "index-1-1122334455667788990",
    "name_1_city_1": "index-2-9090909080706050403"
  }
}
```

  * The collection **`test.userrs`** is physically stored in the file **`collection-0-4581230007890123456.wt`**.
  * The primary index (`_id_`) is stored in **`index-1-1122334455667788990.wt`**.
  * The compound index is stored in **`index-2-9090909080706050403.wt`**.

### B. B+ Tree Tables (Conceptual Data Insertion)

The files referenced above (`collection-0-...` and `index-2-...`) contain B+ Trees structured as follows, based on conceptual data insertion (e.g., `_id: 1, city: "New York", age: 30`):

#### Collection B+ Tree (Data) - Sorted by `_id`

  * **File:** `collection-0-4581230007890123456.wt`

| B+ Tree Level | Key Stored | Value Stored (BSON Document Snippet) |
| :--- | :--- | :--- |
| **Leaf Node** | `1` | `{ _id: 1, name: "Alice", city: "New York", ... }` |
| **Leaf Node** | `2` | `{ _id: 2, name: "Bob", city: "London", ... }` |
| **Leaf Node** | `3` | `{ _id: 3, name: "Charlie", city: "Paris", ... }` |

#### Compound Index B+ Tree (e.g., `{ city: 1, age: -1 }`)

  * **File:** `index-2-9090909080706050403.wt`

| B+ Tree Level | Key Stored (Concatenated) | Value Stored (Pointer) |
| :--- | :--- | :--- |
| **Leaf Node** | `["London", 28]` | `2` (Points to document with `_id: 2`) |
| **Leaf Node** | `["New York", 30]` | `1` (Points to document with `_id: 1`) |
| **Leaf Node** | `["Paris", 25]` | `3` (Points to document with `_id: 3`) |

-----

## 2\. Concurrency Model: Document-Level MVCC 🕰️

WiredTiger ensures high concurrency with strict consistency using **Document-Level Concurrency** and **MVCC**.

| Mechanism | Description | Example Implication |
| :--- | :--- | :--- |
| **MVCC (Optimistic)** | Writers create new versions; readers see older, consistent versions. | Writers **NEVER block Readers** and vice-versa, achieving high throughput. |
| **WiredTigerHS.wt** | The **Durable History Store** holds prior committed versions (*before-images*) for MVCC snapshot reads. | A long-running query can see a consistent state without impacting current writes. |
| **Intent Locks** | **Intent Shared (IS)** and **Intent Exclusive (IX)** locks are used at the collection level but are **compatible** and do not block normal CRUD operations. | Thousands of concurrent reads and writes proceed in parallel. |

-----

## 3\. Data Lifecycle: Cache, Journal, and Checkpoints 🔄

Data moves from volatile memory (RAM) to durable disk storage.

### A. In-Memory Stage (WiredTiger Cache - RAM)

1.  **Unified Cache:** All **data pages** and **index pages** share a single memory pool (default $\approx 50\%$ of RAM minus 1GB), managed by **LRU** eviction.
2.  **Journaling:** Operation is logged to the **Write-Ahead Log (WAL) / Journal** for crash recovery.

### B. Disk Persistence

1.  **Reconciliation:** Dirty in-memory pages are converted to the on-disk format.
2.  **Checkpoint:** Regularly (default **60 seconds**), a **checkpoint** creates a consistent snapshot, flushing data to the final `.wt` files.
3.  **Compression:** Blocks (default **4KB**) are compressed (**Snappy** is the default) before being written to disk.

<!-- end list -->

```
```
