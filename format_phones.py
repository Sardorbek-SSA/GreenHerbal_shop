import os
import sys
import django
import re

# Django ni sozlash
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from shop.models import Order

def format_phone(phone):
    if not phone:
        return ""
    
    digits = re.sub(r'\D', '', str(phone))
    
    if len(digits) >= 9:
        last_9 = digits[-9:]
        return f"+998 {last_9[0:2]} {last_9[2:5]} {last_9[5:7]} {last_9[7:9]}"
    return phone

def main():
    print("🚀 Telefon raqamlarini formatlash")
    print("=" * 50)
    
    orders = Order.objects.all()
    total = orders.count()
    
    print(f"📊 {total} ta buyurtma topildi")
    
    # Avval test uchun 5 tasi
    print("\n🔬 TEST (dastlabki 5 ta):")
    print("-" * 40)
    
    for i in range(min(5, total)):
        order = orders[i]
        new_phone = format_phone(order.phone)
        print(f"{i+1}. {order.order_number}")
        print(f"   Eski: {order.phone}")
        print(f"   Yangi: {new_phone}")
    
    # Davom etish
    confirm = input("\n❓ Barchasini yangilashni istaysizmi? (ha/yoq): ").lower()
    if confirm not in ['ha', 'h', 'yes', 'y']:
        print("❌ Bekor qilindi!")
        return
    
    # Yangilash
    updated = 0
    print("\n⏳ Yangilash boshlanmoqda...")
    
    for i, order in enumerate(orders, 1):
        # Progress ko'rsatish
        if i % 10 == 0 or i == total:
            progress = (i / total) * 100
            print(f"\r📊 {i}/{total} ({progress:.1f}%)", end="")
        
        new_phone = format_phone(order.phone)
        
        if order.phone != new_phone:
            order.phone = new_phone
            order.save()
            updated += 1
    
    print(f"\n\n✅ {updated} ta yangilandi!")
    print("✅ Barcha raqamlar endi +998 90 123 45 67 formatida!")

if __name__ == "__main__":
    main()