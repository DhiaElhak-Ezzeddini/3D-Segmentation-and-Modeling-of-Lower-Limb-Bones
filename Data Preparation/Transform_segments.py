import os
import nrrd
import nibabel as nib # type: ignore
import numpy as np

def convert_to_nii_gz(dataset_root: str):
    """
    Finds extracted segments and converts them from .nrrd to .nii.gz format.
    """
    print("\n--- STARTING NII.GZ CONVERSION ---")
    conversion_count = 0
    errors = []

    for dirpath, dirnames, filenames in os.walk(dataset_root):
        if not dirpath.endswith("_Extracted_Segs"):
            continue

        # Create the corresponding "Transformed" directory
        transformed_folder = dirpath.replace("_Extracted_Segs", "_Segs_Transformed")
        os.makedirs(transformed_folder, exist_ok=True)
        print(f"\nFound extracted segments in: {dirpath}")
        print(f"Outputting to: {transformed_folder}")

        # Find all .nrrd files in the subdirectories
        for sub_dirpath, _, seg_filenames in os.walk(dirpath):
            for seg_filename in seg_filenames:
                if not seg_filename.endswith(".nrrd"):
                    continue

                nrrd_path = os.path.join(sub_dirpath, seg_filename)
                
                # Create corresponding sub-structure in transformed folder
                relative_path = os.path.relpath(sub_dirpath, dirpath)
                output_subfolder = os.path.join(transformed_folder, relative_path)
                os.makedirs(output_subfolder, exist_ok=True)

                output_filename = os.path.splitext(seg_filename)[0] + ".nii.gz"
                output_path = os.path.join(output_subfolder, output_filename)

                try:
                    print(f"  Converting: {nrrd_path}")
                    data, header = nrrd.read(nrrd_path)

                    # Construct affine matrix from NRRD header
                    # Default to identity if space info is missing
                    affine = np.eye(4)
                    if 'space directions' in header and 'space origin' in header:
                        space_directions = header['space directions']
                        space_origin = header['space origin']
                        
                        # Ensure space_directions is a list of lists/arrays
                        if len(np.array(space_directions).shape) == 1:
                            # Handle simple spacing case (diagonal matrix)
                            affine[0, 0] = space_directions[0]
                            affine[1, 1] = space_directions[1]
                            affine[2, 2] = space_directions[2]
                        else:
                            # Handle full direction matrix
                            affine[0, :3] = space_directions[0]
                            affine[1, :3] = space_directions[1]
                            affine[2, :3] = space_directions[2]
                        
                        affine[:3, 3] = space_origin

                    # Create NIfTI image
                    nifti_img = nib.Nifti1Image(data, affine)
                    
                    # Save the NIfTI image
                    nib.save(nifti_img, output_path)
                    print(f"  -> Saved: {output_path}")
                    conversion_count += 1

                except Exception as e:
                    err_msg = f"  ERROR converting '{nrrd_path}': {e}"
                    print(err_msg)
                    errors.append(err_msg)

    print("\n--- CONVERSION SUMMARY ---")
    print(f"Files converted to .nii.gz: {conversion_count}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
    else:
        print("No errors encountered.")
    print("--- CONVERSION FINISHED ---\n")


if __name__ == "__main__":
    # Root path of the dataset to scan
    dataset_root = r"D:\3D-Segmentation-and-Modeling-of-Lower-Limb-Bones\CV Dataset"
    
    # Convert the extracted .nrrd files to .nii.gz
    convert_to_nii_gz(dataset_root)
