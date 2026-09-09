from typing import List, Dict, Optional
import networkx as nx
from sqlalchemy.orm import Session

from app.models import Complaint, Transaction, Account, AccountRelationship
from app.schemas.money_flow import (
    FlowTransaction,
    FlowAccount,
    MoneyFlowPath,
    FlowPattern,
    MoneyFlowSummary,
    WithdrawalAssociation,
    MoneyFlowResponse,
    FlowTimingGap,
    AccountFlowResponse
)

def build_flow_graph(transactions: List[Transaction]) -> nx.DiGraph:
    G = nx.DiGraph()
    # Ensure transactions are sorted chronologically
    sorted_tx = sorted(transactions, key=lambda t: t.transaction_time)
    
    for t in sorted_tx:
        # Only consider successful transactions for money flow weight
        is_success = t.transaction_status.lower() in ("completed", "successful", "success")
        amt = float(t.amount) if is_success else 0.0
        
        # Add nodes if not exist
        if not G.has_node(t.sender_account):
            G.add_node(t.sender_account, incoming_amt=0.0, outgoing_amt=0.0, incoming_tx=[], outgoing_tx=[])
        if not G.has_node(t.receiver_account):
            G.add_node(t.receiver_account, incoming_amt=0.0, outgoing_amt=0.0, incoming_tx=[], outgoing_tx=[])
            
        # Update node amounts
        G.nodes[t.sender_account]['outgoing_amt'] += amt
        G.nodes[t.sender_account]['outgoing_tx'].append(t)
        
        G.nodes[t.receiver_account]['incoming_amt'] += amt
        G.nodes[t.receiver_account]['incoming_tx'].append(t)
        
        # We can add an edge or update an existing edge weight
        if G.has_edge(t.sender_account, t.receiver_account):
            G[t.sender_account][t.receiver_account]['weight'] += amt
            G[t.sender_account][t.receiver_account]['transactions'].append(t)
        else:
            G.add_edge(t.sender_account, t.receiver_account, weight=amt, transactions=[t])
            
    return G

def get_node_roles(G: nx.DiGraph) -> Dict[str, str]:
    roles = {}
    for node in G.nodes():
        # Remove self-loops from out-degree calculation
        out_edges = [v for u, v in G.out_edges(node) if u != v]
        out_deg = len(out_edges)
        in_deg = G.in_degree(node)
        
        if in_deg == 0 and out_deg > 0:
            roles[node] = "SOURCE"
        elif in_deg > 0 and out_deg > 0:
            roles[node] = "INTERMEDIARY"
        elif in_deg > 0 and out_deg == 0:
            roles[node] = "TERMINAL"
        else:
            roles[node] = "UNKNOWN"
            
    # If a graph has no terminals (e.g. cycle), any node that isn't a source could be considered terminal for pathfinding
    # But ideally, we find nodes with the highest in-degree or something. For now, strict terminal is fine.
    
    return roles

def reconstruct_paths(G: nx.DiGraph, roles: Dict[str, str]) -> List[MoneyFlowPath]:
    sources = [n for n, r in roles.items() if r == "SOURCE"]
    terminals = [n for n, r in roles.items() if r == "TERMINAL"]
    
    paths = []
    path_idx = 1
    
    for s in sources:
        for t in terminals:
            if nx.has_path(G, s, t):
                for simple_path in nx.all_simple_paths(G, s, t):
                    # Gather transactions along this path
                    path_tx = []
                    total_amt = 0.0
                    for i in range(len(simple_path) - 1):
                        u = simple_path[i]
                        v = simple_path[i+1]
                        edges_tx = G[u][v]['transactions']
                        path_tx.extend(edges_tx)
                        total_amt += sum(float(tx.amount) for tx in edges_tx if tx.transaction_status.lower() in ("completed", "successful", "success"))
                    
                    if not path_tx:
                        continue
                        
                    sorted_path_tx = sorted(path_tx, key=lambda x: x.transaction_time)
                    paths.append(MoneyFlowPath(
                        path_id=f"PATH_{path_idx:03d}",
                        accounts=simple_path,
                        transactions=[tx.transaction_id for tx in sorted_path_tx],
                        total_amount=total_amt,
                        start_time=sorted_path_tx[0].transaction_time.isoformat(),
                        end_time=sorted_path_tx[-1].transaction_time.isoformat()
                    ))
                    path_idx += 1
    return paths

