from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Owner, Building, Flat, BuildingImage, FlatImage
from .forms import SignUpOwnerForm, LoginOwnerForm, BuildingForm, FlatForm, addTenantForm
from . import forms
from datetime import datetime
from django.http import JsonResponse

from tenant.models import Tenant, RentPayment

def ownerHome(request):
    return render(request, 'owner/ownerHome.html')


# -------------------- AUTHENTICATION --------------------

def signUpOwner(request):
    if request.method == 'POST':
        form = SignUpOwnerForm(request.POST)

        if form.is_valid():
            phone = form.cleaned_data['phone']

            if Owner.objects.filter(phone=phone).exists():
                return render(request, 'owner/signUpOwner.html', {
                    'form': form,
                    'error': "Number already registered."
                })

            form.save()
            return redirect('loginOwner')

    else:
        form = SignUpOwnerForm()

    return render(request, 'owner/signUpOwner.html', {'form': form})


def loginOwner(request):
    if request.method == 'POST':
        form = LoginOwnerForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']

            owner = Owner.objects.filter(name=name, phone=phone).first()

            if owner:
                request.session['owner_phone'] = phone
                return redirect('ownerDashboard')

            return render(request, 'owner/loginOwner.html', {
                'form': form,
                'error': "You are not registered."
            })

    else:
        form = LoginOwnerForm()

    return render(request, 'owner/loginOwner.html', {'form': form})


def logoutOwner(request):
    request.session.flush()
    return redirect('loginOwner')


# -------------------- DASHBOARD --------------------

def ownerDashboard(request):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    owner = Owner.objects.filter(phone=phone).first()
    if not owner:
        return HttpResponse("Owner not found")

    buildings = Building.objects.filter(owner=owner)
    flats = Flat.objects.filter(building__owner=owner)

    # Count only ACTIVE tenants
    occupied = Tenant.objects.filter(
        flat__building__owner=owner, 
        is_active=True
    ).values('flat').distinct().count()

    # Current month
    current_month = datetime.now().strftime("%B %Y")

    # Get all ACTIVE tenants only
    active_tenants = Tenant.objects.filter(
        flat__building__owner=owner,
        is_active=True
    ).order_by('flat_id', '-date_added')

    # Only 1 active tenant per flat → safe
    latest_active_tenants = {}
    for t in active_tenants:
        if t.flat_id not in latest_active_tenants:
            latest_active_tenants[t.flat_id] = t

    # Find unpaid tenants from ACTIVE ones
    unpaid_tenants = []
    for tenant in latest_active_tenants.values():
        paid = RentPayment.objects.filter(
            tenant=tenant,
            month=current_month,
            status="PAID"
        ).exists()

        if not paid:
            unpaid_tenants.append(tenant)

    return render(request, "owner/ownerDashboard.html", {
        "owner": owner,
        "buildings": buildings,
        "total_buildings": buildings.count(),
        "total_flats": flats.count(),

        # Only count active tenants
        "occupied_flats": occupied,
        "vacant_flats": flats.count() - occupied,

        # Show unpaid tenants for this month
        "unpaid_tenants": unpaid_tenants,
        "current_month": current_month,
    })


# -------------------- BUILDING --------------------

