# Module 6 Complete: Fraud Network Analysis

We have successfully constructed the Fraud Network Analysis module, pivoting from understanding *how* money flows, to revealing *how* the involved actors are structurally interconnected.

> [!WARNING]
> This analysis is performed strictly on **SYNTHETIC PROTOTYPE DATA**. Network metrics, graph centralities, and structural indicators are investigative aids only and do not establish actual criminal responsibility.

### What was implemented:
- **Pydantic Schemas (`schemas/network_analysis.py`)**: Designed `AnalysisNetworkNode` and `AnalysisNetworkEdge` to represent the structural skeleton, alongside models for centrality metrics and deterministic indicators. We specifically aliased these models to avoid collision with Module 4's schemas.
- **Graph & Business Logic (`services/network_analysis_service.py`)**:
  - **Directed NetworkX Graphing**: Transforms database transactions and known `AccountRelationships` into a rich, unified topology. Nodes represent accounts, while edges carry properties like transaction frequency, weights, and initial/final timestamps.
  - **Centrality Metrics**: Computes `degree`, `betweenness`, `closeness`, and `pagerank` to mathematically highlight key nodes.
  - **Component Detection**: Maps out disconnected clusters (Weak & Strong Components) to see if the complaint breaks down into separate sub-networks.
  - **Topological Flags**: Automatically generates investigative tags based on the network shape:
    - `SELF_LOOP_OBSERVED`: Accounts transferring to themselves (e.g., `ACC100004`).
    - `RECIPROCAL_CONNECTION`: Two nodes bouncing transfers directly back and forth.
    - `HIGH_CONNECTIVITY`: Nodes exhibiting extraordinarily high linkage (e.g., degree > 2 * average).
    - `POTENTIAL_BRIDGE_ACCOUNT`: Highly central nodes linking disparate groups, scoring unusually high on *betweenness centrality*.
- **API Endpoints (`routers/network_analysis.py`)**:
  - `GET /api/analysis/{complaint_id}/network-analysis`: The comprehensive analytical report detailing the network's mathematical properties.
  - `GET /api/analysis/{complaint_id}/network-analysis/graph`: A streamlined endpoint outputting simplified arrays of nodes and edges, optimized for downstream UI graph visualizers (like React Flow or D3).
  - `GET /api/analysis/{complaint_id}/network-analysis/accounts/{account_id}`: Granular perspective mapping the local sub-graph surrounding a specified account.

### How to Run and Test
1. Make sure your PostgreSQL database and the `uvicorn` server are running (`uvicorn app.main:app --reload` inside the `backend/` directory).
2. Visit `http://localhost:8000/docs` to see the new `Network Analysis` endpoints.
3. Check out the UI-ready graph payload for `CC1001`:
   - `http://localhost:8000/api/analysis/CC1001/network-analysis/graph`
4. Run `pytest tests/` in the `backend/` directory. All 24 automated tests covering Modules 3 through 6 are passing!

### Known Limitations
- The underlying synthetic transactions were randomly generated within constraints, which means metrics like `pagerank` may yield less intuitive results than they would on real-world organic data.
- Edges merge both transaction weights and static relationship markers, but clustering mechanisms only identify components mechanically rather than with deep ML embeddings.
