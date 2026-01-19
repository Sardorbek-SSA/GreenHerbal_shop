from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from .models import Herbal, Order, OrderItem, PickupPoint
import random
import string
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

def home(request):
    herbals = Herbal.objects.filter(is_home=True)[:4]
    return render(request, 'shop/home.html', {'herbals': herbals})

def product_list(request):
    herbals = Herbal.objects.all()
    return render(request, 'shop/products.html', {'herbals': herbals})

def product_detail(request, pk):
    herbal = get_object_or_404(Herbal, id=pk)
    related_products = Herbal.objects.exclude(id=pk)[:4]
    return render(request, 'shop/product_detail.html', {
        'herbal': herbal,
        'related_products': related_products
    })

def add_to_cart(request, pk):
    if request.method == 'POST':
        herbal = get_object_or_404(Herbal, id=pk)
        
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
        
        cart = request.session.get('cart', {})
        
        product_id = str(pk)
        
        if product_id in cart:
            cart[product_id]['qty'] += quantity
            cart[product_id]['total'] = cart[product_id]['qty'] * float(herbal.price)
        else:
            cart[product_id] = {
                'id': herbal.id,
                'name': herbal.name,
                'price': float(herbal.price),
                'qty': quantity,
                'image_url': herbal.image.url if herbal.image else '',  # ✅ To'g'ri format
                'total': float(herbal.price) * quantity
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        
        request.session['cart_message'] = f'{herbal.name} savatga qo\'shildi!'
        
        return redirect('shop:cart_view')

    return redirect('shop:product_detail', pk=pk)

def cart_view(request):
    cart = request.session.get('cart', {})
    
    if not cart:
        return render(request, 'shop/cart.html', {
            'cart': {},
            'subtotal': 0,
            'shipping': 0,
            'tax': 0,
            'total': 0,
            'cart_message': request.session.pop('cart_message', None)
        })
    
    subtotal = 0
    for item in cart.values():
        subtotal += item['total']
    
    # Yetkazib berish: 50,000 so'mdan ko'p bo'lsa bepul
    shipping = 0 if subtotal >= 50000 else 10000
    
    # tax = subtotal * 0.08  # 8% QQS
    
    total = subtotal + shipping
    
    context = {
        'cart': cart,
        'subtotal': round(subtotal, 2),
        'shipping': shipping,
        'total': round(total, 2),
        'cart_message': request.session.pop('cart_message', None)
    }
    
    return render(request, 'shop/cart.html', context)

def remove_from_cart(request, pk):
    cart = request.session.get('cart', {})
    product_id = str(pk)
    
    if product_id in cart:
        product_name = cart[product_id]['name']
        del cart[product_id]
        request.session['cart'] = cart
        request.session.modified = True
        request.session['cart_message'] = f'{product_name} savatdan o\'chirildi!'
    
    return redirect('shop:cart_view')

def increase_quantity(request, pk):
    """Miqdorni oshirish"""
    cart = request.session.get('cart', {})
    product_id = str(pk)
    
    if product_id in cart:
        cart[product_id]['qty'] += 1
        cart[product_id]['total'] = cart[product_id]['qty'] * cart[product_id]['price']
        request.session['cart'] = cart
        request.session.modified = True
    
    return redirect('shop:cart_view')

def decrease_quantity(request, pk):
    """Miqdorni kamaytirish"""
    cart = request.session.get('cart', {})
    product_id = str(pk)
    
    if product_id in cart:
        if cart[product_id]['qty'] > 1:
            cart[product_id]['qty'] -= 1
            cart[product_id]['total'] = cart[product_id]['qty'] * cart[product_id]['price']
        else:
            del cart[product_id]
            request.session['cart_message'] = 'Mahsulot savatdan o\'chirildi!'
        
        request.session['cart'] = cart
        request.session.modified = True
    
    return redirect('shop:cart_view')

def clear_cart(request):
    request.session['cart'] = {}
    request.session.modified = True
    request.session['cart_message'] = 'Savat tozalandi!'
    return redirect('shop:cart_view')

def about(request):
    return render(request, 'shop/about.html')

def contact(request):
    return render(request, 'shop/contact.html')

def generate_order_number():
    """Buyurtma raqamini generatsiya qilish"""
    timestamp = timezone.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=6))
    return f'B-{timestamp}-{random_str}'