def detect_patterns(G: nx.DiGraph, paths: List[MoneyFlowPath]) -> List[FlowPattern]:
    patterns = []
    
    # MULTI_HOP_TRANSFER
    multi_hop_paths = [p for p in paths if len(p.accounts) > 3] # More than 2 edges
    if multi_hop_paths:
        patterns.append(FlowPattern(
            type="MULTI_HOP_TRANSFER",
            description="Funds pass through multiple intermediary accounts.",
            accounts=list({acc for p in multi_hop_paths for acc in p.accounts}),
            transactions=list({tx for p in multi_hop_paths for tx in p.transactions})
        ))
        
    for node in G.nodes():
        in_deg = G.in_degree(node)
        out_deg = G.out_degree(node)
        
        # SPLIT_TRANSFER
        if out_deg > 1:
            out_tx = [tx.transaction_id for tx in G.nodes[node]['outgoing_tx']]
            patterns.append(FlowPattern(
                type="SPLIT_TRANSFER",
                description=f"Account {node} splits funds to multiple receivers.",
                accounts=[node] + [v for _, v in G.out_edges(node)],
                transactions=out_tx
            ))
            
        # CONSOLIDATED_TRANSFER
        if in_deg > 1:
            in_tx = [tx.transaction_id for tx in G.nodes[node]['incoming_tx']]
            patterns.append(FlowPattern(
                type="CONSOLIDATED_TRANSFER",
                description=f"Account {node} consolidates funds from multiple senders.",
                accounts=[u for u, _ in G.in_edges(node)] + [node],
                transactions=in_tx
            ))
            
        # RAPID_FORWARDING
        if in_deg > 0 and out_deg > 0:
            in_tx_list = sorted(G.nodes[node]['incoming_tx'], key=lambda t: t.transaction_time)
            out_tx_list = sorted(G.nodes[node]['outgoing_tx'], key=lambda t: t.transaction_time)
            
            if in_tx_list and out_tx_list:
                first_in = in_tx_list[0].transaction_time
                first_out = out_tx_list[0].transaction_time
                if (first_out - first_in).total_seconds() < 3600 and first_out >= first_in: # Less than 1 hour
                    patterns.append(FlowPattern(
                        type="RAPID_FORWARDING",
                        description=f"Account {node} forwards funds rapidly after receiving.",
                        accounts=[node],
                        transactions=[in_tx_list[0].transaction_id, out_tx_list[0].transaction_id]
                    ))
                    
    return patterns

