from typing import List, Dict, Optional
import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import Complaint, Transaction, Account, AccountRelationship
from app.schemas.network_analysis import (
    AnalysisNetworkNode,
    AnalysisNetworkEdge,
    CentralityMetrics,
    NetworkComponent,
    DistrictDistribution,
    NetworkSummary,
    NetworkIndicator,
    SelfLoopInfo,
    ReciprocalConnection,
    NetworkAnalysisResponse,
    GraphNode,
    GraphEdge,
    NetworkGraphResponse,
    AccountNetworkResponse
)

def build_network_graph(transactions: List[Transaction], relationships: List[AccountRelationship]) -> nx.DiGraph:
    G = nx.DiGraph()
    
    # 1. Add edges from transactions (representing financial connections)
    for t in transactions:
        is_success = t.transaction_status.lower() in ("completed", "successful", "success")
        amt = float(t.amount) if is_success else 0.0
        
        # Add nodes with basic initialized attributes
        if not G.has_node(t.sender_account):
            G.add_node(t.sender_account, incoming_amt=0.0, outgoing_amt=0.0, in_tx_count=0, out_tx_count=0)
        if not G.has_node(t.receiver_account):
            G.add_node(t.receiver_account, incoming_amt=0.0, outgoing_amt=0.0, in_tx_count=0, out_tx_count=0)
            
        G.nodes[t.sender_account]['outgoing_amt'] += amt
        G.nodes[t.sender_account]['out_tx_count'] += 1
        
        G.nodes[t.receiver_account]['incoming_amt'] += amt
        G.nodes[t.receiver_account]['in_tx_count'] += 1
        
        if G.has_edge(t.sender_account, t.receiver_account):
            G[t.sender_account][t.receiver_account]['weight'] += amt
            G[t.sender_account][t.receiver_account]['tx_count'] += 1
            G[t.sender_account][t.receiver_account]['tx_ids'].append(t.transaction_id)
            # Update timestamps
            timestamps = G[t.sender_account][t.receiver_account]['timestamps']
            timestamps.append(t.transaction_time)
            G[t.sender_account][t.receiver_account]['first_tx'] = min(timestamps).isoformat()
            G[t.sender_account][t.receiver_account]['last_tx'] = max(timestamps).isoformat()
        else:
            G.add_edge(t.sender_account, t.receiver_account, 
                       weight=amt, 
                       tx_count=1, 
                       tx_ids=[t.transaction_id],
                       rel_ids=[],
                       rel_types=[],
                       timestamps=[t.transaction_time],
                       first_tx=t.transaction_time.isoformat(),
                       last_tx=t.transaction_time.isoformat())

    # 2. Add edges/metadata from relationships (representing structural connections)
    # Only if they fall within the same set of nodes or we expand? 
    # For now, let's map relationships between the accounts involved in the transactions.
    # To be safe, we add nodes if a relationship is tied directly to the complaint.
    for r in relationships:
        if not G.has_node(r.source_account):
            G.add_node(r.source_account, incoming_amt=0.0, outgoing_amt=0.0, in_tx_count=0, out_tx_count=0)
        if not G.has_node(r.target_account):
            G.add_node(r.target_account, incoming_amt=0.0, outgoing_amt=0.0, in_tx_count=0, out_tx_count=0)
            
        if G.has_edge(r.source_account, r.target_account):
            G[r.source_account][r.target_account]['rel_ids'].append(r.relationship_id)
            G[r.source_account][r.target_account]['rel_types'].append(r.relationship_type)
        else:
            G.add_edge(r.source_account, r.target_account,
                       weight=0.0,
                       tx_count=0,
                       tx_ids=[],
                       rel_ids=[r.relationship_id],
                       rel_types=[r.relationship_type],
                       timestamps=[],
                       first_tx=None,
                       last_tx=None)
    
    return G

def compute_centralities(G: nx.DiGraph) -> Dict[str, CentralityMetrics]:
    metrics = {}
    if len(G.nodes) == 0:
        return metrics
        
    try:
        # Pagerank can fail if graph is empty, but we checked.
        pr = nx.pagerank(G, alpha=0.85, weight='weight')
    except Exception:
        pr = {n: 0.0 for n in G.nodes}
        
    deg = nx.degree_centrality(G)
    bet = nx.betweenness_centrality(G, weight=None) # Topological betweenness
    clo = nx.closeness_centrality(G)
    
    for n in G.nodes:
        metrics[n] = CentralityMetrics(
            degree_centrality=deg.get(n, 0.0),
            betweenness_centrality=bet.get(n, 0.0),
            closeness_centrality=clo.get(n, 0.0),
            pagerank=pr.get(n, 0.0)
        )
    return metrics

