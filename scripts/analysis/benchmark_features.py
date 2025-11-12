"""
Benchmark script: Compare baseline vs advanced features performance.

Usage:
    python scripts/analysis/benchmark_features.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger

from src.core.config import settings


def load_metrics(model_name: str) -> dict:
    """Load metrics from JSON file."""
    metrics_path = settings.models_path / f"{model_name}.json"
    
    if not metrics_path.exists():
        logger.warning(f"Metrics not found: {metrics_path}")
        return {}
    
    with open(metrics_path) as f:
        return json.load(f)


def create_comparison_plot():
    """Create visual comparison of model performance."""
    
    # Metrics data (manually entered from training outputs)
    data = {
        "Model": [
            "Baseline\n(384 emb)",
            "Baseline\n(427 adv)",
            "Ensemble\n(397 emb)",
            "Ensemble\n(427 adv)"
        ],
        "AUC": [0.86, 0.855, 0.855, 0.855],
        "Precision": [0.889, 0.889, 0.889, 0.875],
        "Recall": [0.80, 0.80, 0.80, 0.70],
        "Features": [384, 427, 397, 427]
    }
    
    df = pd.DataFrame(data)
    
    # Create comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Model Performance Comparison: Baseline vs Advanced Features", 
                 fontsize=16, fontweight='bold')
    
    # 1. AUC comparison
    ax1 = axes[0, 0]
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    bars = ax1.bar(df["Model"], df["AUC"], color=colors, alpha=0.8)
    ax1.set_ylabel("AUC Score", fontsize=12)
    ax1.set_title("AUC Performance", fontsize=14, fontweight='bold')
    ax1.set_ylim([0.7, 0.9])
    ax1.axhline(y=0.86, color='red', linestyle='--', label='Target (0.86)')
    ax1.legend()
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 2. Precision vs Recall
    ax2 = axes[0, 1]
    x = range(len(df))
    width = 0.35
    ax2.bar([i - width/2 for i in x], df["Precision"], width, label='Precision', alpha=0.8, color='#3498db')
    ax2.bar([i + width/2 for i in x], df["Recall"], width, label='Recall', alpha=0.8, color='#e74c3c')
    ax2.set_ylabel("Score", fontsize=12)
    ax2.set_title("Precision & Recall", fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["Model"])
    ax2.legend()
    ax2.set_ylim([0.6, 1.0])
    
    # 3. Feature count
    ax3 = axes[1, 0]
    bars = ax3.bar(df["Model"], df["Features"], color=colors, alpha=0.8)
    ax3.set_ylabel("Number of Features", fontsize=12)
    ax3.set_title("Feature Count", fontsize=14, fontweight='bold')
    
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 4. F1 Score (harmonic mean of precision and recall)
    ax4 = axes[1, 1]
    f1_scores = 2 * (df["Precision"] * df["Recall"]) / (df["Precision"] + df["Recall"])
    bars = ax4.bar(df["Model"], f1_scores, color=colors, alpha=0.8)
    ax4.set_ylabel("F1 Score", fontsize=12)
    ax4.set_title("F1 Score (Precision-Recall Balance)", fontsize=14, fontweight='bold')
    ax4.set_ylim([0.7, 0.9])
    
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    # Save plot
    output_path = settings.models_path / "performance_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Comparison plot saved: {output_path}")
    
    return df, f1_scores


def print_summary_table(df: pd.DataFrame, f1_scores: pd.Series):
    """Print formatted summary table."""
    
    df_summary = df.copy()
    df_summary["F1 Score"] = f1_scores
    
    print("\n" + "="*80)
    print("📊 MODEL PERFORMANCE SUMMARY")
    print("="*80)
    print(df_summary.to_string(index=False))
    print("="*80)
    
    # Analysis
    print("\n🔍 ANALYSIS:")
    print(f"  • Best AUC: {df['AUC'].max():.3f} (Baseline 384 embeddings)")
    print(f"  • Best Precision: {df['Precision'].max():.3f} (Baseline models)")
    print(f"  • Best Recall: {df['Recall'].max():.3f} (Baseline + Ensemble 397)")
    print(f"  • Best F1: {f1_scores.max():.3f} (Baseline 384 embeddings)")
    
    print("\n💡 INSIGHTS:")
    print("  1. Advanced features (427) did NOT improve AUC (0.855 vs 0.86)")
    print("  2. Embeddings alone (384-397) are highly informative")
    print("  3. Adding 43 engineered features reduced recall (0.80 → 0.70)")
    print("  4. Possible overfitting: too many features (427) for 100 samples")
    
    print("\n🎯 RECOMMENDATIONS:")
    print("  1. Use baseline model with 384 embeddings (AUC 0.86)")
    print("  2. Collect more data (1000+ samples) before using advanced features")
    print("  3. Focus on real labels (not synthetic) for AUC 0.90+ target")
    print("  4. Consider feature selection (remove low-importance features)")
    print("="*80)


def main():
    """Main benchmark function."""
    
    logger.info("Starting performance benchmark...")
    
    # Create comparison plot
    df, f1_scores = create_comparison_plot()
    
    # Print summary
    print_summary_table(df, f1_scores)
    
    # Feature breakdown
    print("\n📈 FEATURE BREAKDOWN:")
    print("  Baseline (384): 384 embeddings only")
    print("  Baseline (427): 397 embeddings + 30 advanced")
    print("    └─ Advanced: temporal (16) + clustering (4) + reduction (10) + statistical (11)")
    print("  Ensemble (397): 397 embeddings only")
    print("  Ensemble (427): 397 embeddings + 30 advanced")
    
    print("\n✅ Benchmark complete!")


if __name__ == "__main__":
    main()
