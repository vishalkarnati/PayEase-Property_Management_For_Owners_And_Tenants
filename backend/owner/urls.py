from django.urls import path
from . import views

urlpatterns = [
    path('', views.ownerHome, name='ownerHome'),

    # Authentication
    path('signUpOwner/', views.signUpOwner , name='signUpOwner'),

    path('loginOwner/', views.loginOwner , name='loginOwner'),

    path('logout/', views.logoutOwner, name='logoutOwner'),


    # Dashboard
    path('dashboard/', views.ownerDashboard, name='ownerDashboard'),


    # Building
    path('buildings/<int:building_id>/', views.buildingDetails, name='buildingDetails'),

    path('building/add/', views.addBuilding, name='addBuilding'),

    path("building/<int:building_id>/delete/", views.deleteBuilding, name="deleteBuilding"),

    path('buildings/<int:building_id>/edit/', views.editBuilding, name='editBuilding'),

    path('buildings/<int:building_id>/add-image/', views.addBuildingImage, name='addBuildingImage'),

    path('buildings/image/<int:image_id>/delete/', views.deleteBuildingImage, name='deleteBuildingImage'),
    
    path("buildings/<int:building_id>/gallery/", views.buildingGallery, name="buildingGallery"),

    path("clear-upload-error/", views.clearUploadError, name="clearUploadError"),


    # Flat
    path('buildings/<int:building_id>/flat/<int:flat_id>/', views.flatDetails, name='flatDetails'),
    
    path('buildings/<int:building_id>/addFlat/', views.addFlat, name='addFlat'),

    path('buildings/<int:building_id>/flat/<int:flat_id>/edit/', views.editFlat, name='editFlat'),
    
    path("buildings/<int:building_id>/flat/<int:flat_id>/delete/", views.deleteFlat, name="deleteFlat"),

    path('buildings/<int:building_id>/flat/<int:flat_id>/gallery/', views.flatGallery, name='flatGallery'),

    path('flat/image/<int:image_id>/delete/', views.deleteFlatImage, name='deleteFlatImage'),


    # Tenant
    path('buildings/<int:building_id>/flat/<int:flat_id>/addTenant/', views.addTenant, name='addTenant'),

    path('buildings/<int:building_id>/flat/<int:flat_id>/remove/', views.removeTenant, name='removeTenant'),

    path('buildings/<int:building_id>/flat/<int:flat_id>/tenant/<int:tenant_id>/', views.tenantDetails, name='tenantDetails'),
    
    path('buildings/<int:building_id>/flat/<int:flat_id>/pastTenants/', views.pastTenants, name='pastTenants'),

    path('tenant/<int:tenant_id>/details/', views.tenantFullDetails, name='tenantFullDetails'),


    # Payments
    path('buildings/<int:building_id>/payments/', views.ownerBuildingPayments, name='ownerBuildingPayments'),

    path('buildings/<int:building_id>/flat/<int:flat_id>/payments/', views.ownerFlatPayments, name='ownerFlatPayments'),

    path('buildings/<int:building_id>/flat/<int:flat_id>/tenant/payment-history/', views.tenantPaymentHistory, name='tenantPaymentHistory'),

    path('tenant/<int:tenant_id>/transactions/', views.tenantAllTransactions, name='tenantAllTransactions'),

]

