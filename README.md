# سامانه مدیریت مالی و اقساط

**Persian Wallet & Installment App**

یک سامانه مدیریت مالی مبتنی بر Django با رابط کاربری کاملاً فارسی و راست‌چین (RTL) برای مدیریت کاربران، کیف پول، تراکنش‌ها و اقساط. این پروژه از تقویم شمسی (Jalali)، نمودارهای تحلیلی و دفترچه پویا برای برنامه پرداخت اقساط استفاده می‌کند.

## ویژگی‌ها

- مدیریت کاربران و کیف پول (User & Wallet Management)
- ثبت‌نام، ورود، خروج و حذف حساب کاربری
- واریز، برداشت و برداشت حداکثر موجودی
- تاریخچه تراکنش‌ها با مبلغ، نوع، توضیحات و موجودی پس از تراکنش
- تاریخچه ورودها به همراه زمان و IP
- مدیریت اقساط با تقویم شمسی (Installment Management with Jalali Calendar)
- تولید پویا و ماهانه دفترچه اقساط با پشتیبانی از مبلغ باقی‌مانده
- ثبت پرداخت‌های معوقه و تسویه معوقه
- نمودارهای تحلیلی (Analytical Charts) با Chart.js
- رابط کاربری کاملاً راست‌چین و فارسی (Fully RTL & Persian UI)
- نمایش تمامی مبالغ به تومان و بدون اعشار

## پیش‌نیازها

- Python 3.10 یا بالاتر
- Git

## نصب و اجرا

```bash
git clone https://github.com/ixerxesboush/django-persian-wallet.git
cd django-persian-wallet
```

### Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

ساخت ابرکاربر اختیاری است و برای استفاده از پنل مدیریت Django انجام می‌شود. پس از اجرای سرور، برنامه در آدرس `http://127.0.0.1:8000/` در دسترس است.

## ساختار پروژه

```text
django-persian-wallet/
├── core/                 # تنظیمات، URLها و ابزارهای عمومی
├── users/                # مدل کاربر، احراز هویت و تاریخچه ورود
├── wallet/               # کیف پول، تراکنش‌ها و تاریخچه مالی
├── installments/        # اقساط، پرداخت‌ها و معوقه‌ها
├── templates/            # قالب پایه RTL
├── static/               # فایل‌های CSS
├── manage.py
├── requirements.txt
└── README.md
```

## واحد پول

تمامی مبالغ سامانه به **تومان** هستند، نه ریال. تاریخ‌های قابل مشاهده در رابط کاربری به تقویم شمسی نمایش داده می‌شوند.
