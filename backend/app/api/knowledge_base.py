"""Knowledge Base API Routes"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import KnowledgeBaseEntry
from app.services.rag_service import get_rag_service
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
    """Search knowledge base"""
    try:
        rag_service = get_rag_service()
        
        if entry_type == "product":
            results = rag_service.search_products(query, top_k=top_k)
        elif entry_type == "service":
            results = rag_service.search_services(query, top_k=top_k)
        else:
            raise HTTPException(status_code=400, detail="Invalid entry type")
        
        return {
            "query": query,
            "entry_type": entry_type,
            "results": results,
        }
    
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
    """List all products"""
    try:
        rag_service = get_rag_service()
        products = rag_service.get_all_products()
        
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
    """List all services"""
    try:
        rag_service = get_rag_service()
        services = rag_service.get_all_services()
        
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
    """Upload products to knowledge base"""
    try:
        content = await file.read()
        products_data = json.loads(content)
        
        rag_service = get_rag_service()
        rag_service.add_products(products_data)
        
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
    """Upload services to knowledge base"""
    try:
        content = await file.read()
        services_data = json.loads(content)
        
        rag_service = get_rag_service()
        rag_service.add_services(services_data)
        
        return {
            "message": f"Uploaded {len(services_data)} services",
            "count": len(services_data),
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error uploading services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
