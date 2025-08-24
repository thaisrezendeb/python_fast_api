from fastapi import APIRouter
from pydantic import BaseModel

from routers.items import Item
from core.utils import Tags


class Offer(BaseModel):
    name: str
    description: str | None = None
    total_price: float
    items: list[Item]


router = APIRouter()


@router.post("/offers/", tags=[Tags.offers])
async def create_offer(offer: Offer) -> Offer:
    return offer
