from django.shortcuts import render, redirect
from .forms import loginTenantForm
from .models import Tenant, RentPayment
from django.http import HttpResponse
from datetime import datetime
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime
import razorpay


# Create your views here.
def tenantHome(request):
    return render(request, 'tenant/tenantHome.html')

# -------------------- AUTHENTICATION --------------------

def loginTenant(request):
    if request.method == 'POST':
        form = loginTenantForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']

            # Tenant can login even if inactive (he may not be staying anywhere now)
            tenant_exists = Tenant.objects.filter(name=name, phone=phone).exists()

            if tenant_exists:
                request.session['tenant_phone'] = phone
                return redirect('tenantCheckDue')

            return render(request, 'authentication/loginTenant.html', {
                'form': form,
                'error': "You are not registered yet. Please contact your owner."
            })

    else:
        form = loginTenantForm()

    return render(request, 'authentication/loginTenant.html', {
        'form': form
    })


def logoutTenant(request):
    request.session.flush()
    return redirect('loginTenant')


# -------------------- DASHBOARD --------------------

def tenantDashboard(request):
    phone = request.session.get('tenant_phone')
    if not phone:
        return redirect('loginTenant')

    tenant = Tenant.objects.filter(
        phone=phone,
        is_active=True
    ).order_by('-date_added').first()

    if not tenant:
        return render(request, "dashboard/noActiveStay.html")

    return render(request, 'dashboard/tenantDashboard.html', {
        'tenant': tenant
    })


# -------------------- BUILDING --------------------

def tenantBuildingGallery(request):
    phone = request.session.get('tenant_phone')
    if not phone:
        return redirect('loginTenant')

    tenant = Tenant.objects.filter(
        phone=phone,
        is_active=True
    ).order_by('-date_added').first()

    if not tenant:
        return redirect('tenantDashboard')

    building = tenant.flat.building  

    return render(request, "building/tenantBuildingGallery.html", {
        "building": building,
        "images": building.images.all()
    })


# -------------------- FLAT --------------------

def tenantFlatDetails(request, flat_id):
    phone = request.session.get('tenant_phone')
    if not phone:
        return redirect('loginTenant')

    # Get all stay records of this tenant for this flat
    stays = Tenant.objects.filter(
        phone=phone,
        flat_id=flat_id
    ).order_by('-date_added')

    if not stays.exists():
        return HttpResponse("You never stayed in this flat.")

    # Latest stay record for this flat
    stay = stays.first()

    return render(request, 'flat/tenantFlatDetails.html', {
        'stay': stay,          # tenant-flat relationship
        'flat': stay.flat,     # flat details
        'building': stay.flat.building,
        'owner': stay.flat.building.owner,
    })


def allFlats(request):
    phone = request.session.get('tenant_phone')

    if not phone:
        return redirect('loginTenant')

    tenants = Tenant.objects.filter(
        is_active=False,
        phone=phone
    ).select_related('flat', 'flat__building').order_by('-date_added')

    # If tenant has no flats
    if not tenants.exists():
        messages.info(request, "You do not have any previous flats.")
        return render(request, 'flat/allFlats.html', {
            'tenant': [],
        })

    return render(request, 'flat/allFlats.html', {
        'tenant': tenants,
    })


def tenantFlatGallery(request):
    phone = request.session.get('tenant_phone')
    if not phone:
        return redirect('loginTenant')

    tenant = Tenant.objects.filter(
        phone=phone,
        is_active=True
    ).order_by('-date_added').first()

    if not tenant:
        return redirect('tenantDashboard')

    flat = tenant.flat

    return render(request, "flat/tenantFlatGallery.html", {
        "flat": flat,
        "images": flat.images.all()
    })


# -------------------- PAYMENT --------------------

def payRent(request):
    phone = request.session.get('tenant_phone')
    if not phone:
        return redirect('loginTenant')

    tenant = Tenant.objects.filter(
        phone=phone, 
        is_active=True
    ).select_related('flat', 'flat__building', 'flat__building__owner').first()

    if not tenant:
        return redirect('noActiveStay')

    owner = tenant.flat.building.owner

    # Check if owner has Razorpay keys
    if not owner.razorpay_key_id or not owner.razorpay_key_secret:
        return render(request, "payment/payRentError.html", {
            "tenant": tenant,
            "reason": "Your owner has not enabled online payments yet."
        })

    # Prevent paying twice for the same month
    current_month = datetime.now().strftime("%B %Y")
    already_paid = RentPayment.objects.filter(
        tenant=tenant,
        flat=tenant.flat,
        month=current_month,
        status="PAID"
    ).exists()

    return render(request, "payment/payRent.html", {
        "tenant": tenant,
        "already_paid": already_paid,
        "current_month": current_month,
        "owner_key_id": owner.razorpay_key_id,  # used in JS
    })


