import cv2
import numpy as np
import glob
import os

# 设置棋盘格内角点行列数
chessboard_size = (9, 6)

# 准备对象点
objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)

# 存储对象点和图像点
objpoints = []  # 3D真实世界坐标
imgpoints = []  # 2D图像坐标

# 读取棋盘格图像
images = glob.glob('develop/calibrateIMG/*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 检测角点
    ret, corners = cv2.findChessboardCorners(
        gray, chessboard_size, 
        flags=cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
    )
    
    if ret:
        objpoints.append(objp)
        # 亚像素优化
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)
        
        cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
        cv2.imwrite(f'develop/corner/{os.path.basename(fname)}', img)

# 校准相机
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)
# 输出结果
print("相机矩阵:\n", camera_matrix)
print("畸变系数:", dist_coeffs)
# 保存参数
np.save('camera_matrix.npy', camera_matrix)
np.save('dist_coeffs.npy', dist_coeffs)
# 加载参数
camera_matrix = np.load('camera_matrix.npy')
dist_coeffs = np.load('dist_coeffs.npy')

# 计算每张图像的重投影误差
mean_errors = []  # 存储每张图的平均误差

for i in range(len(objpoints)):
    # 投影3D点到图像平面
    imgpoints2, _ = cv2.projectPoints(
        objpoints[i], 
        rvecs[i], 
        tvecs[i], 
        camera_matrix, 
        dist_coeffs
    )
    
    # 计算误差
    error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
    mean_errors.append(error)
    
    # 打印单张图像误差
    print(f"图像 {i+1} 重投影误差: {error:.5f} 像素")

# 计算总平均误差
total_error = np.sqrt(np.mean(np.square(mean_errors)))
print(f"\n总平均重投影误差: {total_error:.5f} 像素")

# 读取测试图像
img = cv2.imread('develop/calibrateIMG/20250301_17_26_45.jpg')
h, w = img.shape[:2]
# 优化相机矩阵（可选）
new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
    camera_matrix, dist_coeffs, (w, h), 0.3, (w, h)
)

# Undisort Method 校正图像
undistorted_img = cv2.undistort(
    img, camera_matrix, dist_coeffs, None, new_camera_matrix
)

# Remapping Method 校正图像
# mapx, mapy = cv2.initUndistortRectifyMap(camera_matrix, dist_coeffs, None, new_camera_matrix, (w,h), 5)
# undistorted_img = cv2.remap(img, mapx, mapy, cv2.INTER_LANCZOS4)

## 裁剪ROI区域
x, y, w, h = roi
undistorted_img = undistorted_img[y:y+h, x:x+w]

# 显示结果
# cv2.imshow('Original', img)
# cv2.imshow('Undistorted', undistorted_img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

cv2.imwrite(f'develop/undistorted_img.jpg', undistorted_img)