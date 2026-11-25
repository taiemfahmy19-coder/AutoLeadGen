# دليل تشغيل AutoLeadGen V3

## 1. التشغيل بنقرة واحدة (واجهة الويب Streamlit)
انقر نقراً مزدوجاً على الملف:
```
Start_AutoLeadGen.bat
```
أو عبر سطر الأوامر:
```powershell
python -m streamlit run app.py
```
- ستفتح واجهة تسجيل الدخول الآمنة.
- عند أول تشغيل، أنشئ حساب المدير الافتراضي أو ادخل بالحساب `admin` وكلمة المرور `admin123`.

---

## 2. تشغيل خادم FastAPI للتحكم عن بُعد والتطبيق
انقر نقراً مزدوجاً على الملف:
```
Start_V3_API.bat
```
أو عبر سطر الأوامر:
```powershell
python -m uvicorn api.main:app --host 0.0.0.0 --port 8502
```
- يعمل الخادم على المنفذ `8502`.
- يوفر توثيق Swagger التفاعلي عبر: `http://localhost:8502/docs`.

---

## 3. تشغيل الاختبارات الشاملة (All Tests)
للتحقق من سلامة جميع أجزاء النظام:
```powershell
python -m pytest tests/ -v
```
