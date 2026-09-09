import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score

def evaluate_predictions(y_true: np.ndarray, y_prob: np.ndarray, groups: np.ndarray) -> Dict[str, float]:
    """
    Evaluates predictions containing binary labels and probabilities.
    Includes classification metrics and ranking metrics grouped by case.
    """
    y_pred = (y_prob >= 0.5).astype(int)
    
    # Classification metrics
    try:
        roc_auc = roc_auc_score(y_true, y_prob)
        pr_auc = average_precision_score(y_true, y_prob)
    except ValueError:
        roc_auc = 0.5
        pr_auc = 0.0
        
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # Ranking metrics (Top-K and MRR)
    df = pd.DataFrame({
        "y_true": y_true,
        "y_prob": y_prob,
        "group": groups
    })
    
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    mrr_sum = 0.0
    group_count = df["group"].nunique()
    
    for _, group_df in df.groupby("group"):
        # Sort candidates for this case by predicted probability descending
        ranked = group_df.sort_values(by="y_prob", ascending=False).reset_index(drop=True)
        
        # Find rank of the true target
        true_ranks = ranked[ranked["y_true"] == 1].index.tolist()
        
        if true_ranks:
            best_rank = true_ranks[0] + 1  # 1-indexed rank
            if best_rank == 1:
                hits_at_1 += 1
            if best_rank <= 3:
                hits_at_3 += 1
            if best_rank <= 5:
                hits_at_5 += 1
            
            mrr_sum += 1.0 / best_rank
            
    top_1_hit_rate = hits_at_1 / group_count if group_count > 0 else 0.0
    top_3_hit_rate = hits_at_3 / group_count if group_count > 0 else 0.0
    top_5_hit_rate = hits_at_5 / group_count if group_count > 0 else 0.0
    mrr = mrr_sum / group_count if group_count > 0 else 0.0
    
    return {
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "top_1_hit_rate": float(top_1_hit_rate),
        "top_3_hit_rate": float(top_3_hit_rate),
        "top_5_hit_rate": float(top_5_hit_rate),
        "mrr": float(mrr)
    }
