"""
Business Metrics Visualization

Creates visual charts and graphs from business reports for presentations and dashboards.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json

from utils.config import OUTPUT_DIR
from utils.logger import log_info


class BusinessMetricsVisualizer:
    """Create visualizations from business metrics reports."""
    
    def __init__(self, reports_dir: str = None):
        """Initialize visualizer with reports directory."""
        self.reports_dir = Path(reports_dir) if reports_dir else Path(OUTPUT_DIR) / "business_reports"
        self.viz_dir = self.reports_dir / "visualizations"
        self.viz_dir.mkdir(exist_ok=True)
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 6)
    
    def generate_all_visualizations(self):
        """Generate all business metric visualizations."""
        log_info("Generating business metrics visualizations...")
        
        # 1. Trigger timeline
        self._plot_trigger_timeline()
        
        # 2. Financial impact by year
        self._plot_financial_impact()
        
        # 3. Alert type distribution
        self._plot_alert_distribution()
        
        # 4. Risk heatmap
        self._plot_risk_heatmap()
        
        log_info(f"✓ Visualizations saved to: {self.viz_dir}")
    
    def _plot_trigger_timeline(self):
        """Plot trigger events over time."""
        triggers_file = self.reports_dir / "insurance_triggers_detailed.csv"
        if not triggers_file.exists():
            return
        
        df = pd.read_csv(triggers_file)
        df['date'] = pd.to_datetime(df['date'])
        
        # Count triggers by month
        monthly_triggers = df.groupby([df['date'].dt.to_period('M'), 'trigger_type']).size().unstack(fill_value=0)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        monthly_triggers.plot(kind='bar', stacked=True, ax=ax, colormap='Set3')
        
        ax.set_title('Insurance Trigger Events Timeline', fontsize=16, fontweight='bold')
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Number of Triggers', fontsize=12)
        ax.legend(title='Trigger Type', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(axis='y', alpha=0.3)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(self.viz_dir / 'trigger_timeline.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        log_info("   ✓ Created: trigger_timeline.png")
    
    def _plot_financial_impact(self):
        """Plot financial impact by year."""
        payout_file = self.reports_dir / "payout_summary_by_year.csv"
        if not payout_file.exists():
            return
        
        df = pd.read_csv(payout_file)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Payouts by year
        ax1.bar(df['year'], df['estimated_payout_usd'], color='steelblue', alpha=0.7)
        ax1.set_title('Estimated Insurance Payouts by Year', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Year', fontsize=12)
        ax1.set_ylabel('Total Payout (USD)', fontsize=12)
        ax1.grid(axis='y', alpha=0.3)
        
        # Format y-axis as currency
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Events by year
        ax2.bar(df['year'], df['total_events'], color='coral', alpha=0.7)
        ax2.set_title('Trigger Events by Year', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Year', fontsize=12)
        ax2.set_ylabel('Number of Events', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.viz_dir / 'financial_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        log_info("   ✓ Created: financial_impact.png")
    
    def _plot_alert_distribution(self):
        """Plot distribution of alert types."""
        alerts_file = self.reports_dir / "alert_timeline.csv"
        if not alerts_file.exists():
            return
        
        df = pd.read_csv(alerts_file)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Alert type counts
        alert_counts = df['alert_type'].value_counts()
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
        ax1.pie(alert_counts.values, labels=alert_counts.index, autopct='%1.1f%%',
                colors=colors, startangle=90)
        ax1.set_title('Alert Type Distribution', fontsize=14, fontweight='bold')
        
        # Severity distribution
        severity_counts = df['severity'].value_counts()
        ax2.bar(severity_counts.index, severity_counts.values, 
                color=['green', 'orange', 'red'], alpha=0.7)
        ax2.set_title('Alert Severity Distribution', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Severity Level', fontsize=12)
        ax2.set_ylabel('Count', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.viz_dir / 'alert_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        log_info("   ✓ Created: alert_distribution.png")
    
    def _plot_risk_heatmap(self):
        """Plot risk heatmap by month and year."""
        triggers_file = self.reports_dir / "insurance_triggers_detailed.csv"
        if not triggers_file.exists():
            return
        
        df = pd.read_csv(triggers_file)
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        
        # Create pivot table
        risk_matrix = df.groupby(['year', 'month']).size().unstack(fill_value=0)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        sns.heatmap(risk_matrix, annot=True, fmt='d', cmap='YlOrRd', 
                    cbar_kws={'label': 'Number of Triggers'}, ax=ax)
        
        ax.set_title('Risk Heatmap: Trigger Events by Month and Year', 
                     fontsize=16, fontweight='bold')
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Year', fontsize=12)
        
        # Set month labels
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_xticklabels(month_labels[:len(risk_matrix.columns)])
        
        plt.tight_layout()
        plt.savefig(self.viz_dir / 'risk_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        log_info("   ✓ Created: risk_heatmap.png")


def main():
    """Generate all visualizations."""
    visualizer = BusinessMetricsVisualizer()
    visualizer.generate_all_visualizations()
    print(f"\n✓ Visualizations saved to: {visualizer.viz_dir}\n")


if __name__ == "__main__":
    main()
