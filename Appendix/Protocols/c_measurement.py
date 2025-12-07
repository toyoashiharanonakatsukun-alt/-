# c_measurement.py
import math, random
from typing import Tuple, Dict, Any
import networkx as nx
import numpy as np
# ---------- H: Shannon from degree distribution ----------
def shannon_entropy_degree(G: nx.Graph) -> float:
    degrees = [d for _, d in G.degree()]
    if not degrees:
        return 0.0
    total = sum(degrees)
    if total == 0:
        N = max(1, G.number_of_nodes())
        p = 1.0 / N
        return -N * p * math.log(p, 2)
    ps = [deg/total for deg in degrees if deg > 0]
    H = -sum(p * math.log(p, 2) for p in ps)
    return float(H)
# ---------- R: redundancy via community count ----------
def modularity_redundancy(G: nx.Graph) -> Tuple[float,int,float]:
    N = G.number_of_nodes()
    if N == 0:
        return 0.0, 0, 0.0
    try:
        communities = list(nx.algorithms.community.greedy_modularity_communities(G))
        M = len(communities)
        try:
            Q = nx.algorithms.community.modularity(G, communities)
        except Exception:
            Q = 0.0
    except Exception:
        comps = list(nx.connected_components(G))
        M = len(comps)
        Q = 0.0
    R_raw = M / N
    return float(R_raw), int(M), float(Q)
# ---------- D: hierarchy depth via BFS ----------
def hierarchy_depth_bfs(G: nx.Graph) -> float:
    N = G.number_of_nodes()
    if N == 0:
        return 1.0
    if nx.is_connected(G):
        degrees = dict(G.degree())
        root = max(degrees, key=degrees.get)
        lengths = nx.single_source_shortest_path_length(G, root)
        maxd = max(lengths.values()) if lengths else 1
        return float(max(1.0, maxd))
    else:
        total_nodes = 0
        acc = 0.0
        for comp in nx.connected_components(G):
            sub = G.subgraph(comp)
            n = sub.number_of_nodes()
            total_nodes += n
            if n <= 1:
                d = 1.0
            else:
                degrees = dict(sub.degree())
                root = max(degrees, key=degrees.get)
                lengths = nx.single_source_shortest_path_length(sub, root)
                d = max(lengths.values()) if lengths else 1.0
            acc += d * n
        return float(max(1.0, acc / total_nodes))
# ---------- Full C computation ----------
def compute_C_precise(G: nx.Graph, normalize: bool = True) -> Dict[str,Any]:
    N = G.number_of_nodes()
    H = shannon_entropy_degree(G)
    R_raw, M, Q = modularity_redundancy(G)
    D = hierarchy_depth_bfs(G)
    C_raw = H * R_raw * D
    res = {"N": N, "H": H, "R": R_raw, "M": M, "Q": Q, "D": D, "C_raw": C_raw}
    if normalize:
        denom_H = math.log2(max(2, N))
        H_norm = H / denom_H if denom_H>0 else 0.0
        D_norm = D / (1.0 + math.log2(max(2, N)))
        C_norm = H_norm * R_raw * D_norm
        res.update({"H_norm": H_norm, "D_norm": D_norm, "C_norm": C_norm})
    return res
# ---------- Graph generators ----------
def generate_ER(n=200, p=0.02, seed=None):
    return nx.erdos_renyi_graph(n, p, seed=seed)
def generate_BA(n=200, m=3, seed=None):
    return nx.barabasi_albert_graph(n, m, seed=seed)
def generate_WS(n=200, k=6, p=0.1, seed=None):
    return nx.watts_strogatz_graph(n, k, p, seed=seed)
def generate_lattice(m=14, n=14):
    return nx.convert_node_labels_to_integers(nx.grid_2d_graph(m, n))
def generate_SBM(sizes=[50,50,50,50], p_in=0.08, p_out=0.005, seed=None):
    return nx.stochastic_block_model(sizes, [[p_in if i==j else p_out for j in range(len(sizes))] for i in range(len(sizes))], seed=seed)
# ---------- Validation routine ----------
def validate_on_topologies(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    graphs = {
        "ER_sparse": generate_ER(n=200, p=0.02, seed=seed),
        "ER_dense": generate_ER(n=200, p=0.08, seed=seed),
        "BA": generate_BA(n=200, m=3, seed=seed),
        "WS": generate_WS(n=200, k=6, p=0.1, seed=seed),
        "Lattice": generate_lattice(14,14),
        "SBM_modular": generate_SBM(sizes=[50,50,50,50], p_in=0.08, p_out=0.005, seed=seed)
    }
    results = {}
    for name, G in graphs.items():
        res = compute_C_precise(G, normalize=True)
        results[name] = res
    # Print summary
    header = ["graph", "N", "H", "H_norm", "R", "M", "Q", "D", "D_norm", "C_raw", "C_norm"]
    print("\t".join(header))
    for name, r in results.items():
        print(f"{name}\t{r['N']}\t{r['H']:.3f}\t{r['H_norm']:.3f}\t{r['R']:.3f}\t{r['M']}\t{r['Q']:.3f}\t{r['D']:.3f}\t{r['D_norm']:.3f}\t{r['C_raw']:.3f}\t{r['C_norm']:.4f}")
    return results
if __name__ == "__main__":
    validate_on_topologies()
