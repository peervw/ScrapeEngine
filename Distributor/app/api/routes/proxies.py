from fastapi import APIRouter, HTTPException, Depends
from ...core.security import token_required
from ...models.proxy import ProxyCreate, WebshareToken
from ...db.session import get_db_connection
from ..dependencies import get_proxy_manager
from ...services.proxy_manager import ProxyManager

router = APIRouter(prefix="/api/proxies", tags=["proxies"])

@router.get("")
async def get_proxies(
    proxy_manager: ProxyManager = Depends(get_proxy_manager),
    authorization: str = Depends(token_required)
):
    """Get all proxies and their stats"""
    return {
        "total_proxies": len(proxy_manager.proxies),
        "available_proxies": len(proxy_manager.available_proxies),
        "proxies": proxy_manager.get_proxy_stats()
    }

@router.post("")
async def add_proxy(
    proxy: ProxyCreate,
    proxy_manager: ProxyManager = Depends(get_proxy_manager),
    authorization: str = Depends(token_required)
):
    """Add a proxy manually"""
    try:
        await proxy_manager.add_manual_proxy(
            proxy.host,
            proxy.port,
            proxy.username,
            proxy.password
        )
        return {"status": "success", "message": f"Added proxy {proxy.host}:{proxy.port}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{host}")
async def delete_proxy(
    host: str,
    proxy_manager: ProxyManager = Depends(get_proxy_manager),
    authorization: str = Depends(token_required)
):
    """Delete a proxy"""
    await proxy_manager.delete_proxy(host)
    return {"status": "success", "message": f"Deleted proxy {host}"}

@router.post("/webshare")
async def set_webshare_token(
    token: WebshareToken,
    proxy_manager: ProxyManager = Depends(get_proxy_manager),
    authorization: str = Depends(token_required)
):
    """Set Webshare API token and refresh proxies"""
    try:
        # Store token in database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO settings (key, value) 
            VALUES ('webshare_token', %s) 
            ON CONFLICT (key) DO UPDATE SET value = %s
        ''', (token.token, token.token))
        conn.commit()
        conn.close()

        # Update proxy manager
        await proxy_manager.set_webshare_token(token.token)
        return {"status": "success", "message": "Updated Webshare token and refreshed proxies"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refresh")
async def refresh_proxies(
    proxy_manager: ProxyManager = Depends(get_proxy_manager),
    authorization: str = Depends(token_required)
):
    """Manually trigger proxy refresh from Webshare"""
    try:
        await proxy_manager.refresh_proxies()
        return {"status": "success", "message": "Refreshed proxies from Webshare"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 