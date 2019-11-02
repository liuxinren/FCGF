import os
import logging
import numpy as np

from util.trajectory import CameraPose
from util.baseline import run_ransac
from util.pointcloud import compute_overlap_ratio, \
    make_open3d_point_cloud, make_open3d_feature_from_numpy


def gather_results(results):
  traj = []
  for r in results:
    success = r[0]
    if success:
      traj.append(CameraPose([r[1], r[2], r[3]], r[4]))
  return traj


def gen_matching_pair(pts_num):
  matching_pairs = []
  for i in range(pts_num):
    for j in range(i + 1, pts_num):
      matching_pairs.append([i, j, pts_num])
  return matching_pairs


def read_data(feature_path, name):
  data = np.load(os.path.join(feature_path, name + ".npz"))
  xyz = make_open3d_point_cloud(data['xyz'])
  feat = make_open3d_feature_from_numpy(data['feature'])
  return data['points'], xyz, feat


def do_single_pair_matching(feature_path, set_name, m, voxel_size):
  i, j, s = m
  name_i = "%s_%03d" % (set_name, i)
  name_j = "%s_%03d" % (set_name, j)
  logging.info("matching %s %s" % (name_i, name_j))
  points_i, xyz_i, feat_i = read_data(feature_path, name_i)
  points_j, xyz_j, feat_j = read_data(feature_path, name_j)
  if len(xyz_i.points) < len(xyz_j.points):
    trans = run_ransac(xyz_i, xyz_j, feat_i, feat_j, voxel_size).cpu().numpy()
  else:
    trans = run_ransac(xyz_j, xyz_i, feat_j, feat_i, voxel_size).cpu().numpy()
    trans = np.linalg.inv(trans)
  ratio = compute_overlap_ratio(xyz_i, xyz_j, trans, voxel_size)
  logging.info(f"{ratio}")
  if ratio > 0.3:
    return [True, i, j, s, np.linalg.inv(trans)]
  else:
    return [False, i, j, s, np.identity(4)]
