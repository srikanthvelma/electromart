from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from elasticsearch import AsyncElasticsearch
import redis.asyncio as redis
import httpx
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ElectroMart Search Service",
    description="Search microservice for ElectroMart e-commerce platform",
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

# Elasticsearch client
es_client = AsyncElasticsearch(
    hosts=[os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")],
    basic_auth=(os.getenv("ELASTICSEARCH_USER", "elastic"), 
                os.getenv("ELASTICSEARCH_PASSWORD", "changeme"))
)

# Redis client
redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379"),
    decode_responses=True
)

# HTTP client for calling other services
http_client = httpx.AsyncClient()

# Index name for products
PRODUCTS_INDEX = "electromart_products"

@app.on_event("startup")
async def startup_event():
    """Initialize connections and create index on startup"""
    try:
        # Test Elasticsearch connection
        await es_client.ping()
        logger.info("Connected to Elasticsearch")
        
        # Test Redis connection
        await redis_client.ping()
        logger.info("Connected to Redis")
        
        # Create products index if it doesn't exist
        if not await es_client.indices.exists(index=PRODUCTS_INDEX):
            await create_products_index()
            logger.info(f"Created index: {PRODUCTS_INDEX}")
            
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    await es_client.close()
    await redis_client.close()
    await http_client.aclose()

async def create_products_index():
    """Create the products index with proper mapping"""
    mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "long"},
                "name": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "description": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "category": {
                    "type": "keyword"
                },
                "brand": {
                    "type": "keyword"
                },
                "price": {"type": "float"},
                "rating": {"type": "float"},
                "review_count": {"type": "integer"},
                "in_stock": {"type": "boolean"},
                "tags": {
                    "type": "keyword"
                },
                "specifications": {
                    "type": "object",
                    "dynamic": True
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "product_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop", "snowball"]
                    }
                }
            }
        }
    }
    
    await es_client.indices.create(index=PRODUCTS_INDEX, body=mapping)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Elasticsearch
        es_health = await es_client.ping()
        
        # Check Redis
        redis_health = await redis_client.ping()
        
        return {
            "status": "healthy",
            "service": "Search Service",
            "timestamp": datetime.utcnow().isoformat(),
            "elasticsearch": "connected" if es_health else "disconnected",
            "redis": "connected" if redis_health else "disconnected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "Search Service",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ElectroMart Search Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "search": "/api/search",
            "suggest": "/api/suggest",
            "index_product": "/api/index-product",
            "delete_product": "/api/delete-product/{product_id}"
        }
    }

