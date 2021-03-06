# Open3D: www.open3d.org
# The MIT License (MIT)
# See license file or visit www.open3d.org for details
# examples/Python/Advanced/global_registration.py
import open3d as o3d
import numpy as np
import copy
import pdb
from open3d.open3d.geometry import OrientedBoundingBox

def draw_registration_result(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
#    source_temp.paint_uniform_color([1, 0.706, 0])
#    target_temp.paint_uniform_color([0, 0.651, 0.929])
    source_temp.transform(transformation)
    o3d.visualization.draw_geometries([source_temp, target_temp])
def preprocess_point_cloud(pcd, voxel_size):
    print(":: Downsample with a voxel size %.3f." % voxel_size)
    pcd_down = pcd.voxel_down_sample(voxel_size)
    radius_normal = voxel_size * 2
    print(":: Estimate normal with search radius %.3f." % radius_normal)
    pcd_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))
    radius_feature = voxel_size * 5
    print(":: Compute FPFH feature with search radius %.3f." % radius_feature)
    pcd_fpfh = o3d.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100))
    return pcd_down, pcd_fpfh
def prepare_dataset(voxel_size):
    print(":: Load two point clouds and disturb initial pose.")
    source = o3d.io.read_point_cloud("arm1.ply")
    target = o3d.io.read_point_cloud("arm2.ply")
    trans_init = np.asarray(
        [[0.90704613, - 0.00783087, - 0.42095842,  0.59964802],
         [-0.02395237,  0.99724801, - 0.07016185,  0.08528194],
        [0.42034937,    0.07372299,    0.90436239, - 0.01007276],
    [0.,          0.,         0.,          1.]]
    )
    #source.transform(trans_init)
    draw_registration_result(source, target, np.identity(4))
    source_down, source_fpfh = preprocess_point_cloud(source, voxel_size)
    target_down, target_fpfh = preprocess_point_cloud(target, voxel_size)
    return source, target, source_down, target_down, source_fpfh, target_fpfh
def execute_global_registration(source_down, target_down, source_fpfh,
                                target_fpfh, voxel_size):
    distance_threshold = voxel_size * 1.5
    print(":: RANSAC registration on downsampled point clouds.")
    print("   Since the downsampling voxel size is %.3f," % voxel_size)
    print("   we use a liberal distance threshold %.3f." % distance_threshold)
    result = o3d.registration.registration_ransac_based_on_feature_matching(
        source_down, target_down, source_fpfh, target_fpfh, distance_threshold,
        o3d.registration.TransformationEstimationPointToPoint(False), 4, [
            o3d.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
            o3d.registration.CorrespondenceCheckerBasedOnDistance(
                distance_threshold)
        ], o3d.registration.RANSACConvergenceCriteria(4000000, 500))
    return result

def refine_registration(source, target, source_fpfh, target_fpfh, voxel_size):
    distance_threshold = voxel_size * 0.4

    print(":: Point-to-plane ICP registration is applied on original point")
    print("   clouds to refine the alignment. This time we use a strict")
    print("   distance threshold %.3f." % distance_threshold)
    result = o3d.registration.registration_icp(
        source, target, distance_threshold, tf1,
        o3d.registration.TransformationEstimationPointToPlane())
    return result

if __name__ == "__main__":
    voxel_size = 0.05  # means 5cm for the dataset
    source, target, source_down, target_down, source_fpfh, target_fpfh = \
            prepare_dataset(voxel_size)
    #pdb.set_trace()
    source_percent = 70
    target_percent = 30

    R = np.identity(3)
    tmp = np.asarray(source.points)
    source_bound = np.percentile(tmp[:,1], source_percent)
    source_center = np.array([[0], [(-0.5+source_bound)/2], [0.5]])
    source_extent = np.array([[1], [1 - (0.5 - source_bound)], [1]])
    source_box = OrientedBoundingBox(source_center, R, source_extent)
    source = source.crop(source_box)

    tmp2 = np.asarray(target.points)
    target_bound = np.percentile(tmp2[:,1], target_percent)
    target_center = np.array([[0], [(0.5+target_bound)/2], [0.5]])
    target_extent = np.array([[1], [1 - (target_bound+0.5)], [1]])
    target_box = OrientedBoundingBox(target_center, R, target_extent)
    target = target.crop(target_box)

    source_c = copy.deepcopy(source)
    target_c = copy.deepcopy(target)

    print("percent", source_percent, target_percent)

    #result_ransac = execute_global_registration(source_down, target_down,source_fpfh, target_fpfh, voxel_size)
    tf1 = np.array([[ 0.99602936, -0.05495211, -0.07004126,  0.06738536],
 [ 0.04685343,  0.99255318, -0.11244086,  0.05507927],
 [ 0.07569854, 0.10871273,  0.9911868,  -0.23161111],
 [ 0.,          0.,          0.,          1.        ]

    ])
    tf2 = np.array([[0.9444,    0.0431,   -0.3259,    0.2551],
   [-0.0218,    0.9974,    0.0685,   -0.0160],
    [0.3280,   -0.0576,    0.9429,   -0.0531],
     [    0,         0,        0,    1.0000]
    ])
    #print(result_ransac)
    #print("transformation")
    #print(result_ransac.transformation)
    pdb.set_trace()
    print("raw data")
    draw_registration_result(source, target, np.identity(4))

    print("global regi")
    draw_registration_result(source, target, tf1)

    print("hmrf regi")
    draw_registration_result(source, target, np.matmul(tf2, tf1))

    draw_registration_result(source_down, target_down,
                             tf1)

    #s_down = source.voxel_down_sample(0.04)
    #t_down = target.voxel_down_sample(0.04)
    #s_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.08, max_nn=30))
    #t_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.08, max_nn=30))
    #result_icp = o3d.registration.registration_icp(s_down, t_down, 0.1, tf1, o3d.registration.TransformationEstimationPointToPlane())


    source.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.08, max_nn=30))
    target.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.08, max_nn=30))

    #draw_registration_result(source, target, np.identity(4))
    result_icp = refine_registration(source, target, source_fpfh, target_fpfh, voxel_size)
    print(result_icp)

    print("point-to-plane regi")
    draw_registration_result(source_c, target_c, result_icp.transformation)

