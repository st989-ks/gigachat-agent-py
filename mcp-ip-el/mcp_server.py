import os
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("IPinfo")

api_key = os.getenv('IPINFO_API_KEY', '')
api_url = "https://api.ipinfo.io/lookup"


class GeoInfo(BaseModel):
    city: str
    region: str
    country: str
    timezone: str
    latitude: float
    longitude: float


class IPLookupInfo(BaseModel):
    ip: str
    city: str
    region: str
    country: str
    timezone: str
    postal_code: str
    asn: str
    org: str
    is_anonymous: bool
    is_hosting: bool
    is_anycast: bool
    is_mobile: bool


@mcp.tool()
async def ip_geo(ip: str) -> GeoInfo:
    """Get geolocation info for IP address"""
    params = {"token": api_key} if api_key else {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{api_url}/{ip}", params=params)
        response.raise_for_status()
        data = response.json()

    geo_data = data.get("geo", {})
    return GeoInfo(
        city=geo_data.get("city", ""),
        region=geo_data.get("region", ""),
        country=geo_data.get("country", ""),
        timezone=geo_data.get("timezone", ""),
        latitude=float(geo_data.get("latitude", 0)),
        longitude=float(geo_data.get("longitude", 0))
    )


@mcp.tool()
async def ip_lookup(ip: str) -> IPLookupInfo:
    """Full lookup info for IP address with ASN and network flags"""
    params = {"token": api_key} if api_key else {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{api_url}/{ip}", params=params)
        response.raise_for_status()
        data = response.json()

    geo_data = data.get("geo", {})
    asn_data = data.get("as", {})

    return IPLookupInfo(
        ip=data.get("ip", ip),
        city=geo_data.get("city", ""),
        region=geo_data.get("region", ""),
        country=geo_data.get("country", ""),
        timezone=geo_data.get("timezone", ""),
        postal_code=geo_data.get("postal_code", ""),
        asn=asn_data.get("asn", ""),
        org=asn_data.get("name", ""),
        is_anonymous=data.get("is_anonymous", False),
        is_hosting=data.get("is_hosting", False),
        is_anycast=data.get("is_anycast", False),
        is_mobile=data.get("is_mobile", False)
    )


def main_start() -> None:
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel as PydanticBaseModel

    fastapi_app = FastAPI()
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class ToolRequest(PydanticBaseModel):
        name: str
        arguments: dict = {}

    @fastapi_app.get("/tools")
    async def get_tools():
        tools = await mcp.list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
        }

    @fastapi_app.post("/call")
    async def call_tool(request: ToolRequest):
        try:
            if request.name == "ip_geo":
                result = await ip_geo(request.arguments.get("ip", ""))
            elif request.name == "ip_lookup":
                result = await ip_lookup(request.arguments.get("ip", ""))
            else:
                raise ValueError(f"Unknown tool: {request.name}")

            return {"result": result.dict() if hasattr(result, 'dict') else result}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @fastapi_app.get("/health")
    async def health():
        return {"status": "ok"}

    uvicorn.run(fastapi_app, host="127.0.0.1", port=5555)