def buildingDetails(request, building_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    # Get building owned by this owner
    building = get_object_or_404(Building, id=building_id, owner__phone=phone)

    flats = building.flats.all()
    current_month = datetime.now().strftime("%B %Y")

    unpaid_tenants = []

    for flat in flats:
        # Only ACTIVE tenant for this flat
        latest_tenant = flat.tenants.filter(is_active=True).order_by('-date_added').first()

        if latest_tenant:
            paid = RentPayment.objects.filter(
                tenant=latest_tenant,
                flat=flat,
                month=current_month,
                status="PAID"
            ).exists()

            if not paid:
                unpaid_tenants.append(latest_tenant)

    return render(request, 'building/buildingDetails.html', {
        'building': building,
        'flats': flats,
        'unpaid_tenants': unpaid_tenants,
        'current_month': current_month,
    })


def addBuilding(request):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    owner = get_object_or_404(Owner, phone=phone)

    if request.method == "POST":
        form = BuildingForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            address = form.cleaned_data['address']

            # Check for duplicate building for same owner
            if Building.objects.filter(owner=owner, name=name, address=address).exists():
                return render(request, 'building/addBuilding.html', {
                    'form': form,
                    'error': "Building already exists. Try adding flats in it or create a new building."
                })

            # Otherwise save building
            building = form.save(commit=False)
            building.owner = owner
            building.save()

            return redirect('ownerDashboard')

    else:
        form = BuildingForm()

    return render(request, 'building/addBuilding.html', {
        'form': form
    })


def deleteBuilding(request, building_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return JsonResponse({"success": False, "message": "You are not logged in."})

    building = get_object_or_404(
        Building,
        id=building_id,
        owner__phone=phone
    )

    # Cannot delete if building has flats
    if building.flats.exists():
        return JsonResponse({
            "success": False,
            "message": "This building cannot be deleted because it contains flats. Please delete all flats before removing the building."
        })

    building.delete()

    return JsonResponse({
        "success": True,
        "message": "Building deleted successfully."
    })






def editBuilding(request, building_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    building = get_object_or_404(Building, id=building_id, owner__phone=phone)

    if request.method == "POST":
        form = BuildingForm(request.POST, instance=building)

        if form.is_valid():
            new_address = form.cleaned_data['address']

            # Check if this address already exists for another building of the same owner
            duplicate = Building.objects.filter(
                owner__phone=phone,
                address__iexact=new_address
            ).exclude(id=building_id).exists()

            if duplicate:
                # Address already exists → do not save
                return render(request, "building/editBuilding.html", {
                    "form": form,
                    "building": building,
                    "error": "This address already exists for another building. Cannot update."
                })

            # Safe to save
            form.save()
            return redirect('buildingDetails', building_id=building_id)

    else:
        form = BuildingForm(instance=building)

    return render(request, "building/editBuilding.html", {
        "form": form,
        "building": building
    })


def addBuildingImage(request, building_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    building = get_object_or_404(Building, id=building_id, owner__phone=phone)

    # Maximum allowed images
    max_images = 5
    current_count = building.images.count()

    if request.method == "POST":
        new_images = request.FILES.getlist('images')

        # If adding these images exceeds limit → DO NOT load new page
        if current_count + len(new_images) > max_images:
            # Store error message in session
            request.session["upload_error"] = (
                f"You can upload only 5 images."
            )

            return redirect('editBuilding', building_id=building.id)

        # Otherwise upload the images
        for img in new_images:
            BuildingImage.objects.create(building=building, image=img)

        return redirect('editBuilding', building_id=building.id)


def deleteBuildingImage(request, image_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    img = get_object_or_404(BuildingImage, id=image_id, building__owner__phone=phone)
    building_id = img.building.id
    
    img.image.delete()  # Deletes file from media folder
    img.delete()

    return redirect('buildingGallery', building_id=building_id)


def buildingGallery(request, building_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    building = get_object_or_404(Building, id=building_id, owner__phone=phone)

    # Max images allowed
    max_images = 5

    if request.method == "POST":
        new_images = request.FILES.getlist('images')

        # Prevent exceeding limit
        if building.images.count() + len(new_images) > max_images:
            remaining = max_images - building.images.count()
            request.session["upload_error"] = f"You can upload only {remaining} more image(s). Maximum allowed is 5."
            return redirect("buildingGallery", building_id=building_id)

        # Upload images
        for img in new_images:
            BuildingImage.objects.create(building=building, image=img)

        return redirect("buildingGallery", building_id=building_id)

    return render(request, "building/gallery.html", {
        "building": building,
        "max_images": max_images
    })


def clearUploadError(request):
    if "upload_error" in request.session:
        del request.session["upload_error"]
    return HttpResponse("")  # return empty response



# -------------------- FLAT --------------------

def flatDetails(request, building_id, flat_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    flat = get_object_or_404(
        Flat, 
        id=flat_id,
        building_id=building_id,
        building__owner__phone=phone
    )

    tenant = flat.tenants.filter(is_active=True).order_by('-date_added').first()

    return render(request, 'flat/flatDetails.html', {
        'flat': flat,
        'tenant': tenant,
        'building': flat.building,
    })


def addFlat(request, building_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    building = get_object_or_404(Building, id=building_id, owner__phone=phone)

    if request.method == "POST":
        form = FlatForm(request.POST)
        if form.is_valid():
            flat_number = form.cleaned_data['flat_number']

            # Duplicate check for FLATS inside the SAME BUILDING
            if Flat.objects.filter(building=building, flat_number=flat_number).exists():
                return render(request, 'flat/addFlat.html', {
                    'form': form,
                    'building': building,
                    'error': "This flat number already exists in this building. Try to add a different flat number."
                })

            flat = form.save(commit=False)
            flat.building = building
            flat.save()

            return redirect('buildingDetails', building_id=building_id)

    else:
        form = FlatForm()

    return render(request, 'flat/addFlat.html', {
        'form': form,
        'building': building,
    })


def editFlat(request, building_id, flat_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    flat = get_object_or_404(
        Flat,
        id=flat_id,
        building_id=building_id,
        building__owner__phone=phone
    )

    if request.method == "POST":
        form = FlatForm(request.POST, instance=flat)
        if form.is_valid():
            form.save()
            return redirect('flatDetails', building_id=building_id, flat_id=flat_id)

    else:
        form = FlatForm(instance=flat)

    return render(request, "flat/editFlat.html", {
        "flat": flat,
        "form": form,
        "building": flat.building,
    })


def deleteFlat(request, building_id, flat_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return JsonResponse({"success": False, "message": "You are not logged in."})

    building = get_object_or_404(Building, id=building_id, owner__phone=phone)
    flat = get_object_or_404(Flat, id=flat_id, building=building)

    # Check if active tenant stays
    if flat.tenants.filter(is_active=True).exists():
        return JsonResponse({
            "success": False,
            "message": "This flat cannot be deleted because a tenant is currently occupying it. Please remove the tenant before attempting to delete the flat."
        })

    flat.delete()

    return JsonResponse({
        "success": True,
        "message": "Flat deleted successfully."
    })


def flatGallery(request, building_id, flat_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    flat = get_object_or_404(
        Flat,
        id=flat_id,
        building_id=building_id,
        building__owner__phone=phone
    )

    max_images = 5

    if request.method == "POST":
        images = request.FILES.getlist("images")

        # Prevent exceeding limit
        if flat.images.count() + len(images) > max_images:
            remaining = max_images - flat.images.count()
            request.session["upload_error"] = f"You can upload only {remaining} more image(s). Maximum allowed is 5."
            return redirect("flatGallery", building_id=building_id, flat_id=flat_id)

        for img in images:
            FlatImage.objects.create(flat=flat, image=img)

        return redirect("flatGallery", building_id=building_id, flat_id=flat_id)

    return render(request, "flat/flatGallery.html", {
        "flat": flat,
        "building": flat.building,
    })


def deleteFlatImage(request, image_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    img = get_object_or_404(FlatImage, id=image_id, flat__building__owner__phone=phone)
    flat = img.flat
    building_id = flat.building.id

    img.image.delete()
    img.delete()

    return redirect("flatGallery", building_id=building_id, flat_id=flat.id)


# -------------------- TENANT --------------------

def addTenant(request, building_id, flat_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    flat = get_object_or_404(
        Flat,
        id=flat_id,
        building_id=building_id,
        building__owner__phone=phone
    )

    if request.method == "POST":
        form = addTenantForm(request.POST)

        if form.is_valid():
            # 1. Deactivate existing active tenant (if any)
            Tenant.objects.filter(flat=flat, is_active=True).update(is_active=False)

            # 2. Create new tenant as active
            tenant = form.save(commit=False)
            tenant.flat = flat
            tenant.is_active = True
            tenant.save()

            return redirect('flatDetails', building_id=building_id, flat_id=flat_id)

    else:
        form = addTenantForm()

    return render(request, 'tenant/addTenant.html', {
        'form': form,
        'flat': flat,
        'building': flat.building,
    })


def removeTenant(request, building_id, flat_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    flat = get_object_or_404(
        Flat,
        id=flat_id,
        building_id=building_id,
        building__owner__phone=phone
    )

    # Deactivate active tenant
    Tenant.objects.filter(flat=flat, is_active=True).update(is_active=False)

    return redirect('flatDetails', building_id=building_id, flat_id=flat_id)


def tenantDetails(request, building_id, flat_id, tenant_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    tenant = get_object_or_404(
        Tenant, id=tenant_id, flat_id=flat_id,
        flat__building_id=building_id,
        flat__building__owner__phone=phone
    )

    return render(request, 'tenant/tenantDetails.html', {
        'tenant': tenant,
        'flat': tenant.flat,
        'building': tenant.flat.building,
    })


def pastTenants(request, building_id, flat_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    flat = get_object_or_404(
        Flat, id=flat_id,
        building_id=building_id,
        building__owner__phone=phone
    )

    past = Tenant.objects.filter(is_active=False, flat_id=flat_id).order_by('-date_added')

    return render(request, 'tenant/pastTenants.html', {
        'flat': flat,
        'tenants': past,
        'building': flat.building,
    })


def tenantFullDetails(request, tenant_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    # Fetch tenant, but ensure the owner truly owns the building this tenant stayed in
    tenant = get_object_or_404(
        Tenant,
        id=tenant_id,
        flat__building__owner__phone=phone
    )

    payments = RentPayment.objects.filter(
        tenant=tenant
    ).order_by('-id')

    flat = tenant.flat
    building = flat.building
    owner = building.owner

    return render(request, 'tenant/tenantFullDetails.html', {
        'tenant': tenant,
        'payments': payments,
        'flat': flat,
        'building': building,
        'owner': owner
    })


def tenantPaymentHistory(request, building_id, flat_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    # Validate flat belongs to this owner
    flat = get_object_or_404(
        Flat,
        id=flat_id,
        building_id=building_id,
        building__owner__phone=phone
    )

    # Latest active tenant
    tenant = flat.tenants.order_by('-date_added').first()

    if not tenant:
        payments = []
    else:
        payments = RentPayment.objects.filter(
            tenant=tenant,
            flat=flat
        ).order_by('-id')  # newest record always at top


    return render(request, 'tenant/tenantPaymentHistory.html', {
        'flat': flat,
        'tenant': tenant,
        'payments': payments,
    })


def tenantAllTransactions(request, tenant_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    # Ensure owner can only see their own tenant
    tenant = get_object_or_404(
        Tenant,
        id=tenant_id,
        flat__building__owner__phone=phone
    )

    payments = RentPayment.objects.filter(
        tenant=tenant
    ).order_by('-id')

    flat = tenant.flat
    building = flat.building
    owner = building.owner

    return render(request, 'tenant/tenantAllTransactions.html', {
        'tenant': tenant,
        'payments': payments,
        'flat': flat,
        'building': building,
        'owner': owner
    })


def ownerBuildingPayments(request, building_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    building = get_object_or_404(
        Building, id=building_id, owner__phone=phone
    )

    payments = RentPayment.objects.filter(
        flat__building=building
    ).select_related('tenant', 'flat').order_by('-id')

    return render(request, "payment/ownerBuildingPayments.html", {
        "building": building,
        "payments": payments
    })


def ownerFlatPayments(request, building_id, flat_id):
    phone = request.session.get('owner_phone')
    if not phone:
        return redirect('loginOwner')

    flat = get_object_or_404(
        Flat,
        id=flat_id,
        building_id=building_id,
        building__owner__phone=phone
    )

    payments = RentPayment.objects.filter(
        flat=flat
    ).select_related('tenant').order_by('-id')

    return render(request, "payment/ownerFlatPayments.html", {
        "flat": flat,
        "building": flat.building,
        "payments": payments
    })
