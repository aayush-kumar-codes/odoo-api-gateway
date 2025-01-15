from fastapi import APIRouter
from app.api.v1.endpoints import auth, product, category, variant, attribute, basket, order, notification, user, vendor

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(product.router, prefix="/catalog/products", tags=["products"])
api_router.include_router(category.router, prefix="/catalog/categories", tags=["categories"])
api_router.include_router(variant.router, prefix="/catalog/variants", tags=["variants"])
api_router.include_router(attribute.router, prefix="/catalog/attributes", tags=["attributes"]) 
api_router.include_router(basket.router, prefix="/baskets", tags=["basket"])
api_router.include_router(order.router, prefix="/orders", tags=["orders"])
api_router.include_router(notification.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(vendor.router, prefix="/vendors", tags=["vendors"])