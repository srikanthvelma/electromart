from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os
from dotenv import load_dotenv

from database import engine, get_db
from models import Base, Product, Category, Brand
from schemas import ProductCreate, ProductUpdate, ProductResponse, CategoryCreate, BrandCreate
from services.product_service import ProductService
from services.search_service import SearchService

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ElectroMart Product Service",
    description="Product catalog and inventory management service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
product_service = ProductService()
search_service = SearchService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Product Service",
        "version": "1.0.0"
    }

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with service information"""
    return {
        "message": "ElectroMart Product Service",
        "version": "1.0.0",
        "endpoints": {
            "products": "/products",
            "categories": "/categories",
            "brands": "/brands",
            "search": "/search",
            "docs": "/docs"
        }
    }

# Product endpoints
@app.get("/products", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[int] = None,
    brand_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering"""
    try:
        products = product_service.get_products(
            db, skip=skip, limit=limit, 
            category_id=category_id, brand_id=brand_id,
            min_price=min_price, max_price=max_price
        )
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    try:
        product = product_service.get_product(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    try:
        new_product = product_service.create_product(db, product)
        # Index in search service
        await search_service.index_product(new_product)
        return new_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    """Update an existing product"""
    try:
        updated_product = product_service.update_product(db, product_id, product)
        if not updated_product:
            raise HTTPException(status_code=404, detail="Product not found")
        # Update search index
        await search_service.index_product(updated_product)
        return updated_product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    try:
        success = product_service.delete_product(db, product_id)
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")
        # Remove from search index
        await search_service.remove_product(product_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Category endpoints
@app.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    try:
        categories = product_service.get_categories(db)
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    try:
        new_category = product_service.create_category(db, category)
        return new_category
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Brand endpoints
@app.get("/brands")
async def get_brands(db: Session = Depends(get_db)):
    """Get all brands"""
    try:
        brands = product_service.get_brands(db)
        return brands
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/brands", status_code=status.HTTP_201_CREATED)
async def create_brand(brand: BrandCreate, db: Session = Depends(get_db)):
    """Create a new brand"""
    try:
        new_brand = product_service.create_brand(db, brand)
        return new_brand
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoint
@app.get("/search")
async def search_products(
    q: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search products using Elasticsearch"""
    try:
        results = await search_service.search_products(q, skip, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
