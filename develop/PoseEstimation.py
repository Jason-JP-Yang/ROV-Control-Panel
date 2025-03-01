import cv2
import numpy as np
import glob
import os

chessboard_size = (9, 6)

objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
axis = np.float32([[0,0,0], [0,2,0], [2,2,0], [2,0,0],
                   [0,0,-2],[0,2,-2],[2,2,-2],[2,0,-2] ])
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

def draw(img, corners, imgpts):
    imgpts = np.int32(imgpts).reshape(-1,2)
 
    # draw ground floor in green
    img = cv2.drawContours(img, [imgpts[:4]],-1,(0,255,0),-3)
 
    # draw pillars in blue color
    for i,j in zip(range(4),range(4,8)):
        img = cv2.line(img, tuple(imgpts[i]), tuple(imgpts[j]),(255),3)
 
    # draw top layer in red color
    img = cv2.drawContours(img, [imgpts[4:]],-1,(0,0,255),3)
 
    return img

# 存储对象点和图像点
objpoints = []  # 3D真实世界坐标
imgpoints = []  # 2D图像坐标

# 读取棋盘格图像
images = glob.glob('develop/calibrateIMG/*.jpg')
mtx = np.load('camera_matrix.npy')
dist = np.load('dist_coeffs.npy')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
    
    if ret == True:
        corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)

        # Find the rotation and translation vectors.
        ret,rvecs, tvecs = cv2.solvePnP(objp, corners2, mtx, dist)

        # project 3D points to image plane
        imgpts, jac = cv2.projectPoints(axis, rvecs, tvecs, mtx, dist)

        img = draw(img,corners2,imgpts)
        cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
        cv2.imwrite(f'develop/corner/{os.path.basename(fname)}', img)