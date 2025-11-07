import nrrd # type: ignore
import numpy as np
import os

def extraire_segmentations(fichier_nrrd, dossier_sortie="segmentations_extraites"):
    """
    Extrait les différentes segmentations d'un fichier NRRD et les sauvegarde séparément.
    
    Args:
        fichier_nrrd: Chemin vers le fichier NRRD
        dossier_sortie: Dossier où sauvegarder les segmentations extraites
    """
    
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(dossier_sortie, exist_ok=True)
    
    # Lire le fichier NRRD
    print(f"Lecture du fichier: {fichier_nrrd}")
    data, header = nrrd.read(fichier_nrrd)
    
    print(f"Dimensions des données: {data.shape}")
    print(f"Type de données: {data.dtype}")
    
    # Extraire les informations des segments depuis le header
    segments_info = {}
    segment_idx = 0
    
    while f'Segment{segment_idx}_Name' in header:
        segment_info = {
            'name': header.get(f'Segment{segment_idx}_Name', f'Segment_{segment_idx}'),
            'label_value': int(header.get(f'Segment{segment_idx}_LabelValue', segment_idx + 1)),
            'color': header.get(f'Segment{segment_idx}_Color', 'N/A'),
            'id': header.get(f'Segment{segment_idx}_ID', f'Segment_{segment_idx}'),
            'extent': header.get(f'Segment{segment_idx}_Extent', 'N/A')
        }
        segments_info[segment_idx] = segment_info
        segment_idx += 1
    
    print(f"\n{len(segments_info)} segments trouvés:")
    print("-" * 60)
    
    # Afficher les informations des segments
    for idx, info in segments_info.items():
        print(f"Segment {idx}: {info['name']}")
        print(f"  Label value: {info['label_value']}")
        print(f"  Couleur RGB: {info['color']}")
        print(f"  ID: {info['id']}")
        print(f"  Extent: {info['extent']}")
        print()
    
    # Extraire et sauvegarder chaque segmentation
    print("\nExtraction des segmentations individuelles...")
    print("-" * 60)
    
    for idx, info in segments_info.items():
        label_value = info['label_value']
        segment_name = info['name']
        
        # Créer un masque binaire pour ce segment
        segment_mask = (data == label_value).astype(np.uint8)
        
        # Compter le nombre de voxels
        num_voxels = np.sum(segment_mask)
        
        print(f"Segment: {segment_name} (Label {label_value})")
        print(f"  Voxels: {num_voxels}")
        
        if num_voxels > 0:
            # Créer un nouveau header pour ce segment
            segment_header = header.copy()
            
            # Nettoyer le header des informations des autres segments
            keys_to_remove = [k for k in segment_header.keys() if k.startswith('Segment')]
            for key in keys_to_remove:
                del segment_header[key]
            
            # Sauvegarder le segment
            nom_fichier = f"{segment_name}_label{label_value}.nrrd"
            chemin_sortie = os.path.join(dossier_sortie, nom_fichier)
            
            nrrd.write(chemin_sortie, segment_mask, segment_header)
            print(f"  Sauvegardé: {chemin_sortie}")
        else:
            print(f"  ATTENTION: Aucun voxel trouvé pour ce segment!")
        
        print()
    
    # Créer également un fichier résumé
    with open(os.path.join(dossier_sortie, "segments_info.txt"), 'w', encoding='utf-8') as f:
        f.write("RÉSUMÉ DES SEGMENTATIONS\n")
        f.write("=" * 60 + "\n\n")
        
        for idx, info in segments_info.items():
            label_value = info['label_value']
            segment_mask = (data == label_value)
            num_voxels = np.sum(segment_mask)
            
            f.write(f"Segment {idx}: {info['name']}\n")
            f.write(f"  Label value: {label_value}\n")
            f.write(f"  Couleur RGB: {info['color']}\n")
            f.write(f"  ID: {info['id']}\n")
            f.write(f"  Nombre de voxels: {num_voxels}\n")
            f.write(f"  Fichier: {info['name']}_label{label_value}.nrrd\n")
            f.write("\n")
    
    print(f"Résumé sauvegardé: {os.path.join(dossier_sortie, 'segments_info.txt')}")
    print("\nExtraction terminée!")
    
    return segments_info, data, header


# Exemple d'utilisation
if __name__ == "__main__":
    # Remplacer par le chemin de votre fichier NRRD
    fichier_nrrd = "CV Dataset\\002\\002\\SMIR.Lower_limb.078Y.F.CT.9\\SMIR.Lower_limb.078Y.F.CT.9-Pelvis-Thighs_Segmentation.seg.nrrd"
    
    # Extraire les segmentations
    try:
        segments_info, data, header = extraire_segmentations(fichier_nrrd)
        
        # Afficher les labels uniques dans les données
        labels_uniques = np.unique(data)
        print(f"\nLabels uniques trouvés dans les données: {labels_uniques}")
        
        # Afficher la distribution des labels
        print("\nDistribution des labels:")
        for label in labels_uniques:
            count = np.sum(data == label)
            percentage = (count / data.size) * 100
            print(f"  Label {label}: {count} voxels ({percentage:.2f}%)")
            
    except FileNotFoundError:
        print(f"Erreur: Le fichier '{fichier_nrrd}' n'existe pas.")
        print("Veuillez modifier la variable 'fichier_nrrd' avec le bon chemin.")
    except Exception as e:
        print(f"Erreur lors de l'extraction: {str(e)}")