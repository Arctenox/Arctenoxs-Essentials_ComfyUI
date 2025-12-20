"""
Arctenox Essentials - Artifact Risk Predictor
==============================================

Analyzes latent space to predict potential artifacts before decoding.
Provides informational risk scores and warnings for decision-making.

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import torch
import numpy as np


class ArtifactRiskPredictor:
    """
    Analyzes latent space for potential artifacts before decoding.
    Provides risk scores and warnings - informational only, does not stop workflow.
    Use with other nodes (like switches/routers) to build self-correcting workflows.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent": ("LATENT",),
                "steps_taken": ("INT", {
                    "default": 25,
                    "min": 1,
                    "max": 10000,
                    "tooltip": "Number of sampling steps used"
                }),
                "cfg_used": ("FLOAT", {
                    "default": 7.0,
                    "min": 0.0,
                    "max": 30.0,
                    "step": 0.001,
                    "tooltip": "CFG scale used during generation"
                }),
                "denoise_used": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.001,
                    "tooltip": "Denoise strength used"
                }),
                "risk_threshold": ([
                    "conservative",  # Flag more potential issues
                    "balanced",      # Standard detection
                    "permissive",    # Only flag obvious problems
                ], {
                    "default": "balanced",
                    "tooltip": "Sensitivity of risk detection"
                }),
            },
        }

    RETURN_TYPES = ("LATENT", "FLOAT", "STRING", "STRING")
    RETURN_NAMES = ("latent_passthrough", "risk_score", "risk_report", "warnings")
    FUNCTION = "predict_artifacts"
    CATEGORY = "Arctenox Essentials/Utilities"
    
    DESCRIPTION = """
    🔍 Artifact Risk Predictor - Analyze Quality Before Decoding
    
    Analyzes latent space for signs of common generation artifacts:
    • Overbaked faces (too many steps/high CFG)
    • Melted hands (high-frequency noise patterns)
    • Flat contrast (collapsed dynamic range)
    • Noisy/grainy results (sampling artifacts)
    • Oversaturated regions (CFG overshoot)
    
    ⚡ What This Node Does:
    Provides INFORMATIONAL risk assessment - does not stop or control workflow.
    Use the risk_score output with switches, routers, or conditional nodes 
    to build self-correcting workflows that can retry or adjust parameters.
    
    🎯 Risk Score Output:
    • 0.0-0.2: ✅ Low risk - probably good
    • 0.2-0.4: ⚠️ Mild risk - watch for issues
    • 0.4-0.6: 🟡 Moderate risk - likely problems
    • 0.6-0.8: 🟠 High risk - expect artifacts
    • 0.8-1.0: 🔴 Critical risk - probably unusable
    
    💡 Example Use Cases:
    • Pass risk_score to a switch node to conditionally decode
    • Log warnings for quality monitoring in batch generation
    • Use with retry nodes to regenerate high-risk latents
    • Build adaptive workflows that adjust CFG based on risk
    
    🔧 Detection Methods:
    • Latent statistics (mean, std, range)
    • Frequency analysis (detect noise patterns)
    • Dynamic range checks (contrast collapse)
    • Parameter correlation (overbaking detection)
    • Channel balance analysis
    
    ⚙️ Risk Thresholds:
    • Conservative: Flag more potential issues (fewer false negatives)
    • Balanced: Standard detection (good default)
    • Permissive: Only flag obvious problems (fewer false positives)
    
    ℹ️ Note: This node analyzes and reports - it does not prevent decoding.
    Combine with other nodes to create conditional/adaptive workflows.
    """

    def _calculate_latent_statistics(self, latent_samples):
        """Calculate statistical properties of latent tensor"""
        # Flatten to analyze overall distribution
        flat = latent_samples.flatten()
        
        stats = {
            "mean": float(torch.mean(flat)),
            "std": float(torch.std(flat)),
            "min": float(torch.min(flat)),
            "max": float(torch.max(flat)),
            "range": float(torch.max(flat) - torch.min(flat)),
        }
        
        # Channel-wise statistics
        channel_means = torch.mean(latent_samples, dim=[0, 2, 3])
        stats["channel_balance"] = float(torch.std(channel_means))
        
        return stats

    def _detect_high_frequency_noise(self, latent_samples):
        """Detect high-frequency noise patterns (indicator of artifacts)"""
        # Calculate gradients in spatial dimensions
        dx = torch.diff(latent_samples, dim=3)
        dy = torch.diff(latent_samples, dim=2)
        
        # High gradient variance = noisy/artifacted
        gradient_variance = float(torch.var(dx)) + float(torch.var(dy))
        
        return gradient_variance

    def _detect_contrast_collapse(self, stats):
        """Detect if contrast has collapsed (flat, lifeless image)"""
        # Low range and low std = flat contrast
        range_score = min(stats["range"] / 6.0, 1.0)  # Expect ~6 range in healthy latents
        std_score = min(stats["std"] / 1.5, 1.0)      # Expect ~1.5 std in healthy latents
        
        # Lower scores = more collapsed
        contrast_health = (range_score + std_score) / 2.0
        collapse_risk = 1.0 - contrast_health
        
        return collapse_risk

    def _detect_overbaking(self, cfg_used, steps_taken, denoise_used):
        """Detect overbaking from parameter combinations"""
        # High CFG + many steps = overbaked risk
        cfg_risk = max(0, (cfg_used - 8.0) / 12.0)  # Risk starts above CFG 8
        step_risk = max(0, (steps_taken - 30) / 70.0)  # Risk starts above 30 steps
        denoise_risk = denoise_used  # Higher denoise = more baking
        
        # Combined overbaking risk
        overbake_risk = (cfg_risk * 0.4 + step_risk * 0.3 + denoise_risk * 0.3)
        
        return min(overbake_risk, 1.0)

    def _detect_oversaturation(self, latent_samples):
        """Detect oversaturated regions (CFG overshoot)"""
        # Check for extreme values
        extreme_threshold = 3.0  # Latents typically stay within ±3
        extreme_ratio = float(torch.sum(torch.abs(latent_samples) > extreme_threshold)) / latent_samples.numel()
        
        return extreme_ratio

    def _detect_channel_imbalance(self, stats):
        """Detect unbalanced channels (can cause color/style issues)"""
        # High channel balance variance = imbalanced
        balance_risk = min(stats["channel_balance"] / 0.5, 1.0)
        
        return balance_risk

    def predict_artifacts(self, latent, steps_taken, cfg_used, denoise_used, risk_threshold):
        """Analyze latent space and predict artifact risks"""
        
        latent_samples = latent["samples"]
        
        # Calculate all risk factors
        stats = self._calculate_latent_statistics(latent_samples)
        noise_score = self._detect_high_frequency_noise(latent_samples)
        contrast_risk = self._detect_contrast_collapse(stats)
        overbake_risk = self._detect_overbaking(cfg_used, steps_taken, denoise_used)
        saturation_risk = self._detect_oversaturation(latent_samples)
        balance_risk = self._detect_channel_imbalance(stats)
        
        # Normalize noise score (typical range 0-0.5)
        noise_risk = min(noise_score / 0.5, 1.0)
        
        # Get threshold multipliers
        threshold_multipliers = {
            "conservative": 0.7,   # Lower threshold = more sensitive
            "balanced": 1.0,       # Standard
            "permissive": 1.3,     # Higher threshold = less sensitive
        }
        multiplier = threshold_multipliers.get(risk_threshold, 1.0)
        
        # Weighted combination of risk factors
        risk_components = {
            "overbaking": overbake_risk * 0.25,
            "contrast_collapse": contrast_risk * 0.20,
            "high_freq_noise": noise_risk * 0.20,
            "oversaturation": saturation_risk * 0.20,
            "channel_imbalance": balance_risk * 0.15,
        }
        
        # Calculate total risk
        total_risk = sum(risk_components.values())
        
        # Apply threshold adjustment
        adjusted_risk = min(total_risk / multiplier, 1.0)
        
        # Generate warnings
        warnings = self._generate_warnings(risk_components, adjusted_risk, multiplier)
        
        # Generate detailed report
        report = self._generate_report(
            adjusted_risk, risk_components, stats,
            steps_taken, cfg_used, denoise_used,
            risk_threshold, warnings
        )
        
        return (latent, adjusted_risk, report, warnings)

    def _generate_warnings(self, risk_components, total_risk, multiplier):
        """Generate warning messages for detected risks"""
        warnings = []
        
        # Adjust component thresholds based on sensitivity
        warning_threshold = 0.3 / multiplier
        
        if risk_components["overbaking"] > warning_threshold:
            warnings.append("⚠️ OVERBAKING: High CFG/steps may cause crispy faces")
        
        if risk_components["contrast_collapse"] > warning_threshold:
            warnings.append("⚠️ FLAT CONTRAST: Image may lack depth/dimension")
        
        if risk_components["high_freq_noise"] > warning_threshold:
            warnings.append("⚠️ NOISY ARTIFACTS: Grainy/artifacted regions likely")
        
        if risk_components["oversaturation"] > warning_threshold:
            warnings.append("⚠️ OVERSATURATION: CFG overshoot detected")
        
        if risk_components["channel_imbalance"] > warning_threshold:
            warnings.append("⚠️ CHANNEL IMBALANCE: Color/style issues possible")
        
        # Overall assessment
        if total_risk >= 0.8:
            warnings.insert(0, "🔴 CRITICAL: Very high artifact risk - consider regenerating")
        elif total_risk >= 0.6:
            warnings.insert(0, "🟠 HIGH RISK: Significant artifacts expected")
        elif total_risk >= 0.4:
            warnings.insert(0, "🟡 MODERATE: Some artifacts likely")
        elif total_risk >= 0.2:
            warnings.insert(0, "⚠️ MILD: Minor issues possible")
        else:
            warnings.insert(0, "✅ LOW RISK: Generation looks healthy")
        
        return "\n".join(warnings) if warnings else "✅ No significant risks detected"

    def _generate_report(self, total_risk, components, stats, steps, cfg, denoise, threshold, warnings):
        """Generate detailed risk analysis report"""
        
        # Risk level indicator
        if total_risk < 0.2:
            risk_badge = "✅ LOW"
            risk_bar = "█" * 2 + "░" * 8
        elif total_risk < 0.4:
            risk_badge = "⚠️ MILD"
            risk_bar = "█" * 4 + "░" * 6
        elif total_risk < 0.6:
            risk_badge = "🟡 MODERATE"
            risk_bar = "█" * 6 + "░" * 4
        elif total_risk < 0.8:
            risk_badge = "🟠 HIGH"
            risk_bar = "█" * 8 + "░" * 2
        else:
            risk_badge = "🔴 CRITICAL"
            risk_bar = "█" * 10
        
        report = f"""
╔═══════════════════════════════════════════════════════╗
          🔍 ARTIFACT RISK ANALYSIS REPORT             
╠═══════════════════════════════════════════════════════╣

  📊 OVERALL RISK SCORE: {total_risk:.3f} ({risk_badge})
      [{risk_bar}] {total_risk*100:.1f}%
      
  🎚️ Threshold: {threshold} sensitivity

╠═══════════════════════════════════════════════════════╣
   RISK BREAKDOWN                                        
╠═══════════════════════════════════════════════════════╣

  🔥 Overbaking Risk:        {components['overbaking']:.3f} [{self._risk_bar(components['overbaking'])}]
     CFG: {cfg:.1f} | Steps: {steps} | Denoise: {denoise:.2f}
  
  📉 Contrast Collapse:      {components['contrast_collapse']:.3f} [{self._risk_bar(components['contrast_collapse'])}]
     Range: {stats['range']:.2f} | Std: {stats['std']:.2f}
  
  📡 High-Freq Noise:        {components['high_freq_noise']:.3f} [{self._risk_bar(components['high_freq_noise'])}]
     Spatial gradient variance detected
  
  💥 Oversaturation:         {components['oversaturation']:.3f} [{self._risk_bar(components['oversaturation'])}]
     Extreme value regions
  
  ⚖️ Channel Imbalance:      {components['channel_imbalance']:.3f} [{self._risk_bar(components['channel_imbalance'])}]
     Balance: {stats['channel_balance']:.3f}

╠═══════════════════════════════════════════════════════╣
   LATENT STATISTICS                                     
╠═══════════════════════════════════════════════════════╣

  Mean:   {stats['mean']:+.3f}
  Std:    {stats['std']:.3f}
  Range:  {stats['range']:.3f} ({stats['min']:.2f} to {stats['max']:.2f})

╠═══════════════════════════════════════════════════════╣
   WARNINGS & RECOMMENDATIONS                            
╠═══════════════════════════════════════════════════════╣

{warnings}

╠═══════════════════════════════════════════════════════╣
   ℹ️ This is informational - use outputs with other nodes
   💡 Connect risk_score to switches for conditional logic
╚═══════════════════════════════════════════════════════╝
"""
        return report

    def _risk_bar(self, value):
        """Generate mini risk bar"""
        filled = int(value * 5)
        return "█" * filled + "░" * (5 - filled)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ArtifactRiskPredictor": ArtifactRiskPredictor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArtifactRiskPredictor": "Artifact Risk Predictor (Arctenox's Essentials)",
}

__all__ = ["ArtifactRiskPredictor"]