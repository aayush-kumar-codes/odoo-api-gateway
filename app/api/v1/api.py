from fastapi import APIRouter, Depends
from app.api.v1.endpoints import auth, product, category, variant, attribute, basket, order, notification, user, vendor
from app.api import deps

api_router = APIRouter()

# Public routes (no auth required)
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Protected routes (require authentication)
api_router.include_router(
    product.router,
    prefix="/catalog/products",
    tags=["products"],
    dependencies=[Depends(deps.get_current_user)]
)

api_router.include_router(
    category.router,
    prefix="/catalog/categories",
    tags=["categories"],
    dependencies=[Depends(deps.get_current_user)]
)

api_router.include_router(
    variant.router,
    prefix="/catalog/variants",
    tags=["variants"],
    dependencies=[Depends(deps.get_current_user)]
)

api_router.include_router(
    attribute.router,
    prefix="/catalog/attributes",
    tags=["attributes"],
    dependencies=[Depends(deps.get_current_user)]
)

api_router.include_router(
    basket.router,
    prefix="/baskets",
    tags=["basket"],
    dependencies=[Depends(deps.get_current_user)]
)

api_router.include_router(
    order.router,
    prefix="/orders",
    tags=["orders"],
    dependencies=[Depends(deps.get_current_user)]
)

# Admin routes (require superuser)
api_router.include_router(
    notification.router,
    prefix="/notifications",
    tags=["notifications"],
    dependencies=[Depends(deps.get_current_superuser)]
)

api_router.include_router(
    user.router,
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(deps.get_current_superuser)]
)

api_router.include_router(
    vendor.router,
    prefix="/vendors",
    tags=["vendors"],
    dependencies=[Depends(deps.get_current_superuser)]
)