@app.get("/api/search")
async def search_products(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    sort_by: Optional[str] = Query("relevance", description="Sort field (relevance, price, rating, name)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Results per page")
):
    """Search products with filters and pagination"""
    try:
        # Check cache first
        cache_key = f"search:{hash(f'{q}{category}{brand}{min_price}{max_price}{in_stock}{sort_by}{sort_order}{page}{size}')}"
        cached_result = await redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        # Build search query
        query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": q,
                            "fields": ["name^3", "description^2", "tags", "brand", "category"],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    }
                ],
                "filter": []
            }
        }
        
        # Add filters
        if category:
            query["bool"]["filter"].append({"term": {"category": category}})
        
        if brand:
            query["bool"]["filter"].append({"term": {"brand": brand}})
        
        if min_price is not None or max_price is not None:
            price_filter = {"range": {"price": {}}}
            if min_price is not None:
                price_filter["range"]["price"]["gte"] = min_price
            if max_price is not None:
                price_filter["range"]["price"]["lte"] = max_price
            query["bool"]["filter"].append(price_filter)
        
        if in_stock is not None:
            query["bool"]["filter"].append({"term": {"in_stock": in_stock}})
        
        # Build sort
        sort = []
        if sort_by == "price":
            sort.append({"price": {"order": sort_order}})
        elif sort_by == "rating":
            sort.append({"rating": {"order": sort_order}})
        elif sort_by == "name":
            sort.append({"name.keyword": {"order": sort_order}})
        else:  # relevance
            sort.append("_score")
        
        # Execute search
        search_body = {
            "query": query,
            "sort": sort,
            "from": (page - 1) * size,
            "size": size,
            "highlight": {
                "fields": {
                    "name": {},
                    "description": {}
                }
            },
            "aggs": {
                "categories": {
                    "terms": {"field": "category", "size": 20}
                },
                "brands": {
                    "terms": {"field": "brand", "size": 20}
                },
                "price_ranges": {
                    "range": {
                        "field": "price",
                        "ranges": [
                            {"to": 50},
                            {"from": 50, "to": 100},
                            {"from": 100, "to": 200},
                            {"from": 200, "to": 500},
                            {"from": 500}
                        ]
                    }
                }
            }
        }
        
        response = await es_client.search(index=PRODUCTS_INDEX, body=search_body)
        
        # Process results
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        
        products = []
        for hit in hits:
            product = hit["_source"]
            product["score"] = hit["_score"]
            
            # Add highlights
            if "highlight" in hit:
                product["highlights"] = hit["highlight"]
            
            products.append(product)
        
        # Process aggregations
        aggs = response.get("aggregations", {})
        
        result = {
            "products": products,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
            "aggregations": {
                "categories": [{"key": bucket["key"], "count": bucket["doc_count"]} 
                              for bucket in aggs.get("categories", {}).get("buckets", [])],
                "brands": [{"key": bucket["key"], "count": bucket["doc_count"]} 
                          for bucket in aggs.get("brands", {}).get("buckets", [])],
                "price_ranges": [{"key": bucket["key"], "count": bucket["doc_count"]} 
                                for bucket in aggs.get("price_ranges", {}).get("buckets", [])]
            }
        }
        
        # Cache result for 5 minutes
        await redis_client.setex(cache_key, 300, json.dumps(result))
        
        return result
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/suggest")
async def suggest_products(
    q: str = Query(..., description="Search query for suggestions"),
    size: int = Query(5, ge=1, le=20, description="Number of suggestions")
):
    """Get product search suggestions"""
    try:
        # Check cache
        cache_key = f"suggest:{q}:{size}"
        cached_result = await redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        # Build suggestion query
        suggest_body = {
            "suggest": {
                "product_suggestions": {
                    "prefix": q,
                    "completion": {
                        "field": "name_suggest",
                        "size": size,
                        "skip_duplicates": True
                    }
                },
                "category_suggestions": {
                    "prefix": q,
                    "completion": {
                        "field": "category_suggest",
                        "size": size,
                        "skip_duplicates": True
                    }
                }
            }
        }
        
        response = await es_client.search(index=PRODUCTS_INDEX, body=suggest_body)
        
        suggestions = {
            "products": [],
            "categories": []
        }
        
        # Process product suggestions
        for option in response["suggest"]["product_suggestions"][0]["options"]:
            suggestions["products"].append({
                "text": option["text"],
                "score": option["_score"]
            })
        
        # Process category suggestions
        for option in response["suggest"]["category_suggestions"][0]["options"]:
            suggestions["categories"].append({
                "text": option["text"],
                "score": option["_score"]
            })
        
        # Cache for 10 minutes
        await redis_client.setex(cache_key, 600, json.dumps(suggestions))
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Suggestion error: {e}")
        raise HTTPException(status_code=500, detail="Suggestion failed")

@app.post("/api/index-product")
async def index_product(product: Dict[str, Any]):
    """Index a product in Elasticsearch"""
    try:
        product_id = product.get("id")
        if not product_id:
            raise HTTPException(status_code=400, detail="Product ID is required")
        
        # Add suggestion fields
        product["name_suggest"] = {
            "input": [product["name"]] + product["name"].split(),
            "weight": product.get("rating", 0) * product.get("review_count", 1)
        }
        
        product["category_suggest"] = {
            "input": [product["category"]],
            "weight": 1
        }
        
        # Index the product
        await es_client.index(
            index=PRODUCTS_INDEX,
            id=product_id,
            body=product
        )
        
        # Clear related caches
        await clear_search_cache()
        
        return {"message": "Product indexed successfully", "product_id": product_id}
        
    except Exception as e:
        logger.error(f"Index product error: {e}")
        raise HTTPException(status_code=500, detail="Failed to index product")

@app.delete("/api/delete-product/{product_id}")
async def delete_product(product_id: int):
    """Delete a product from Elasticsearch"""
    try:
        await es_client.delete(index=PRODUCTS_INDEX, id=product_id)
        
        # Clear related caches
        await clear_search_cache()
        
        return {"message": "Product deleted successfully", "product_id": product_id}
        
    except Exception as e:
        logger.error(f"Delete product error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete product")

async def clear_search_cache():
    """Clear search-related caches"""
    try:
        # Get all search cache keys
        search_keys = await redis_client.keys("search:*")
        suggest_keys = await redis_client.keys("suggest:*")
        
        if search_keys:
            await redis_client.delete(*search_keys)
        if suggest_keys:
            await redis_client.delete(*suggest_keys)
            
    except Exception as e:
        logger.error(f"Clear cache error: {e}")

@app.post("/api/sync-products")
async def sync_products():
    """Sync products from Product Service to Elasticsearch"""
    try:
        # Get products from Product Service
        product_service_url = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8001")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{product_service_url}/api/products")
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch products from Product Service")
            
            products = response.json().get("products", [])
        
        # Index each product
        indexed_count = 0
        for product in products:
            try:
                await index_product(product)
                indexed_count += 1
            except Exception as e:
                logger.error(f"Failed to index product {product.get('id')}: {e}")
        
        return {
            "message": "Products synced successfully",
            "total_products": len(products),
            "indexed_count": indexed_count
        }
        
    except Exception as e:
        logger.error(f"Sync products error: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync products")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
