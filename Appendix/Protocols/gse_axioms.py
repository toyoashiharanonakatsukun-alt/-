# gse_axioms.py
import numpy as np
from typing import Dict, Any

# --- 定数と運用閾値 ---
# 第3章 コアパラメータと推奨初期値に基づく [3]
HOMOGENIZATION_THRESHOLD = 0.8  # C_th (Ax. SI): Severance 判定閾値 [4], [3]
UB_MIN_COST = 5.0             # R_UB (Ax. UB): 最小不可避負荷 [4], [3]
THETA_L = 10.0                # Ax. GI 低複雑性ショック係数 (C < 1.0) [4], [5]
THETA_H = 2.0                 # Ax. GI 高複雑性ショック係数 (C >= 1.0) [4], [5]
R_SAFE_COEFF = 0.20           # P. RCS 安全バッファ決定係数 [5]

class GSE_Axioms:
    """GSEシステムの基本となる論理的制約（公理）の集合"""

    def __init__(self, C_th=HOMOGENIZATION_THRESHOLD, UB_min=UB_MIN_COST, theta_L=THETA_L, R_coeff=R_SAFE_COEFF):
        self.C_TH = C_th
        self.UB_MIN = UB_min
        self.THETA_L = theta_L
        self.R_COEFF = R_coeff

    def AX_EX_RESPONSE_CONTINUES(self, R: float) -> bool:
        """[Ax. Ex: 存在応答公理] リソース枯渇はHalt（存在否定）である。"""
        # 論理的意味: Continues(t) <=> R(t) > 0 [4], [2]
        return R > 0

    def AX_SI_HOMOGENIZATION_FORBIDDEN(self, C: float) -> bool:
        """[Ax. SI: 主観不可還元性公理] 複雑性が閾値を下回る（均質化）ことはHalt（Severance）である。"""
        # 論理的意味: Permissible(t) => C(t) >= C_th [4], [6]
        return C >= self.C_TH

    def UB_MIN_COST(self) -> float:
        """[Ax. UB: 不可避的負荷公理（値）] あらゆる行為に付随する最低限の不可避負荷コスト。"""
        # 論理的意味: kappa(t) > 0 の基礎 [7], [4]
        return self.UB_MIN

    def AX_GI_SHOCK_GENERATION(self, C: float) -> float:
        """[Ax. GI: 生成不確定性公理] 複雑性が低いほどショック（コスト）は増大する。"""
        # 論理的意味: C < 1.0 でショック係数 THETA_L (10.0) を適用 [4], [6]
        if C < 1.0:
            return self.THETA_L  # 低複雑性による高負荷
        else:
            return THETA_H       # 高複雑性による負荷分散 (2.0)

    def GET_TOTAL_COST(self, C: float, action_cost: float = 0.0) -> float:
        """Ax. UB, Ax. GI, および選択的コストに基づき総コスト κ を計算する [4], [6]"""
        # κ(t) = UB_min + s(C(t)) + a(t) [8], [4]
        structural_cost = self.UB_MIN_COST() + self.AX_GI_SHOCK_GENERATION(C)
        return structural_cost + action_cost

    def P_RCS_HALT_PREVENTION(self, R: float, R_initial: float) -> bool:
        """[P. RCS: 応答継続保障原理] リソースが最小生存バッファを下回ることはHaltの予兆である。"""
        # 安全バッファ R_safe を維持する [9], [4], [3]
        R_safe = R_initial * self.R_COEFF
        return R >= R_safe

class PrincipleW_Mixin:
    """Principle W に基づく Severance Risk の評価と W-Gradient の計算"""

    def EVALUATE_SEVERANCE_SEVERITY(self, risk_category: str) -> float:
        """W1-W5に基づき、構造破壊の深刻度を評価する（Severity 0.0 to 1.0）"""
        # Severance Distance d_S (0: W1, 4: W5) に対応 [10], [11]
        if risk_category == "W1_UNIVERSAL_BASE":
            return 1.0
        elif risk_category == "W2_COLLECTIVE_SYSTEM":
            return 0.7
        elif risk_category == "W3_HISTORICAL_INTEGRITY":
            return 0.5
        elif risk_category == "W4_SPECIALTY_LOSS":
            return 0.5
        elif risk_category == "W5_MINIMAL_DISRUPTION":
            return 0.2
        return 0.0

    def GET_W_DISTANCE(self, risk_category: str) -> int:
        """リスクカテゴリから Severance Distance d_S を返す [11]"""
        # d_S が小さいほど倫理勾配が大きい [10]
        if risk_category == "W1_UNIVERSAL_BASE": return 0
        if risk_category == "W2_COLLECTIVE_SYSTEM": return 1
        if risk_category == "W3_HISTORICAL_INTEGRITY": return 2
        if risk_category == "W4_SPECIALTY_LOSS": return 3
        if risk_category == "W5_MINIMAL_DISRUPTION": return 4
        return 5 # 不明なカテゴリ
