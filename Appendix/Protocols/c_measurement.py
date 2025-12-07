# c_measurement.py
import math
import networkx as nx
import numpy as np
from typing import Tuple, Dict, Any

# --- Cの定義定数 ---
# C(G) = H(G) * R(G) * D(G) [24], [25]

# ---------- H: シャノンエントロピー (情報複雑度) ----------
def shannon_entropy_degree(G: nx.Graph) -> float:
    """ノードの次数分布に基づくシャノンエントロピー H(G) を計算する [26], [27]"""
    degrees = [d for _, d in G.degree()]
    if not degrees:
        return 0.0

    total = sum(degrees)
    if total == 0:
        return 0.0

    # 確率質量関数 p_v = deg(v) / sum(deg) [25]
    ps = [deg / total for deg in degrees if deg > 0]
    H = -sum(p * math.log2(p) for p in ps)
    return float(H)

# ---------- R: 冗長性 (コミュニティ数) ----------
def modularity_redundancy(G: nx.Graph) -> Tuple[float, int]:
    """コミュニティ検出に基づき冗長性 R(G) を計算する [28], [27]"""
    N = G.number_of_nodes()
    if N == 0:
        return 0.0, 0
    
    try:
        # greedy_modularity_communities を使用 [28]
        communities = list(nx.algorithms.community.greedy_modularity_communities(G))
        M = len(communities)
    except Exception:
        # 連結成分数をコミュニティ数Mの代理とする [28]
        M = len(list(nx.connected_components(G)))
        
    # 冗長性 R = M / N [25], [27]
    R_raw = M / N
    return float(R_raw), int(M)

# ---------- D: 階層深度 (BFS-tree 深度代理) ----------
def hierarchy_depth_bfs(G: nx.Graph) -> float:
    """最大次数ノードを根としたBFSの最大深度 D(G) を計算する [29], [27]"""
    N = G.number_of_nodes()
    if N == 0:
        return 1.0

    if nx.is_connected(G):
        # 根ノードを最大次数ノードとする [29]
        degrees = dict(G.degree())
        root = max(degrees, key=degrees.get)
        lengths = nx.single_source_shortest_path_length(G, root)
        maxd = max(lengths.values()) if lengths else 1.0
        return float(max(1.0, maxd))
    else:
        # 非連結グラフの場合は成分ごとの重み付き平均を使用 [29]
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

# ---------- 総合複雑性 C の計算 ----------
def compute_C_precise(G: nx.Graph, normalize: bool = True) -> Dict[str, Any]:
    """総合複雑性 C = H * R * D を計算する [24], [30]"""
    
    N = G.number_of_nodes()
    H = shannon_entropy_degree(G)
    R_raw, M = modularity_redundancy(G)
    D = hierarchy_depth_bfs(G)

    # C_raw = H * R * D [24]
    C_raw = H * R_raw * D
    
    res = {"N": N, "H": H, "R": R_raw, "M": M, "D": D, "C_raw": C_raw}

    if normalize:
        # 正規化（スケール問題を避けるため推奨される）[31], [32]
        denom_H = math.log2(max(2, N))
        H_norm = H / denom_H if denom_H > 0 else 0.0
        D_norm = D / (1.0 + math.log2(max(2, N))) # 1.0 + log2(N) で正規化 [31]

        C_norm = H_norm * R_raw * D_norm
        res.update({"H_norm": H_norm, "D_norm": D_norm, "C_norm": C_norm})

    return res

# --- ネットワーク生成関数 (検証用) ---
# generate_ER, generate_BA, generate_lattice などが続く (実装はソースに存在する) [33]-[34]
