"""
Professional Pipeline Architecture Diagram Generator
For 3D Segmentation and Modeling of Lower Limb Bones Project
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

def create_pipeline_diagram():
    # Set up the figure with high DPI for crisp output
    fig, ax = plt.subplots(figsize=(14, 18), dpi=150)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 18)
    ax.axis('off')
    
    # Professional color palette (medical/scientific theme)
    colors = {
        'input': '#1E3A5F',        # Deep navy blue
        'preprocessing': '#2E6B8A', # Teal blue
        'preparation': '#3D8B7A',   # Sea green
        'planning': '#4CAF50',      # Fresh green
        'training': '#FF7043',      # Coral orange
        'inference': '#7E57C2',     # Purple
        'output': '#C62828',        # Deep red
        'arrow': '#37474F',         # Dark gray
        'text_light': '#FFFFFF',    # White
        'text_dark': '#212121',     # Dark gray
        'subtitle': '#78909C',      # Blue gray
        'border': '#263238',        # Dark border
    }
    
    # Box dimensions
    box_width = 10
    box_height = 1.6
    x_center = 7
    x_left = x_center - box_width/2
    
    # Y positions for each box (from top to bottom)
    y_positions = [15.5, 13.0, 10.5, 8.0, 5.5, 3.0, 0.5]
    
    # Pipeline stages data
    stages = [
        {
            'title': 'Raw CT Data (NRRD)',
            'subtitle': 'Input Medical Images',
            'icon': '📁',
            'color': colors['input'],
            'details': 'CT scans • NRRD format • Multi-patient dataset'
        },
        {
            'title': 'Data Extraction & Format Conversion',
            'subtitle': 'NRRD → NIfTI Transformation',
            'icon': '🔄',
            'color': colors['preprocessing'],
            'details': 'Label extraction • Format standardization • Data validation'
        },
        {
            'title': 'Dataset Preparation (nnU-Net Format)',
            'subtitle': 'Structured Data Organization',
            'icon': '📊',
            'color': colors['preparation'],
            'details': 'Standardization • 5-fold split • Metadata generation'
        },
        {
            'title': 'Preprocessing & Planning',
            'subtitle': 'Data Analysis Pipeline',
            'icon': '⚙️',
            'color': colors['planning'],
            'details': 'Intensity analysis • Normalization • Fold creation'
        },
        {
            'title': 'Deep Learning Model Training',
            'subtitle': 'nnU-Net v2 Architecture',
            'icon': '🧠',
            'color': colors['training'],
            'details': '3D U-Net • 5-fold cross-validation • GPU acceleration'
        },
        {
            'title': 'Inference & Validation',
            'subtitle': 'Model Evaluation',
            'icon': '📈',
            'color': colors['inference'],
            'details': 'Predictions • Dice score • Metrics computation'
        },
        {
            'title': '3D Segmentation Output',
            'subtitle': 'Final Results',
            'icon': '🎯',
            'color': colors['output'],
            'details': 'Medical-grade masks • Bone segmentation • Clinical validation'
        }
    ]
    
    # Draw boxes and content
    for i, (y, stage) in enumerate(zip(y_positions, stages)):
        # Main box with rounded corners and shadow effect
        # Shadow
        shadow = FancyBboxPatch(
            (x_left + 0.1, y - 0.1), box_width, box_height,
            boxstyle="round,pad=0.05,rounding_size=0.3",
            facecolor='#00000020',
            edgecolor='none',
            zorder=1
        )
        ax.add_patch(shadow)
        
        # Main box
        box = FancyBboxPatch(
            (x_left, y), box_width, box_height,
            boxstyle="round,pad=0.05,rounding_size=0.3",
            facecolor=stage['color'],
            edgecolor=colors['border'],
            linewidth=2,
            zorder=2
        )
        ax.add_patch(box)
        
        # Gradient overlay effect (lighter strip at top)
        gradient_box = FancyBboxPatch(
            (x_left + 0.1, y + box_height - 0.4), box_width - 0.2, 0.3,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            facecolor='#FFFFFF15',
            edgecolor='none',
            zorder=3
        )
        ax.add_patch(gradient_box)
        
        # Step number badge
        badge_x = x_left + 0.5
        badge_y = y + box_height/2
        badge = plt.Circle((badge_x, badge_y), 0.35, 
                          facecolor='#FFFFFF', 
                          edgecolor=stage['color'],
                          linewidth=2,
                          zorder=4)
        ax.add_patch(badge)
        ax.text(badge_x, badge_y, str(i + 1), 
               fontsize=14, fontweight='bold',
               color=stage['color'],
               ha='center', va='center', zorder=5)
        
        # Title text
        ax.text(x_center + 0.3, y + box_height - 0.45, stage['title'],
               fontsize=13, fontweight='bold',
               color=colors['text_light'],
               ha='center', va='center', zorder=5)
        
        # Subtitle text
        ax.text(x_center + 0.3, y + box_height/2, stage['subtitle'],
               fontsize=10, fontstyle='italic',
               color='#E0E0E0',
               ha='center', va='center', zorder=5)
        
        # Details text
        ax.text(x_center + 0.3, y + 0.35, stage['details'],
               fontsize=8,
               color='#B0BEC5',
               ha='center', va='center', zorder=5)
    
    # Draw arrows between boxes
    arrow_style = "Simple, tail_width=8, head_width=20, head_length=12"
    
    for i in range(len(y_positions) - 1):
        y_start = y_positions[i]
        y_end = y_positions[i + 1] + box_height
        
        # Arrow
        arrow = FancyArrowPatch(
            (x_center, y_start - 0.05),
            (x_center, y_end + 0.15),
            arrowstyle=arrow_style,
            color=colors['arrow'],
            mutation_scale=0.8,
            zorder=1,
            alpha=0.8
        )
        ax.add_patch(arrow)
        
        # Decorative dots on arrow
        mid_y = (y_start + y_end + box_height) / 2
        for offset in [-0.15, 0, 0.15]:
            dot = plt.Circle((x_center, mid_y + offset), 0.05,
                           facecolor=colors['arrow'],
                           edgecolor='none',
                           zorder=2,
                           alpha=0.5)
            ax.add_patch(dot)
    
    # Title
    ax.text(x_center, 17.5, '3D Segmentation Pipeline Architecture',
           fontsize=20, fontweight='bold',
           color=colors['text_dark'],
           ha='center', va='center')
    
    ax.text(x_center, 17.0, 'Lower Limb Bone Segmentation using Deep Learning',
           fontsize=12,
           color=colors['subtitle'],
           ha='center', va='center',
           fontstyle='italic')
    
    # Decorative line under title
    ax.plot([x_center - 4, x_center + 4], [16.7, 16.7], 
           color=colors['training'], linewidth=3, alpha=0.7)
    ax.plot([x_center - 3, x_center + 3], [16.6, 16.6], 
           color=colors['training'], linewidth=1, alpha=0.4)
    
    # Side annotations for key technologies
    annotations = [
        (15.5, 'NRRD Files'),
        (13.0, 'NIfTI (.nii.gz)'),
        (10.5, 'nnU-Net v2'),
        (8.0, 'Fingerprint'),
        (5.5, '3D U-Net'),
        (3.0, 'Dice Score'),
        (0.5, 'NIfTI Masks'),
    ]
    
    for y, text in annotations:
        # Right side annotation
        ax.annotate(text,
                   xy=(x_left + box_width + 0.3, y + box_height/2),
                   fontsize=8,
                   color='#607D8B',
                   ha='left',
                   va='center',
                   bbox=dict(boxstyle='round,pad=0.3',
                           facecolor='#ECEFF1',
                           edgecolor='#B0BEC5',
                           alpha=0.8))
    
    # Footer
    ax.text(x_center, -0.8, 
           'Medical Image Segmentation • nnU-Net Framework • Deep Learning',
           fontsize=9,
           color='#90A4AE',
           ha='center', va='center')
    
    plt.tight_layout()
    
    # Save in multiple formats
    plt.savefig('pipeline_architecture.png', 
               dpi=300, 
               bbox_inches='tight',
               facecolor='white',
               edgecolor='none',
               pad_inches=0.5)
    
    plt.savefig('pipeline_architecture.pdf', 
               bbox_inches='tight',
               facecolor='white',
               edgecolor='none',
               pad_inches=0.5)
    
    plt.savefig('pipeline_architecture.svg', 
               bbox_inches='tight',
               facecolor='white',
               edgecolor='none',
               pad_inches=0.5)
    
    print("✅ Pipeline diagram generated successfully!")
    print("📄 Saved files:")
    print("   • pipeline_architecture.png (300 DPI - for presentations)")
    print("   • pipeline_architecture.pdf (vector - for printing)")
    print("   • pipeline_architecture.svg (vector - for editing)")
    
    plt.show()

if __name__ == "__main__":
    create_pipeline_diagram()