def checkout(request):
    if request.method == 'GET':
        cart = request.session.get('cart', {})
        
        if not cart:
            messages.warning(request, 'Savat boʻsh!')
            return redirect('shop:cart_view')
        
        subtotal = sum(item['total'] for item in cart.values())
        
        # shipping = 0 if subtotal >= 50000 else 10000
        
        total = subtotal
        
        pickup_points = PickupPoint.objects.filter(is_active=True)
        
        context = {
            'cart': cart,
            'subtotal': subtotal,
            'total': total,
            'pickup_points': pickup_points,
        }
        return render(request, 'shop/checkout.html', context)
    
    elif request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash_pickup')
        
        order_id = 'ORD' + str(random.randint(10000, 99999))
        
        order_data = {
            'full_name': request.POST.get('full_name', ''),
            'phone': request.POST.get('phone', ''),
            'email': request.POST.get('email', ''),
            'pickup_point_id': request.POST.get('pickup_point', ''),
            'payment_method': payment_method,
            'notes': request.POST.get('notes', ''),
        }
        request.session['order_data'] = order_data
        request.session['order_id'] = order_id
        
        if payment_method == 'cash_pickup':
            return redirect('shop:order_confirmation')
        else:
            return redirect('shop:online_payment', payment_method=payment_method)

def order_confirmation(request):
    """Buyurtma tasdiqlash sahifasi"""
    order_data = request.session.get('order_data', {})
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, 'Savat boʻsh!')
        return redirect('shop:cart_view')
    
    try:
        order_number = generate_order_number()
        
        pickup_point = None
        pickup_point_id = order_data.get('pickup_point_id')
        if pickup_point_id:
            try:
                pickup_point = PickupPoint.objects.get(id=pickup_point_id)
            except PickupPoint.DoesNotExist:
                pickup_point = None
        
        subtotal = sum(item['total'] for item in cart.values())
        # shipping = 0 if subtotal >= 50000 else 10000
        total = subtotal

        order = Order.objects.create(
            order_number=order_number,
            full_name=order_data.get('full_name', 'Mijoz'),
            phone=order_data.get('phone', ''),
            email=order_data.get('email', ''),
            pickup_point=pickup_point,
            payment_method=order_data.get('payment_method', 'cash_pickup'),
            notes=order_data.get('notes', ''),
            subtotal=subtotal,
            total=total,
            payment_status=(order_data.get('payment_method') != 'cash_pickup'),
            status='confirmed' if order_data.get('payment_method') != 'cash_pickup' else 'pending',
        )
        
        for product_id, item in cart.items():
            try:
                herbal = Herbal.objects.get(id=item['id'])
            except Herbal.DoesNotExist:
                herbal = None
            
            OrderItem.objects.create(
                order=order,
                herbal=herbal,
                product_name=item['name'],
                product_price=item['price'],
                quantity=item['qty'],
                total_price=item['total'],
            )
        
        request.session['cart'] = {}
        request.session['last_order_id'] = order.id
        request.session['last_order_number'] = order.order_number
        request.session.modified = True
        
        context = {
            'order': order,
            'order_number': order.order_number,
            'payment_method': order.payment_method,
            'full_name': order.full_name,
            'phone': order.phone,
            'total': order.total,
            'message': 'Buyurtmangiz muvaffaqiyatli saqlandi!' if order.payment_method == 'cash_pickup' else 'To\'lov muvaffaqiyatli amalga oshirildi!',
        }
        
        messages.success(request, f'Buyurtma raqamingiz: {order.order_number}')
        
    except Exception as e:
        print(f"❌ Xatolik: {str(e)}")
        messages.error(request, f'Buyurtma saqlashda xatolik: {str(e)}')
        
        order_number = request.session.get('order_id', 'ORD' + str(random.randint(10000, 99999)))
        
        subtotal = sum(item['total'] for item in cart.values())
        # shipping = 0 if subtotal >= 50000 else 10000
        total = subtotal
        
        context = {
            'order_number': order_number,
            'payment_method': order_data.get('payment_method', 'cash_pickup'),
            'full_name': order_data.get('full_name', ''),
            'phone': order_data.get('phone', ''),
            'total': total,
            'message': 'Buyurtma ma\'lumotlari saqlanmadi. Iltimos, administrator bilan bog\'laning.',
        }
        
        request.session['cart'] = {}
        request.session.modified = True
    
    return render(request, 'shop/order_confirmation.html', context)

