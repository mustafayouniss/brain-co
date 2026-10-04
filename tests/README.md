# 🧪 Test Suites & Architectural Invariant Enforcement

دليل منظومة الاختبارات لمشروع **Organizational Brain**:

- **`unit/`**: اختبارات الوحدة لكل طبقة (Backend, Frontend, Mobile, AI).
- **`isolation/`**: 🔒 **اختبارات العزل الصارم**: تضمن عدم تسرب أي بيانات بين القضايا (`Case Isolation`) أو بين المؤسسات (`Tenant Isolation`).
- **`invariant/`**: اختبارات تطابق الـ 17 مبدأ دستورياً التي تحكم سلوك النظام.
- **`e2e/`**: اختبارات السيناريوهات المتكاملة من طرف لطرف (WhatsApp Ingestion → Case Creation → Assistance → Human Validation).
- **`ai-evaluation/`**: قياسات دقة الاسترجاع والاستدلال وتوليد الاستشهادات القانونية على بيانات غير مرئية (`Unseen Corpus`).
- **`performance/`**: اختبارات الحمل وسرعة استجابة الـ API وطابور الرسائل (k6).