def analyze_network(complaint_id: str, db: Session) -> Optional[NetworkAnalysisResponse]:
    transactions = db.query(Transaction).filter(Transaction.complaint_id == complaint_id).all()
    
    # Extract accounts involved in transactions
    tx_accs = {t.sender_account for t in transactions} | {t.receiver_account for t in transactions}
    
    if not tx_accs:
        return None
        
    # Get relationships linking any of these accounts
    # For a true complaint-scoped network, we look at relationships where BOTH sides are in tx_accs
    relationships = db.query(AccountRelationship).filter(
        AccountRelationship.source_account.in_(tx_accs) &
        AccountRelationship.target_account.in_(tx_accs)
    ).all()
    
    G = build_network_graph(transactions, relationships)
    
    # Filter to only the strongly connected or relevant nodes if the graph explodes, 
    # but for prototype, we keep it as built.
    
    # Fetch account metadata
    account_ids = list(G.nodes())
    accounts = db.query(Account).filter(Account.account_id.in_(account_ids)).all()
    acc_map = {a.account_id: a for a in accounts}
    
    # Compute metrics
    centralities = compute_centralities(G)
    
    nodes: List[AnalysisNetworkNode] = []
    for n in G.nodes():
        a = acc_map.get(n)
        nodes.append(AnalysisNetworkNode(
            account_id=n,
            account_role=a.account_type if a else None,
            district=a.district_id if a else None,
            city=a.city if a else None,
            latitude=float(a.latitude) if a and a.latitude else None,
            longitude=float(a.longitude) if a and a.longitude else None,
            incoming_transaction_count=G.nodes[n]['in_tx_count'],
            outgoing_transaction_count=G.nodes[n]['out_tx_count'],
            total_incoming_amount=G.nodes[n]['incoming_amt'],
            total_outgoing_amount=G.nodes[n]['outgoing_amt'],
            in_degree=G.in_degree(n),
            out_degree=G.out_degree(n),
            total_degree=G.degree(n),
            centrality=centralities.get(n)
        ))
        
    edges: List[AnalysisNetworkEdge] = []
    for u, v, data in G.edges(data=True):
        edges.append(AnalysisNetworkEdge(
            source=u,
            target=v,
            transaction_ids=data['tx_ids'],
            relationship_ids=data['rel_ids'],
            relationship_types=data['rel_types'],
            transaction_count=data['tx_count'],
            total_transferred_amount=data['weight'],
            first_transaction_timestamp=data['first_tx'],
            last_transaction_timestamp=data['last_tx']
        ))
        
    # Components
    wcc = list(nx.weakly_connected_components(G))
    scc = list(nx.strongly_connected_components(G))
    
    components = []
    for i, c in enumerate(wcc):
        components.append(NetworkComponent(
            component_id=f"WCC_{i+1:03d}",
            type="WEAK",
            account_count=len(c),
            accounts=list(c)
        ))
    for i, c in enumerate(scc):
        if len(c) > 1: # Only care about non-trivial strong components
            components.append(NetworkComponent(
                component_id=f"SCC_{i+1:03d}",
                type="STRONG",
                account_count=len(c),
                accounts=list(c)
            ))
            
    # District Distribution
    districts = {}
    for a in accounts:
        if a.district_id:
            districts[a.district_id] = districts.get(a.district_id, 0) + 1
    dist_dist = [DistrictDistribution(district=k, account_count=v) for k, v in districts.items()]
    
    # Self loops
    self_loops = []
    for u, v, data in G.edges(data=True):
        if u == v:
            self_loops.append(SelfLoopInfo(
                account_id=u,
                self_loop_count=data['tx_count'],
                self_loop_amount=data['weight']
            ))
            
    # Reciprocal connections
    reciprocal = []
    # To avoid duplicates, iterate undirected, but DiGraph doesn't have an easy reciprocal iterator
    seen_pairs = set()
    for u, v, data in G.edges(data=True):
        if u != v and G.has_edge(v, u):
            pair = tuple(sorted([u, v]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                v_u_data = G[v][u]
                reciprocal.append(ReciprocalConnection(
                    account_a=u,
                    account_b=v,
                    transaction_ids=data['tx_ids'] + v_u_data['tx_ids'],
                    relationship_ids=data['rel_ids'] + v_u_data['rel_ids'],
                    amount_a_to_b=data['weight'],
                    amount_b_to_a=v_u_data['weight']
                ))
                
    # Indicators
    indicators = []
    
    if self_loops:
        indicators.append(NetworkIndicator(
            type="SELF_LOOP_OBSERVED",
            severity="LOW",
            description="Accounts transferring money to themselves, often a sign of layering or obfuscation.",
            accounts=[sl.account_id for sl in self_loops],
            evidence=[]
        ))
        
    if reciprocal:
        indicators.append(NetworkIndicator(
            type="RECIPROCAL_CONNECTION",
            severity="MEDIUM",
            description="Accounts sending money back and forth, indicating a strong bidirectional link.",
            accounts=list(seen_pairs)[0] if seen_pairs else [], # Just a representative
            evidence=[]
        ))
        
    # High connectivity (e.g. max degree > average * 2 and degree > 3)
    avg_deg = sum(dict(G.degree()).values()) / len(G.nodes()) if G.nodes() else 0
    high_deg_nodes = [n for n, d in G.degree() if d > max(3, avg_deg * 2)]
    if high_deg_nodes:
        indicators.append(NetworkIndicator(
            type="HIGH_CONNECTIVITY",
            severity="MEDIUM",
            description="Nodes with unusually high connectivity relative to the complaint network.",
            accounts=high_deg_nodes,
            evidence=[]
        ))
        
    # Bridge Accounts (High betweenness)
    if centralities:
        avg_bet = sum(c.betweenness_centrality for c in centralities.values()) / len(centralities)
        bridge_nodes = [n for n, c in centralities.items() if c.betweenness_centrality > 0.1 and c.betweenness_centrality > avg_bet * 3]
        if bridge_nodes:
            indicators.append(NetworkIndicator(
                type="POTENTIAL_BRIDGE_ACCOUNT",
                severity="HIGH",
                description="Nodes with high betweenness centrality acting as bridges between clusters.",
                accounts=bridge_nodes,
                evidence=[]
            ))
            
    summary = NetworkSummary(
        total_accounts=len(G.nodes()),
        total_edges=len(G.edges()),
        connected_components=len(wcc),
        strong_components=len([c for c in scc if len(c) > 1]),
        districts_involved=len(districts),
        maximum_degree=max(dict(G.degree()).values(), default=0),
        average_degree=avg_deg,
        network_density=nx.density(G)
    )
    
    return NetworkAnalysisResponse(
        complaint_id=complaint_id,
        nodes=nodes,
        edges=edges,
        network_summary=summary,
        centrality=list(centralities.values()),
        components=components,
        district_distribution=dist_dist,
        self_loops=self_loops,
        reciprocal_connections=reciprocal,
        indicators=indicators
    )

def get_network_graph(complaint_id: str, db: Session) -> Optional[NetworkGraphResponse]:
    analysis = analyze_network(complaint_id, db)
    if not analysis:
        return None
        
    g_nodes = [GraphNode(
        id=n.account_id,
        label=n.account_id,
        district=n.district,
        latitude=n.latitude,
        longitude=n.longitude
    ) for n in analysis.nodes]
    
    g_edges = [GraphEdge(
        source=e.source,
        target=e.target,
        weight=e.total_transferred_amount,
        transaction_count=e.transaction_count
    ) for e in analysis.edges]
    
    return NetworkGraphResponse(nodes=g_nodes, edges=g_edges)

def get_account_network(complaint_id: str, account_id: str, db: Session) -> Optional[AccountNetworkResponse]:
    analysis = analyze_network(complaint_id, db)
    if not analysis:
        return None
        
    node = next((n for n in analysis.nodes if n.account_id == account_id), None)
    if not node:
        return None
        
    in_edges = [e for e in analysis.edges if e.target == account_id]
    out_edges = [e for e in analysis.edges if e.source == account_id]
    connected = list(set([e.source for e in in_edges] + [e.target for e in out_edges]))
    
    comp = next((c.component_id for c in analysis.components if account_id in c.accounts and c.type == "WEAK"), None)
    
    inds = [i for i in analysis.indicators if account_id in i.accounts]
    
    return AccountNetworkResponse(
        account=node,
        degree_metrics={
            "in_degree": node.in_degree,
            "out_degree": node.out_degree,
            "total_degree": node.total_degree
        },
        centrality_metrics=node.centrality,
        incoming_connections=in_edges,
        outgoing_connections=out_edges,
        connected_accounts=connected,
        component=comp,
        district=node.district,
        indicators=inds
    )
