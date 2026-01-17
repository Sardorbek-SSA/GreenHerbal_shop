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
                'name': herbal.name,
                'price': float(herbal.price),
                'qty': quantity,
                'image': herbal.image.url if herbal.image else '',
                'total': float(herbal.price) * quantity
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        
        request.session['cart_message'] = f'{herbal.name} added to cart!'
        
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
    
    shipping = 0 if subtotal >= 50 else 5
    
    tax = subtotal * 0.08
    
    total = subtotal + shipping + tax
    
    context = {
        'cart': cart,
        'subtotal': round(subtotal, 2),
        'shipping': shipping,
        'tax': round(tax, 2),
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
        request.session['cart_message'] = f'{product_name} removed from cart!'
    
    return redirect('shop:cart_view')

def clear_cart(request):
    request.session['cart'] = {}
    request.session.modified = True
    request.session['cart_message'] = 'Cart cleared!'
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

# ===================== CHECKOUT FUNKSIYASI =====================
def checkout(request):
    if request.method == 'GET':
        # GET so'rovi: checkout sahifasini ko'rsatish
        cart = request.session.get('cart', {})
        
        if not cart:
            messages.warning(request, 'Savat boʻsh!')
            return redirect('shop:cart_view')
        
        subtotal = sum(item['total'] for item in cart.values())
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
        # POST so'rovi: to'lov usulini qayta ishlash
        payment_method = request.POST.get('payment_method', 'cash_pickup')
        
        # Order ID generatsiya qilish
        order_id = 'ORD' + str(random.randint(10000, 99999))
        
        # Ma'lumotlarni session ga saqlash
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
        
        # To'lov usuliga qarab yo'naltirish
        if payment_method == 'cash_pickup':
            # Naqd to'lov - tasdiqlash sahifasiga
            return redirect('shop:order_confirmation')
        else:
            # Onlayn to'lov - payment sahifasiga
            return redirect('shop:online_payment', payment_method=payment_method)

# ===================== ORDER CONFIRMATION FUNKSIYASI =====================
def order_confirmation(request):
    """Buyurtma tasdiqlash sahifasi"""
    order_data = request.session.get('order_data', {})
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, 'Savat boʻsh!')
        return redirect('shop:cart_view')
    
    # DEBUG: Nima saqlanayotganini ko'rish
    print(f"✅ DEBUG: order_data = {order_data}")
    print(f"✅ DEBUG: cart = {cart}")
    
    try:
        # ✅ 1. Buyurtma raqamini generatsiya qilish
        order_number = generate_order_number()
        
        # ✅ 2. PickupPoint ni olish (agar mavjud bo'lsa)
        pickup_point = None
        pickup_point_id = order_data.get('pickup_point_id')
        if pickup_point_id:
            try:
                pickup_point = PickupPoint.objects.get(id=pickup_point_id)
            except PickupPoint.DoesNotExist:
                pickup_point = None
        
        # ✅ 3. Buyurtmani DATABASE ga saqlash
        order = Order.objects.create(
            order_number=order_number,
            full_name=order_data.get('full_name', 'Mijoz'),
            phone=order_data.get('phone', ''),
            email=order_data.get('email', ''),
            pickup_point=pickup_point,
            payment_method=order_data.get('payment_method', 'cash_pickup'),
            notes=order_data.get('notes', ''),
            subtotal=sum(item['total'] for item in cart.values()),
            # shipping=0,
            total=sum(item['total'] for item in cart.values()),
            payment_status=(order_data.get('payment_method') != 'cash_pickup'),  # Onlayn to'lov = True
            status='confirmed' if order_data.get('payment_method') != 'cash_pickup' else 'pending',
        )
        
        print(f"✅ Buyurtma yaratildi: {order.id} - {order.order_number}")
        
        # ✅ 4. Buyurtma mahsulotlarini saqlash
        for product_id, item in cart.items():
            OrderItem.objects.create(
                order=order,
                product_name=item['name'],
                product_price=item['price'],
                quantity=item['qty'],
                total_price=item['total'],
            )
            print(f"✅ Mahsulot saqlandi: {item['name']} x {item['qty']}")
        
        # ✅ 5. Savatni tozalash
        request.session['cart'] = {}
        request.session['last_order_id'] = order.id
        request.session['last_order_number'] = order.order_number
        request.session.modified = True
        
        print(f"✅ Session tozalandi, last_order_id: {order.id}")
        
        # ✅ 6. Kontekst
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
        
        # Agar saqlanmasa, oddiy ma'lumotlarni ko'rsatish
        order_number = request.session.get('order_id', 'ORD' + str(random.randint(10000, 99999)))
        
        context = {
            'order_number': order_number,
            'payment_method': order_data.get('payment_method', 'cash_pickup'),
            'full_name': order_data.get('full_name', ''),
            'phone': order_data.get('phone', ''),
            'total': sum(item['total'] for item in cart.values()),
            'message': 'Buyurtma ma\'lumotlari saqlanmadi. Iltimos, administrator bilan bog\'laning.',
        }
        
        # Savatni saqlab qolish
        request.session['cart'] = {}
        request.session.modified = True
    
    return render(request, 'shop/order_confirmation.html', context)

def track_order(request):
    """Buyurtmani kuzatish sahifasi"""
    if request.method == 'POST':
        order_number = request.POST.get('order_number')
        phone = request.POST.get('phone')
        
        try:
            order = Order.objects.get(order_number=order_number, phone=phone)
            return render(request, 'shop/track_order.html', {'order': order})
        except Order.DoesNotExist:
            messages.error(request, 'Buyurtma topilmadi. Raqam va telefonni tekshiring.')
    
    return render(request, 'shop/track_order.html')

def my_orders(request):
    """Mening buyurtmalarim sahifasi"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        orders = Order.objects.filter(phone=phone).order_by('-created_at')
        
        if orders.exists():
            return render(request, 'shop/my_orders.html', {'orders': orders, 'phone': phone})
        else:
            messages.info(request, 'Bu telefon raqami bilan buyurtma topilmadi.')
    
    return render(request, 'shop/my_orders.html')