def reconstruct_money_flow(complaint_id: str, db: Session) -> Optional[MoneyFlowResponse]:
    transactions = db.query(Transaction).filter(Transaction.complaint_id == complaint_id).all()
    if not transactions:
        return None
        
    G = build_flow_graph(transactions)
    roles = get_node_roles(G)
    
    # Fetch accounts
    account_ids = list(G.nodes())
    accounts = db.query(Account).filter(Account.account_id.in_(account_ids)).all()
    acc_map = {a.account_id: a for a in accounts}
    
    flow_accounts = []
    for node in G.nodes():
        acc = acc_map.get(node)
        in_amt = G.nodes[node]['incoming_amt']
        out_amt = G.nodes[node]['outgoing_amt']
        
        flow_accounts.append(FlowAccount(
            account_id=node,
            account_type=acc.account_type if acc else None,
            district=acc.district_id if acc else None,
            latitude=float(acc.latitude) if acc else None,
            longitude=float(acc.longitude) if acc else None,
            role=roles[node],
            total_incoming=in_amt,
            total_outgoing=out_amt,
            observed_remaining=in_amt - out_amt if roles[node] != "SOURCE" else 0.0,
            incoming_transactions=[t.transaction_id for t in G.nodes[node]['incoming_tx']],
            outgoing_transactions=[t.transaction_id for t in G.nodes[node]['outgoing_tx']]
        ))
        
    sources = [fa for fa in flow_accounts if fa.role == "SOURCE"]
    intermediaries = [fa for fa in flow_accounts if fa.role == "INTERMEDIARY"]
    terminals = [fa for fa in flow_accounts if fa.role == "TERMINAL"]
    
    paths = reconstruct_paths(G, roles)
    patterns = detect_patterns(G, paths)
    
    districts = {a.district_id for a in accounts if a.district_id}
    
    total_successful = sum(float(t.amount) for t in transactions if t.transaction_status.lower() in ("completed", "successful", "success"))
    
    summary = MoneyFlowSummary(
        total_accounts=len(flow_accounts),
        source_accounts=len(sources),
        intermediary_accounts=len(intermediaries),
        terminal_accounts=len(terminals),
        total_successful_amount=total_successful,
        total_paths=len(paths),
        max_hops=max((len(p.accounts)-1 for p in paths), default=0),
        districts_involved=len(districts)
    )
    
    return MoneyFlowResponse(
        complaint_id=complaint_id,
        source_accounts=sources,
        intermediary_accounts=intermediaries,
        terminal_accounts=terminals,
        paths=paths,
        account_flows=flow_accounts,
        flow_patterns=patterns,
        flow_summary=summary,
        withdrawal_associations=[] # Explicitly not filled without withdrawal associations yet
    )

def get_account_flow(complaint_id: str, account_id: str, db: Session) -> Optional[AccountFlowResponse]:
    transactions = db.query(Transaction).filter(Transaction.complaint_id == complaint_id).all()
    if not transactions:
        return None
        
    G = build_flow_graph(transactions)
    if not G.has_node(account_id):
        return None
        
    roles = get_node_roles(G)
    acc = db.query(Account).filter(Account.account_id == account_id).first()
    
    in_tx_objs = sorted(G.nodes[account_id]['incoming_tx'], key=lambda t: t.transaction_time)
    out_tx_objs = sorted(G.nodes[account_id]['outgoing_tx'], key=lambda t: t.transaction_time)
    
    in_tx = [FlowTransaction(
        transaction_id=t.transaction_id,
        timestamp=t.transaction_time.isoformat(),
        amount=float(t.amount),
        status=t.transaction_status
    ) for t in in_tx_objs]
    
    out_tx = [FlowTransaction(
        transaction_id=t.transaction_id,
        timestamp=t.transaction_time.isoformat(),
        amount=float(t.amount),
        status=t.transaction_status
    ) for t in out_tx_objs]
    
    time_gaps = []
    # Simplified gap logic: compare all incoming to all subsequent outgoing
    for itx in in_tx_objs:
        for otx in out_tx_objs:
            if otx.transaction_time >= itx.transaction_time:
                time_gaps.append(FlowTimingGap(
                    from_transaction=itx.transaction_id,
                    to_transaction=otx.transaction_id,
                    time_gap_seconds=(otx.transaction_time - itx.transaction_time).total_seconds(),
                    amount_before=float(itx.amount),
                    amount_after=float(otx.amount)
                ))
    
    in_amt = G.nodes[account_id]['incoming_amt']
    out_amt = G.nodes[account_id]['outgoing_amt']
    
    return AccountFlowResponse(
        account_id=account_id,
        role=roles[account_id],
        district=acc.district_id if acc else None,
        incoming_transactions=in_tx,
        outgoing_transactions=out_tx,
        total_incoming=in_amt,
        total_outgoing=out_amt,
        observed_remaining=in_amt - out_amt if roles[account_id] != "SOURCE" else 0.0,
        time_gaps=time_gaps
    )
