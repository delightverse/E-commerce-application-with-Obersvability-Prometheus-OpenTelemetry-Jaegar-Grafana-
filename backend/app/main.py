"""
E-Commerce Backend with OpenTelemetry Instrumentation
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import time
import random

from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from app.database import engine, SessionLocal, Base
from app import models, schemas, crud

app = FastAPI(
    title="E-Commerce API",
    description="Fully instrumented e-commerce backend with observability features",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Prometheus metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
active_users = Gauge('active_users_total', 'Active users')
orders_total = Counter('orders_total', 'Total orders', ['status'])
revenue_total = Counter('revenue_total_usd', 'Total revenue in USD')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ecommerce-backend"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Products
@app.post("/products/", response_model=schemas.Product, status_code=201)
async def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    start_time = time.time()
    try:
        db_product = crud.create_product(db, product)
        http_requests_total.labels(method='POST', endpoint='/products/', status='201').inc()
        duration = time.time() - start_time
        http_request_duration_seconds.labels(method='POST', endpoint='/products/').observe(duration)
        return db_product
    except Exception as e:
        http_requests_total.labels(method='POST', endpoint='/products/', status='500').inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/", response_model=List[schemas.Product])
async def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    start_time = time.time()
    products = crud.get_products(db, skip=skip, limit=limit)
    http_requests_total.labels(method='GET', endpoint='/products/', status='200').inc()
    duration = time.time() - start_time
    http_request_duration_seconds.labels(method='GET', endpoint='/products/').observe(duration)
    return products

@app.get("/products/{product_id}", response_model=schemas.Product)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    start_time = time.time()
    product = crud.get_product(db, product_id)
    if product is None:
        http_requests_total.labels(method='GET', endpoint='/products/{id}', status='404').inc()
        raise HTTPException(status_code=404, detail="Product not found")
    http_requests_total.labels(method='GET', endpoint='/products/{id}', status='200').inc()
    duration = time.time() - start_time
    http_request_duration_seconds.labels(method='GET', endpoint='/products/{id}').observe(duration)
    return product

# Orders
@app.post("/orders/", response_model=schemas.Order, status_code=201)
async def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    start_time = time.time()
    
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("order.user_id", order.user_id)
        span.set_attribute("order.item_count", len(order.items))
        
        try:
            with tracer.start_as_current_span("validate_products"):
                total_amount = 0
                for item in order.items:
                    product = crud.get_product(db, item.product_id)
                    if not product:
                        span.add_event("product_not_found", {"product_id": item.product_id})
                        raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
                    
                    if product.stock < item.quantity:
                        span.add_event("insufficient_stock", {"product_id": item.product_id, "requested": item.quantity, "available": product.stock})
                        raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")
                    
                    total_amount += product.price * item.quantity
                
                span.set_attribute("order.total_amount", total_amount)
            
            with tracer.start_as_current_span("process_payment") as payment_span:
                payment_span.set_attribute("payment.amount", total_amount)
                payment_span.set_attribute("payment.method", "credit_card")
                
                payment_delay = random.uniform(0.05, 0.2)
                time.sleep(payment_delay)
                
                if random.random() < 0.05:
                    payment_span.set_attribute("payment.status", "failed")
                    payment_span.add_event("payment_failed", {"reason": "card_declined"})
                    orders_total.labels(status='failed').inc()
                    raise HTTPException(status_code=402, detail="Payment failed")
                
                payment_span.set_attribute("payment.status", "success")
                payment_span.add_event("payment_successful")
            
            with tracer.start_as_current_span("save_order"):
                db_order = crud.create_order(db, order, total_amount)
                span.set_attribute("order.id", db_order.id)
            
            with tracer.start_as_current_span("update_inventory"):
                for item in order.items:
                    crud.update_product_stock(db, item.product_id, -item.quantity)
            
            orders_total.labels(status='success').inc()
            revenue_total.inc(total_amount)
            active_users.inc()
            
            http_requests_total.labels(method='POST', endpoint='/orders/', status='201').inc()
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method='POST', endpoint='/orders/').observe(duration)
            
            span.add_event("order_created", {"order_id": db_order.id, "total_amount": total_amount, "duration_seconds": duration})
            
            return db_order
            
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("error", True)
            orders_total.labels(status='error').inc()
            http_requests_total.labels(method='POST', endpoint='/orders/', status='500').inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/", response_model=List[schemas.Order])
async def list_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    start_time = time.time()
    orders = crud.get_orders(db, skip=skip, limit=limit)
    http_requests_total.labels(method='GET', endpoint='/orders/', status='200').inc()
    duration = time.time() - start_time
    http_request_duration_seconds.labels(method='GET', endpoint='/orders/').observe(duration)
    return orders

@app.get("/orders/{order_id}", response_model=schemas.Order)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    start_time = time.time()
    order = crud.get_order(db, order_id)
    if order is None:
        http_requests_total.labels(method='GET', endpoint='/orders/{id}', status='404').inc()
        raise HTTPException(status_code=404, detail="Order not found")
    http_requests_total.labels(method='GET', endpoint='/orders/{id}', status='200').inc()
    duration = time.time() - start_time
    http_request_duration_seconds.labels(method='GET', endpoint='/orders/{id}').observe(duration)
    return order

FastAPIInstrumentor.instrument_app(app)

@app.on_event("startup")
async def startup_event():
    print("🚀 E-Commerce Backend Started")
    print("📊 OpenTelemetry instrumentation active")
    print("📈 Prometheus metrics at /metrics")
