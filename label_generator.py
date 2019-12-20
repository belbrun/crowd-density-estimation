import h5py
import scipy.io as io
import PIL.Image as Image
import numpy as np
import os
import glob
from matplotlib import pyplot as plt
from scipy.ndimage.filters import gaussian_filter
import scipy
from matplotlib import cm as CM
import scipy.spatial

root = 'ShanghaiTech_Crowd_Counting_Dataset/'

def get_paths(set, N):

    img_paths = []
    for i in range(1, N+1):
        img_paths.append(os.path.join(set, 'IMG_'+str(i)+'.jpg'))
    return img_paths


# function to create density maps for images
def gaussian_filter_density(gt):
    print (gt.shape)
    density = np.zeros(gt.shape, dtype=np.float32)
    gt_count = np.count_nonzero(gt)
    if gt_count == 0:
        return density

    pts = np.array(list(zip(np.nonzero(gt)[1], np.nonzero(gt)[0])))
    leafsize = 2048
    # build kdtree
    tree = scipy.spatial.KDTree(pts.copy(), leafsize=leafsize)
    # query kdtree
    distances, locations = tree.query(pts, k=4)

    print ('generate density...')
    for i, pt in enumerate(pts):
        pt2d = np.zeros(gt.shape, dtype=np.float32)
        pt2d[pt[1],pt[0]] = 1.
        if gt_count > 1:
            sigma = (distances[i][1]+distances[i][2]+distances[i][3])*0.1
        else:
            sigma = np.average(np.array(gt.shape))/2./2. #case: 1 point
        density += scipy.ndimage.filters.gaussian_filter(pt2d, sigma, mode='constant')
    print ('done.')
    return density





def get_count(img_path):
    mat = io.loadmat(img_path.replace('.jpg','.mat').replace('images','ground_truth').replace('IMG_','GT_IMG_'))
    img= plt.imread(img_path)
    k = np.zeros((img.shape[0],img.shape[1]))
    gt = mat["image_info"][0,0][0,0][0]
    for i in range(0,len(gt)):
        if int(gt[i][1])<img.shape[0] and int(gt[i][0])<img.shape[1]:
            k[int(gt[i][1]),int(gt[i][0])]=1
    k = gaussian_filter_density(k)
    with h5py.File(img_path.replace('.jpg','.h5').replace('images','ground_truth'), 'w') as hf:
            hf['density'] = k

    gt_file = h5py.File(img_path.replace('.jpg','.h5').replace('images','ground_truth'),'r')
    groundtruth = np.asarray(gt_file['density'])
    plt.imshow(groundtruth,cmap=CM.jet)

    return np.sum(groundtruth)

def generate_label(count):
    lower, upper = 50, 250
    if count < lower:
        return 0
    elif count < upper:
        return 1
    else:
        return 2

def save(name, data):
    with open(name, 'w+') as file:
        for i, row in enumerate(data):
            d = str(row) if i+1 == len(data) else str(row) + '\n'
            file.write(d)

def save_labels(set, labels):
    save(set + '/labels.txt', labels)


def save_counts(set, counts):
    save(set + '/counts.txt', counts)

def load_counts(set):
    with open(set + '/counts.txt', 'r+') as file:
        return [float(c) for c in file.read().split('\n')]

def class_ratios(labels):
    counts = [0, 0, 0]
    for label in labels:
        counts[label] += 1
    return [c/len(labels) for c in counts]

def count(path_sets):

    for set, N in path_sets:
        counts = []
        for path in get_paths(set, N):
            counts.append(get_count(path))
        print(counts)
        save_counts(set, counts)

def label(path_sets):
    for set, _ in path_sets:
        labels = []
        for count in load_counts(set):
            labels.append(generate_label(count))
        print(class_ratios(labels))
        save_labels(set, labels)


def main():

    part_A_train = os.path.join(root,'part_A_final/train_data','images')
    part_A_test = os.path.join(root,'part_A_final/test_data','images')
    part_B_train = os.path.join(root,'part_B_final/train_data','images')
    part_B_test = os.path.join(root,'part_B_final/test_data','images')

    path_sets = [(part_A_train, 300), (part_A_test, 182)]
    path_sets = [(part_B_train, 400), (part_B_test, 316)]

    count(path_sets)
    label(path_sets)


if __name__ == '__main__':
    main()
