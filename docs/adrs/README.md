# 📋 Architecture Decision Records (ADRs)

سجل القرارات المعمارية للمشروع. كل قرار يغير في المعمارية يجب توثيقه هنا ولا يجوز مخالفة دستور المشروع دون تعديل رسمي.

- **ADR-001**: اعتماد المعمارية ثلاثية الطبقات (Three-Layer Intelligence Model).
- **ADR-002**: اعتماد معمارية التخزين المتعدد (Multi-Store Architecture: PostgreSQL, pgvector, Redis, Neo4j, MinIO).
- **ADR-003**: اعتماد منهجية التطوير عبر الحلقات المتكاملة رأسياً (Ring-Based Vertical Development).
- **ADR-004**: العزل الصارم للبيانات على مستوى القضايا والمؤسسات (Strict Multi-Tenant & Case Isolation).
- **ADR-005**: فرض المراجعة البشرية الإلزامية لترقية المعرفة (Human-in-the-Loop Validation Gate).
- **ADR-006**: اعتماد معمارية العمل بدون إنترنت لتطبيق الموبايل (Flutter Offline-First Sync with Hive/Isar).
- **ADR-007**: فصل الاستقبال الفوري للرسائل عن الاستدلال البطيء (Observation Buffering with Redis/Kafka).
