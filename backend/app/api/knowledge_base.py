"""Knowledge Base API Routes"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import KnowledgeBaseEntry
from app.services.rag_service import get_rag_service
from app.services.cache_service import get_cache_service
from app.security import rate_limit, require_auth
from typing import List
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", dependencies=[Depends(rate_limit("RATE_LIMIT_KB_UPLOADS"))])
async def search_knowledge_base(
    query: str,
    entry_type: str = "product",
    top_k: int = 5,
):
    """Search knowledge base with caching"""
    try:
        cache = get_cache_service()
        cache_key = cache.cache_key_kb_search(f"{query}:{top_k}", entry_type=entry_type)
        cached_result = await cache.get(cache_key)
        if cached_result:
            return cached_result

        rag_service = get_rag_service()
        
        if entry_type == "product":
            results = rag_service.search_products(query, top_k=top_k)
        elif entry_type == "service":
            results = rag_service.search_services(query, top_k=top_k)
        else:
            raise HTTPException(status_code=400, detail="Invalid entry type")
        
        response_payload = {
            "query": query,
            "entry_type": entry_type,
            "results": results,
        }
        await cache.set(cache_key, response_payload, ttl=600)
        return response_payload
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products")
async def list_products(
    skip: int = 0,
    limit: int = 20,
):
    """List all products with Redis caching"""
    try:
        cache = get_cache_service()
        cache_key = cache.cache_key_products()
        products = await cache.get(cache_key)
        
        if products is None:
            rag_service = get_rag_service()
            products = rag_service.get_all_products()
            await cache.set(cache_key, products, ttl=600)
        
        # Apply pagination
        total = len(products)
        products_page = products[skip:skip + limit]
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": products_page,
        }
    
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def list_services(
    skip: int = 0,
    limit: int = 20,
):
    """List all services with Redis caching"""
    try:
        cache = get_cache_service()
        cache_key = cache.cache_key_services()
        services = await cache.get(cache_key)
        
        if services is None:
            rag_service = get_rag_service()
            services = rag_service.get_all_services()
            await cache.set(cache_key, services, ttl=600)
        
        # Apply pagination
        total = len(services)
        services_page = services[skip:skip + limit]
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "services": services_page,
        }
    
    except Exception as e:
        logger.error(f"Error listing services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/upload", dependencies=[Depends(require_auth), Depends(rate_limit("RATE_LIMIT_KB_UPLOADS"))])
async def upload_products(
    file: UploadFile = File(...),
):
    """Upload products to knowledge base and invalidate cache"""
    try:
        content = await file.read()
        products_data = json.loads(content)
        
        rag_service = get_rag_service()
        rag_service.add_products(products_data)
        
        # Invalidate cache
        cache = get_cache_service()
        await cache.invalidate_kb()
        
        return {
            "message": f"Uploaded {len(products_data)} products",
            "count": len(products_data),
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error uploading products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/services/upload", dependencies=[Depends(require_auth), Depends(rate_limit("RATE_LIMIT_KB_UPLOADS"))])
async def upload_services(
    file: UploadFile = File(...),
):
    """Upload services to knowledge base and invalidate cache"""
    try:
        content = await file.read()
        services_data = json.loads(content)
        
        rag_service = get_rag_service()
        rag_service.add_services(services_data)
        
        # Invalidate cache
        cache = get_cache_service()
        await cache.invalidate_kb()
        
        return {
            "message": f"Uploaded {len(services_data)} services",
            "count": len(services_data),
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error uploading services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
