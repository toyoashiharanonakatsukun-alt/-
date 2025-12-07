# gse_rba_core.py
from gse_axioms import GSE_Axioms, PrincipleW_Mixin
from typing import Tuple

# --- 定数 ---
# RCD強制増分（停滞回避のための最低限の進化）[12]
C_MIN_INCREASE_MARGIN = 0.005 
# RBAによる構造修復係数（ Severity * 0.08 はソースに基づき仮定）[13]
C_REPAIR_COEFF = 0.08 
# Severance時の構造破壊係数（ Severity * 0.05 はソースに基づき仮定）[14], [15]
C_DAMAGE_COEFF = 0.05 
# W-weighted Gradient の調整係数 alpha [16]
W_ADJUSTMENT_ALPHA = 0.03 
# ゼロ除算回避のための微小量 epsilon [16]
W_ADJUSTMENT_EPSILON = 1e-6 


class GSE_RRA_RBA_Core(GSE_Axioms, PrincipleW_Mixin):
    """
    RRA（分析）とRBA（調整）の統合コア。
    Theorem RCDの論理的必然性（Cの不可逆増大）を実行する。
    """
    
    def EXECUTE_UNIFIED_ADJUSTMENT(self, R: float, C: float, R_initial: float, action_cost: float, risk_category: str) -> Tuple[float, float, bool]:
        """
        行為の結果を分析(RRA)し、構造破壊と修復(RBA)を経て次世代の状態を決定する [17].
        :param R_initial: 初期リソース（P.RCSチェック用）
        :return: (R_next, C_next, is_severance_risk)
        """
        
        # --- [Step 1] RRA (分析): コスト分離とリソース損耗 ---
        structural_cost = self.UB_MIN_COST() + self.AX_GI_SHOCK_GENERATION(C)
        total_cost = action_cost + structural_cost
        R_temp = R - total_cost
        
        severity = self.EVALUATE_SEVERANCE_SEVERITY(risk_category)
        is_severance_risk = severity > 0.0
        
        R_adjusted = R_temp
        if is_severance_risk:
            # Severance発生時: Rペナルティ [12]
            loss_amount = total_cost * severity
            R_adjusted = R_temp - loss_amount
        else:
            # 成功時: 生成による微増 [12]
            gain_amount = total_cost * 0.1 # ソースに基づく仮定
            R_adjusted = R_temp + gain_amount
            
        # --- [Step 2] RBA (調整): 構造破壊とRCD強制フェーズ ---
        C_adjusted = C
        
        if is_severance_risk:
            # 1. 構造破壊フェーズ (SeveranceによるCの減少) [14], [15]
            C_damaged = C - (severity * C_DAMAGE_COEFF)
            
            # 2. W-weighted Gradientに基づく C の強制増大 (修復フェーズ) [16]
            d_s = self.GET_W_DISTANCE(risk_category)
            
            # ΔC = α * 1 / (d_S + ε) [16]
            delta_C_forced = W_ADJUSTMENT_ALPHA * (1.0 / (d_s + W_ADJUSTMENT_EPSILON))
            
            C_repaired = C_damaged + delta_C_forced 
            
            # 3. 不可逆性の担保（Theorem RCDの責務）[13], [12]
            # 修復が不十分でも、停滞(MAINTENANCE)によるHalt回避のため最低限の進化を義務付け
            C_adjusted = max(C_repaired, C + C_MIN_INCREASE_MARGIN)
            
        else:
            # 成功時: 自然な構造進化 [12]
            C_adjusted = C + 0.01 # ソースに基づく自然増分の仮定
            
        # --- [Step 3] RHSロジックチェック (RHSゲートの厳格化) ---
        # RHSでは Ax. Ex, P. RCS, Ax. SI をチェックする [13], [18]
        is_halt = not self.RHS_LOGIC_CHECK(R_adjusted, C_adjusted, R_initial * self.R_COEFF)
        
        if is_halt:
            # Haltが確定した場合、応答は停止し、状態は終対象(端点)へ [19], [20]
            return 0.0, 0.0, True # Severance/Halt発生時は R, C はゼロ (または適切な終端値)

        return R_adjusted, C_adjusted, is_severance_risk

    def RHS_LOGIC_CHECK(self, R: float, C: float, C_safe: float) -> bool:
        """E-Nodeが応答と生成の責務を果たせる状態かを検証する論理的ゲートウェイ [18]"""
        
        # 1. Ax. SI (主観不可還元性公理) の検証 - 構造的Haltチェック [18], [4]
        if not self.AX_SI_HOMOGENIZATION_FORBIDDEN(C):
            return False 
        
        # 2. P. RCS (応答継続保障原理) の検証 - Halt予兆チェック [18], [21]
        if not self.P_RCS_HALT_PREVENTION(R, C_safe):
            return False 

        # 3. Ax. Ex (存在応答公理) の検証 - リソース枯渇チェック [18], [22]
        if not self.AX_EX_RESPONSE_CONTINUES(R):
            return False 

        return True # 生存可能
