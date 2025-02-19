#  Copyright 2016 Intel Corporation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import numpy as np
from mpi4py import MPI
import nibabel as nib
import sys

from brainiak.searchlight.searchlight import Searchlight
from brainiak.searchlight.searchlight import Diamond

"""Distributed Searchlight Example
example usage: mpirun -n 4 python3 example_searchlight.py

分布式探照灯实例
示例用法：mpirun -n 4 python3 example_searchlight.py

"""

comm = MPI.COMM_WORLD
rank = comm.rank
size = comm.size

# 数据集大小参数  Dataset size parameters

# dim = 40

dim1 = 91
dim2 = 109
dim3 = 91

ntr = 576  # 400   576
kneeNumber = 18
# maskrad = 15

# 预测点参数  Predictive point parameters
pt = (23, 23, 23)
kernel_dim = 5
weight = 1

# 生成数据  Generate data
data = np.random.random((dim1, dim2, dim3, ntr)) if rank == 0 else None  # data 只有在rank==0的时候才有值, 其他的时候都是None

subjectDir = "/gpfs/milgram/project/turk-browne/projects/localize/analysis/subjects/"
subject = 'sub001'
mask = nib.load(
    f"{subjectDir}/{subject}/preprocess/allruns.gfeat/mask.nii.gz")  # /gpfs/milgram/project/turk-browne/projects/localize/analysis/subjects/sub004/preprocess/allruns.gfeat/mask.nii.gz  91x109x91 stand space
affine_mat = mask.affine
print(f"affine_mat.shape={affine_mat.shape}")
mask = mask.get_fdata()
print(f"mask.shape={mask.shape}")
allMaskSum = np.nansum(mask)
print('number of voxels in mask: {}'.format(allMaskSum))  # 239565

# mask = np.zeros((dim, dim, dim), dtype=np.bool)  # mask在任何rank都有值. 不光是在rank==0的时候.
# for i in range(dim):
#     for j in range(dim):
#         for k in range(dim):
#             dist = np.sqrt(((dim / 2) - i) ** 2 + ((dim / 2) - j) ** 2 + ((dim / 2) - k) ** 2)
#             if dist < maskrad:
#                 mask[i, j, k] = 1
# print(f"mask.shape={mask.shape}")
# print(f"np.prod(mask.shape)={np.prod(mask.shape)}")
# print(f"np.nansum(mask)={np.nansum(mask)}")

# 生成标签  Generate labels
labels = np.random.choice([True, False], (ntr, kneeNumber)) if rank == 0 else None  # 只有当rank==0的时候labels才有值,其他时候都是None

# 在随机数据中注入预测性区域  Inject predictive region in random data
if rank == 0:
    kernel = np.zeros((kernel_dim, kernel_dim, kernel_dim))
    for i in range(kernel_dim):
        for j in range(kernel_dim):
            for k in range(kernel_dim):
                arr = np.array([i - (kernel_dim / 2), j - (kernel_dim / 2), k - (kernel_dim / 2)])
                kernel[i, j, k] = np.exp(-np.dot(arr.T, arr))
    kernel = kernel / np.sum(kernel)

    for (idx, l) in enumerate(labels[:, 0]):
        if l:
            data[pt[0]:pt[0] + kernel_dim, pt[1]:pt[1] + kernel_dim, pt[2]:pt[2] + kernel_dim, idx] += kernel * weight
        else:
            data[pt[0]:pt[0] + kernel_dim, pt[1]:pt[1] + kernel_dim, pt[2]:pt[2] + kernel_dim, idx] -= kernel * weight

    print(f"data.shape={data.shape}")
    print(f"labels.shape={labels.shape}")

# 创建探照灯对象  Create searchlight object
sl = Searchlight(sl_rad=1, max_blk_edge=5, shape=Diamond,
                 min_active_voxels_proportion=0)

# 将数据分配给流程  Distribute data to processes
print("sl.distribute([data], mask)")
sl.distribute([data], mask)
print("sl.broadcast(labels)")
sl.broadcast(labels)


# 定义体素函数  Define voxel function
def sfn(l, msk, myrad, bcast_var):
    import sklearn.svm
    import sklearn.model_selection
    classifier = sklearn.svm.SVC(gamma='auto')
    print(f"l[0].shape={l[0].shape}")
    print(f"msk.shape={msk.shape}")
    # data = l[0][msk, :].T
    data = l[0].reshape(msk.shape[0] * msk.shape[1] * msk.shape[2], l[0].shape[3]).T
    print(f"data.shape={data.shape}")
    print(f"bcast_var.shape={bcast_var.shape}")
    return np.mean(sklearn.model_selection.cross_val_score(classifier, data, bcast_var[:, 0], n_jobs=1))


# Run searchlight
global_outputs = sl.run_searchlight(sfn)

# # Visualize result
# if rank == 0:
#     print(global_outputs)
#     global_outputs = np.array(global_outputs, dtype=np.float)
#     import matplotlib.pyplot as plt
#
#     for (cnt, img) in enumerate(global_outputs):
#         plt.imshow(img, cmap='hot', vmin=0, vmax=1)
#         plt.savefig('img' + str(cnt) + '.png')
#         plt.clf()

print("done")
