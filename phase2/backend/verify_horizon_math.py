"""
Verify the mathematical behavior of horizon adjustment
"""

def calculate_adjusted_probability(base_prob, horizon_months):
    """
    Simulate the new horizon adjustment logic
    """
    # Apply horizon decay factor
    horizon_decay = 0.85 ** (horizon_months - 3)
    mean_probability = 0.35
    
    # Blend base probability with mean based on horizon
    adjusted_prob = base_prob * horizon_decay + mean_probability * (1 - horizon_decay)
    
    return adjusted_prob

def calculate_confidence_interval(probability, horizon_months, has_model=False):
    """
    Simulate the new confidence interval logic
    """
    base_uncertainty = 0.15 if has_model else 0.25
    horizon_uncertainty = base_uncertainty + (0.02 * (horizon_months - 3))
    
    lower = max(0.0, probability - horizon_uncertainty)
    upper = min(1.0, probability + horizon_uncertainty)
    
    return lower, upper

# Test with example scenarios
print("=" * 70)
print("HORIZON ADJUSTMENT VERIFICATION")
print("=" * 70)

scenarios = [
    ("High drought risk (base 70%)", 0.70),
    ("Moderate flood risk (base 50%)", 0.50),
    ("Low crop failure risk (base 30%)", 0.30),
]

for scenario_name, base_prob in scenarios:
    print(f"\n{scenario_name}")
    print("-" * 70)
    print(f"{'Horizon':<10} {'Probability':<15} {'Confidence Interval':<30} {'Change'}")
    print("-" * 70)
    
    prev_prob = None
    for horizon in [3, 4, 5, 6]:
        adj_prob = calculate_adjusted_probability(base_prob, horizon)
        lower, upper = calculate_confidence_interval(adj_prob, horizon, has_model=False)
        
        change = ""
        if prev_prob is not None:
            diff = adj_prob - prev_prob
            change = f"{diff:+.1%}"
        
        print(f"{horizon} months  {adj_prob:>6.1%}         "
              f"[{lower:.1%}, {upper:.1%}]              {change}")
        
        prev_prob = adj_prob

print("\n" + "=" * 70)
print("KEY OBSERVATIONS:")
print("=" * 70)
print("1. Probabilities now DIFFER by horizon (not identical)")
print("2. Longer horizons regress toward mean (~35%)")
print("3. Confidence intervals WIDEN with longer horizons")
print("4. This reflects increasing uncertainty over time")
print("=" * 70)