def my_orders(request):
    """Mening buyurtmalarim sahifasi"""
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        
        # Telefon raqamini tozalash
        def clean_phone_number(phone_str):
            import re
            cleaned = re.sub(r'\D', '', str(phone_str))
            
            # Oxirgi 9 raqam
            if len(cleaned) >= 9:
                return cleaned[-9:]
            return cleaned
        
        phone_clean = clean_phone_number(phone)
        
        print(f"DEBUG: Original phone: {phone}")
        print(f"DEBUG: Cleaned phone: {phone_clean}")
        
        if len(phone_clean) != 9:
            messages.error(request, 'Iltimos, to\'g\'ri telefon raqamini kiriting (9 raqam).')
            return render(request, 'shop/my_orders.html')
        
        # Database dan qidirish
        orders = Order.objects.all()
        matching_orders = []
        
        for order in orders:
            # Order telefonini tozalash
            order_phone_clean = clean_phone_number(order.phone)
            
            # Agar tozalangan raqamlar mos kelsa
            if order_phone_clean == phone_clean:
                matching_orders.append(order)
        
        if matching_orders:
            return render(request, 'shop/my_orders.html', {
                'orders': matching_orders, 
                'phone': phone  # Asl kiritilgan raqamni saqlash
            })
        else:
            messages.info(request, f'"{phone}" raqami bilan buyurtma topilmadi.')
    
    return render(request, 'shop/my_orders.html')


