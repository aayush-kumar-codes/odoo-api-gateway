from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.order import Order, OrderCreate, OrderLine, OrderStatus
from app.models.order import Order as OrderModel, OrderLine as OrderLineModel
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, clear_cache_pattern
from datetime import datetime
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

# Standard error messages
ORDER_NOT_FOUND = "Order not found"
UNAUTHORIZED = "Not enough permissions"

@router.get("/", response_model=List[Order])
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Retrieve orders for the current user"""
    try:
        current_user = await deps.get_current_user(credentials, db)
        user_id = current_user.get('id')
        
        cache_key = f"order:list:{user_id}:{skip}:{limit}"
        cached_data = get_cache(cache_key)
        if cached_data:
            return cached_data
            
        orders = db.query(OrderModel)\
            .filter(OrderModel.user_id == user_id)\
            .order_by(OrderModel.order_date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
            
        # Fix any orders with missing names
        for order in orders:
            if not order.name:
                order_date = order.order_date or datetime.utcnow()
                order.name = f"ORD/{order_date.strftime('%Y%m')}/{order.id:03d}"
        
        if orders:
            db.commit()
            set_cache(cache_key, orders, expire=1800)
            
        return orders
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving orders: {str(e)}"
        )

@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Get details of a specific order"""
    current_user = await deps.get_current_user(credentials, db)
    
    order = db.query(OrderModel).filter(
        OrderModel.id == order_id,
        OrderModel.user_id == current_user.get('id')
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/", response_model=Order)
async def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Create a new order"""
    current_user = await deps.get_current_user(credentials, db)
    
    db_order = OrderModel(
        user_id=current_user.get('id'),
        shipping_address=order.shipping_address,
        payment_method=order.payment_method,
        state=OrderStatus.DRAFT
    )
    
    total_price = 0
    for line in order.lines:
        order_line = OrderLineModel(
            product_id=line.product_id,
            product_uom_qty=line.product_uom_qty,
            price_unit=line.price_unit,
            subtotal=line.price_unit * line.product_uom_qty
        )
        total_price += order_line.subtotal
        db_order.lines.append(order_line)
    
    db_order.total_price = total_price
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.put("/{order_id}", response_model=Order)
async def update_order(
    order_id: int,
    order: OrderCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Update an order"""
    current_user = await deps.get_current_user(credentials, db)
    
    db_order = db.query(OrderModel).filter(
        OrderModel.id == order_id,
        OrderModel.user_id == current_user.get('id'),
        OrderModel.state == OrderStatus.DRAFT
    ).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found or cannot be modified")
    
    # Update order details
    db_order.shipping_address = order.shipping_address
    db_order.payment_method = order.payment_method
    
    # Clear existing lines and add new ones
    db.query(OrderLineModel).filter(OrderLineModel.order_id == order_id).delete()
    
    total_price = 0
    for line in order.lines:
        order_line = OrderLineModel(
            order_id=order_id,
            product_id=line.product_id,
            product_uom_qty=line.product_uom_qty,
            price_unit=line.price_unit,
            subtotal=line.price_unit * line.product_uom_qty
        )
        total_price += order_line.subtotal
        db.add(order_line)
    
    db_order.total_price = total_price
    db.commit()
    db.refresh(db_order)
    return db_order

@router.delete("/{order_id}")
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Cancel an order"""
    current_user = await deps.get_current_user(credentials, db)
    
    order = db.query(OrderModel).filter(
        OrderModel.id == order_id,
        OrderModel.user_id == current_user.get('id'),
        OrderModel.state.in_([OrderStatus.DRAFT, OrderStatus.PENDING])
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or cannot be cancelled")
    
    order.state = OrderStatus.CANCELLED
    db.commit()
    return {"message": "Order cancelled successfully"}

@router.get("/{order_id}/status")
async def get_order_status(
    order_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Get the status of an order"""
    current_user = await deps.get_current_user(credentials, db)
    
    order = db.query(OrderModel).filter(
        OrderModel.id == order_id,
        OrderModel.user_id == current_user.get('id')
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"status": order.state}

@router.post("/{order_id}/confirm")
async def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Confirm the order for payment processing"""
    current_user = await deps.get_current_user(credentials, db)
    
    order = db.query(OrderModel).filter(
        OrderModel.id == order_id,
        OrderModel.user_id == current_user.get('id'),
        OrderModel.state == OrderStatus.DRAFT
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or cannot be confirmed")
    
    order.state = OrderStatus.PENDING
    db.commit()
    return {"message": "Order confirmed and ready for payment processing"} 