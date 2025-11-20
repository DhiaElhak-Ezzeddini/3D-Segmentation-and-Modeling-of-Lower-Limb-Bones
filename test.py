import nibabel as nib
import numpy as np

lab = nib.load("D:\\3D-Segmentation-and-Modeling-of-Lower-Limb-Bones\\Data Preparation\\nnUNet_raw_data\\Dataset001_LowerLimb\\labelsTr\\LOWERLIMB_001.nii.gz").get_fdata()
print(np.unique(lab))
