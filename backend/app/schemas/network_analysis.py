from typing import List, Optional
from pydantic import BaseModel

class CentralityMetrics(BaseModel):
    degree_centrality: float
    betweenness_centrality: float
    closeness_centrality: float
    pagerank: float

class AnalysisNetworkNode(BaseModel):
    account_id: str
    account_role: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    incoming_transaction_count: int
    outgoing_transaction_count: int
    total_incoming_amount: float
    total_outgoing_amount: float
    in_degree: int
    out_degree: int
    total_degree: int
    centrality: Optional[CentralityMetrics] = None

class AnalysisNetworkEdge(BaseModel):
    source: str
    target: str
    transaction_ids: List[str]
    relationship_ids: List[str]
    relationship_types: List[str]
    transaction_count: int
    total_transferred_amount: float
    first_transaction_timestamp: Optional[str] = None
    last_transaction_timestamp: Optional[str] = None

class NetworkSummary(BaseModel):
    total_accounts: int
    total_edges: int
    connected_components: int
    strong_components: int
    districts_involved: int
    maximum_degree: int
    average_degree: float
    network_density: float

class NetworkComponent(BaseModel):
    component_id: str
    type: str # "WEAK" or "STRONG"
    account_count: int
    accounts: List[str]

class DistrictDistribution(BaseModel):
    district: str
    account_count: int

class SelfLoopInfo(BaseModel):
    account_id: str
    self_loop_count: int
    self_loop_amount: float
    indicator: str = "SELF_LOOP_OBSERVED"

class ReciprocalConnection(BaseModel):
    account_a: str
    account_b: str
    transaction_ids: List[str]
    relationship_ids: List[str]
    amount_a_to_b: float
    amount_b_to_a: float

class NetworkIndicator(BaseModel):
    type: str
    severity: str
    description: str
    accounts: List[str]
    evidence: List[str]

class NetworkAnalysisResponse(BaseModel):
    complaint_id: str
    nodes: List[AnalysisNetworkNode]
    edges: List[AnalysisNetworkEdge]
    network_summary: NetworkSummary
    centrality: List[CentralityMetrics]
    components: List[NetworkComponent]
    district_distribution: List[DistrictDistribution]
    self_loops: List[SelfLoopInfo]
    reciprocal_connections: List[ReciprocalConnection]
    indicators: List[NetworkIndicator]

class GraphNode(BaseModel):
    id: str
    label: str
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float
    transaction_count: int

class NetworkGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class AccountNetworkResponse(BaseModel):
    account: AnalysisNetworkNode
    degree_metrics: dict
    centrality_metrics: Optional[CentralityMetrics]
    incoming_connections: List[AnalysisNetworkEdge]
    outgoing_connections: List[AnalysisNetworkEdge]
    connected_accounts: List[str]
    component: Optional[str] = None
    district: Optional[str] = None
    indicators: List[NetworkIndicator]
