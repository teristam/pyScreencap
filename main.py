#%%
import pyscreenshot as ImageGrab
import time
import glob
import skimage as ski 
import numpy as np 
from tqdm import tqdm
import matplotlib.pylab as plt

chapter = 'chap27'

#%% Recoding screen

# grab fullscreen
imgIdx = 0


while True:
    im = ImageGrab.grab()

    # save image file
    im.save(f'data/{chapter}/{imgIdx}.png')

    print(imgIdx)
    time.sleep(5)
    imgIdx += 1

#%% Load saved images

n = len(glob.glob(f'data/{chapter}/*.png'))
images = np.zeros((n,1080//2,1920//2))

imageList = np.arange(n)

for i in tqdm(imageList):
    image = ski.io.imread(f'data/{chapter}/{i}.png')
    image = ski.color.rgb2gray(image)
    image = ski.transform.resize(image, (1080/2,1920/2))
    images[i,:,:] = image

 
# %% Calculate distance between frames

# images = np.load('images.npy')
imFlatten = images.reshape(-1,images.shape[1]*images.shape[2])
imDiff = np.diff(imFlatten,axis=0)
imDiffMS = np.mean(imDiff**2,axis=1)
plt.plot(imDiffMS)

# %% Remove the outliners first

median = np.median(imDiffMS)
std = np.std(imDiffMS)
outliner_thres = median + 2*std
outliner_idx = np.flatnonzero(imDiffMS>outliner_thres)

# for i in outliner_idx[:10]:
#     plt.figure()
#     ski.io.imshow(images[i,:,:])

imDiffMS_clean = np.delete(imDiffMS,outliner_idx)
image_clean = np.delete(images,outliner_idx,axis=0)
imageList_clean = np.delete(imageList,outliner_idx)

print(f'{len(outliner_idx)} outliners removed')

#%% Detect change of slides
change_thres = np.median(imDiffMS_clean) + np.std(imDiffMS_clean)
change_idx = np.flatnonzero(imDiffMS_clean > change_thres)

imageList_change = imageList_clean[change_idx]

# for i in change_idx:
#     plt.figure()
#     ski.io.imshow(image_clean[i,:,:])


# %% save the extracted page as pdfs
from reportlab.platypus import *
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import *

doc = SimpleDocTemplate(f'data/{chapter}.pdf')
doc.pagesize = landscape(A4)

story = []
width = 9.5*inch
height = width * 1080/1920
for i in imageList_change:
    im = Image(f'data/{chapter}/{i}.png',width,height)
    story.append(im)
    story.append(PageBreak())

doc.build(story)
# %%