def track_order(request):
    """Buyurtmani kuzatish sahifasi"""
    
    # GET parametrlari bilan ishlash
    if request.method == 'GET' and 'order_number' in request.GET:
        order_number = request.GET.get('order_number', '').strip()
        phone = request.GET.get('phone', '').strip()
        
        print(f"DEBUG GET: order_number={order_number}, phone={phone}")
        
        # Telefon raqamini tozalash funksiyasi
        def clean_phone_number(phone_str):
            import re
            cleaned = re.sub(r'\D', '', str(phone_str))
            
            # Oxirgi 9 raqam
            if len(cleaned) >= 9:
                return cleaned[-9:]
            return cleaned
        
        phone_clean = clean_phone_number(phone)
        
        try:
            # Order raqami bo'yicha qidirish
            order = Order.objects.get(order_number=order_number)
            
            # Order telefonini tozalash
            order_phone_clean = clean_phone_number(order.phone)
            
            # Agar tozalangan raqamlar mos kelsa
            if order_phone_clean == phone_clean:
                return render(request, 'shop/track_order.html', {'order': order})
            else:
                messages.error(request, 'Buyurtma topilmadi. Telefon raqami mos kelmadi.')
                
        except Order.DoesNotExist:
            messages.error(request, 'Buyurtma topilmadi. Raqam va telefonni tekshiring.')
        
        return render(request, 'shop/track_order.html')
    
    # POST so'rovi
    elif request.method == 'POST':
        order_number = request.POST.get('order_number', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        print(f"DEBUG POST: Input phone: {phone}")
        
        # Formatlash funksiyasi
        def format_input_phone(phone_str):
            import re
            digits = re.sub(r'\D', '', str(phone_str))
            
            if len(digits) >= 9:
                last_9 = digits[-9:]
                return f"+998 {last_9[0:2]} {last_9[2:5]} {last_9[5:7]} {last_9[7:9]}"
            return phone_str
        
        # Formatlash
        formatted_phone = format_input_phone(phone)
        print(f"DEBUG POST: Formatted phone: {formatted_phone}")
        
        try:
            # Qidirish
            order = Order.objects.get(
                order_number=order_number,
                phone=formatted_phone
            )
            return render(request, 'shop/track_order.html', {'order': order})
            
        except Order.DoesNotExist:
            # Tozalangan raqamlar bilan qidirish
            def clean_phone_number(phone_str):
                import re
                cleaned = re.sub(r'\D', '', str(phone_str))
                return cleaned[-9:] if len(cleaned) >= 9 else cleaned
            
            phone_clean = clean_phone_number(phone)
            
            try:
                order = Order.objects.get(order_number=order_number)
                order_phone_clean = clean_phone_number(order.phone)
                
                if order_phone_clean == phone_clean:
                    return render(request, 'shop/track_order.html', {'order': order})
                else:
                    messages.error(request, 'Buyurtma topilmadi. Raqam va telefonni tekshiring.')
                    
            except Order.DoesNotExist:
                messages.error(request, 'Buyurtma topilmadi. Raqam va telefonni tekshiring.')
    
    return render(request, 'shop/track_order.html')

    """Mening buyurtmalarim sahifasi"""
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        
        # Telefon raqamini tozalash (barcha belgilarni olib tashlash)
        import re
        phone_clean = re.sub(r'\D', '', phone)  # Faqat raqamlar
        
        # Agar +998 yoki 998 boshlansa, 9 raqam qo'shish
        if phone_clean.startswith('998') and len(phone_clean) > 3:
            phone_clean = phone_clean[3:]  # Faqat 9 raqamni olish
        
        print(f"DEBUG: Original phone: {phone}")
        print(f"DEBUG: Cleaned phone: {phone_clean}")
        
        # Database'dan qidirish (bir necha formatda)
        orders = Order.objects.filter(
            phone__contains=phone_clean
        ).order_by('-created_at')
        
        # Agar to'g'ridan-to'g'ri topilmasa, formatlarni sinab ko'rish
        if not orders.exists() and len(phone_clean) >= 9:
            # Boshqa formatlarda qidirish
            phone_formats = []
            
            # Format 1: 901234567
            phone_formats.append(phone_clean)
            
            # Format 2: +998901234567
            phone_formats.append('+998' + phone_clean)
            
            # Format 3: 998901234567
            phone_formats.append('998' + phone_clean)
            
            # Format 4: 90 123 45 67
            if len(phone_clean) == 9:
                formatted = f"{phone_clean[0:2]} {phone_clean[2:5]} {phone_clean[5:7]} {phone_clean[7:9]}"
                phone_formats.append(formatted)
            
            print(f"DEBUG: Searching with formats: {phone_formats}")
            
            # Har bir formatda qidirish
            for phone_format in phone_formats:
                orders = Order.objects.filter(phone__contains=phone_format).order_by('-created_at')
                if orders.exists():
                    print(f"DEBUG: Found with format: {phone_format}")
                    break
        
        if orders.exists():
            return render(request, 'shop/my_orders.html', {
                'orders': orders, 
                'phone': phone_clean if len(phone_clean) >= 9 else phone
            })
        else:
            messages.info(request, f'"{phone}" raqami bilan buyurtma topilmadi.')
    
    return render(request, 'shop/my_orders.html')