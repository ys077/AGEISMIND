from typing import List
from pydantic import BaseModel, ConfigDict


class RelationshipBase(BaseModel):
    relationship_id: str
    source_account: str
    target_account: str
    relationship_type: str
    total_amount: float
    transaction_count: int


class RelationshipResponse(RelationshipBase):
    model_config = ConfigDict(from_attributes=True)


class NetworkNode(BaseModel):
    id: str
    type: str
    district_id: str
    latitude: float
    longitude: float


class NetworkEdge(BaseModel):
    source: str
    target: str
    relationship_type: str
    total_amount: float


class NetworkResponse(BaseModel):
    complaint_id: str
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
