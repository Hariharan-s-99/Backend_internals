# 🧑‍💻 Distributed Systems & Backend Engineering Explorations

This repository serves as a personal laboratory for implementing core concepts and complex algorithms vital to **scalable backend systems** and **distributed computing**. It combines practical Python code implementations with detailed, academic write-ups for a complete understanding of foundational concepts.

---

## 📂 Repository Structure

| Directory | Content | Description |
| :--- | :--- | :--- |
| **`backendEngineering/`** | **Practical Code** | Contains functional Python implementations of core backend algorithms, such as hashing, load balancing, and concurrency models. |
| **`writeUps/`** | **Theoretical Deep Dives** | Houses detailed Markdown files (`.md`) that explore complex technical topics, database internals, and architectural patterns. |
| `README.md` | Repository Entry | This file, providing an overview and navigation guide. |

---

## ⚙️ BackendEngineering: Implemented Algorithms

This folder contains Python scripts demonstrating key distributed systems concepts.

| File/Concept | Description | Key Takeaway |
| :--- | :--- | :--- |
| **Consistent Hashing** | Implementation of **Normal Hashing (Modulo)** vs. **Consistent Hashing** using Python classes. | Demonstrates how Consistent Hashing drastically reduces **data migration** when nodes are added or removed (e.g., re-mapping only $K/N$ keys instead of nearly all keys). |

| **Run the Demo** |
| :--- |
| The `main()` function provides a complete side-by-side comparison of re-mapping counts between the two hashing methods. |

---

## 📚 writeUps: Detailed Architectural Summaries

This folder contains deep-dive summaries on complex topics. The goal of these files is to provide a complete, structured understanding of advanced systems concepts.

### Featured Write-Up: WiredTiger Storage Engine Summary 🧠

This document provides a comprehensive overview of MongoDB's default storage engine, WiredTiger.

| Focus Area | Key Concept | Core Mechanism |
| :--- | :--- | :--- |
| **Core Architecture** | Everything is a **B+ Tree** (Collections and Indexes are separate B+ Trees). | Documents are stored by `_id`. Indexes store pointers to the `_id`. |
| **Concurrency Model** | High concurrency with strict consistency. | **Document-Level MVCC** (Multi-Version Concurrency Control) ensures readers never block writers. |
| **Durability** | Data persistence and crash recovery. | **Write-Ahead Log (Journal)** and periodic **Checkpoints** for consistent snapshots. |

---

## 🤝 Contribution & Learning

This repository is for personal learning and documentation. Feel free to explore the code, read the write-ups, and use them as a resource for understanding key backend engineering principles!