def paymentSuccess(request):
    payment_id = request.GET.get("payment_id")
    order_id = request.GET.get("order_id")
    signature = request.GET.get("signature")

    if not payment_id or not order_id or not signature:
        return HttpResponse("Invalid payment callback")

    phone = request.session.get("tenant_phone")
    tenant = Tenant.objects.filter(phone=phone, is_active=True).first()

    if not tenant:
        return HttpResponse("Tenant not found")

    owner = tenant.flat.building.owner

    # Razorpay verification
    client = razorpay.Client(auth=(owner.razorpay_key_id, owner.razorpay_key_secret))

    try:
        client.utility.verify_payment_signature({
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
            "razorpay_signature": signature
        })
    except:
        return render(request, "payment/paymentFailed.html")

    current_month = datetime.now().strftime("%B %Y")

    # prevent duplicate entries
    if RentPayment.objects.filter(
        tenant=tenant,
        flat=tenant.flat,
        month=current_month,
        status="PAID"
    ).exists():
        return redirect("rentHistory")

    # store successful payment
    RentPayment.objects.create(
        tenant=tenant,
        flat=tenant.flat,
        payment_id=payment_id,
        amount=tenant.flat_price,
        month=current_month,
        status="PAID"
    )

    return render(request, "payment/paymentSuccess.html", {
        "payment_id": payment_id
    })


def paymentFailed(request):
    return render(request, "payment/paymentFailed.html")


def rentHistory(request):
    phone = request.session.get('tenant_phone')
    tenant = Tenant.objects.filter(phone=phone, is_active=True).first()

    if not tenant:
        return render(request, "dashboard/noActiveStay.html")

    payments = RentPayment.objects.filter(
        tenant=tenant
    ).order_by('-id')

    return render(request, 'payment/rentHistory.html', {
        'tenant': tenant,
        'payments': payments
    })


def tenantFlatTransactions(request, flat_id):
    phone = request.session.get('tenant_phone')
    if not phone:
        return redirect('loginTenant')

    # Get tenant stays for this flat (past or present)
    stays = Tenant.objects.filter(phone=phone, flat_id=flat_id)

    if not stays.exists():
        return HttpResponse("You have no stay records for this flat.")

    # Get all payments tenant made for this flat
    payments = RentPayment.objects.filter(
        tenant__phone=phone,
        flat_id=flat_id
    ).order_by('-id')

    # For page display
    flat = stays.first().flat
    building = flat.building
    owner = building.owner

    return render(request, "payment/flatTransactions.html", {
        "flat": flat,
        "building": building,
        "owner": owner,
        "payments": payments
    })


def tenantCheckDue(request):
    phone = request.session.get('tenant_phone')
    if not phone:
        return redirect('loginTenant')

    # Find active stay
    tenant = Tenant.objects.filter(phone=phone, is_active=True).order_by('-date_added').first()

    if not tenant:
        # No active flat
        return render(request, "dashboard/noActiveStay.html")

    current_month = datetime.now().strftime("%B %Y")

    already_paid = RentPayment.objects.filter(
        tenant=tenant,
        month=current_month,
        status="PAID"
    ).exists()

    if already_paid:
        return redirect('tenantDashboard')

    # Rent is due
    return render(request, "payment/rentDuePrompt.html", {
        "tenant": tenant,
        "current_month": current_month
    })


def createOrder(request):
    phone = request.session.get("tenant_phone")
    if not phone:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    tenant = Tenant.objects.filter(
        phone=phone, 
        is_active=True
    ).select_related('flat', 'flat__building', 'flat__building__owner').first()

    if not tenant:
        return JsonResponse({"error": "No active tenant found"}, status=400)

    owner = tenant.flat.building.owner

    client = razorpay.Client(
        auth=(owner.razorpay_key_id, owner.razorpay_key_secret)
    )

    amount = tenant.flat_price * 100

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return JsonResponse({
        "order_id": order["id"],
        "amount": amount,
        "key_id": owner.razorpay_key_id
    })
