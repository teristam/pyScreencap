print('Python code starting...')

import PySimpleGUIQt as sg
import pyscreenshot as ImageGrab
import time
import glob
import skimage as ski
import numpy as np
from io import BytesIO
from skimage import transform
from skimage import io as sio
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import landscape,A4
from pathlib import Path
import subprocess
import platform


def load_images(folder, progressbar=None):
    n = len(glob.glob(f"{folder}/*.png"))

    images = np.zeros((n, 1080 // 2, 1920 // 2))

    imageList = np.arange(n)

    for i in imageList:
        image = ski.io.imread(f"{folder}/{i}.png")
        image = ski.color.rgb2gray(image)
        image = ski.transform.resize(image, (1080 / 2, 1920 / 2))
        images[i, :, :] = image

        if progressbar:
            progressbar.UpdateBar(i/(n-1)*100)

    return images


def analyze_slide_change(images):
    imageList = np.arange(len(images))
    # calculate differences between images
    imFlatten = images.reshape(-1, images.shape[1] * images.shape[2])
    imDiff = np.diff(imFlatten, axis=0)
    imDiffMS = np.mean(imDiff ** 2, axis=1)

    # %% Remove the outliners first
    median = np.median(imDiffMS)
    std = np.std(imDiffMS)
    outliner_thres = median + 2 * std
    outliner_idx = np.flatnonzero(imDiffMS > outliner_thres)

    imDiffMS_clean = np.delete(imDiffMS, outliner_idx)
    image_clean = np.delete(images, outliner_idx, axis=0)
    imageList_clean = np.delete(imageList, outliner_idx)

    print(f"{len(outliner_idx)} outliners removed")

    #%% Detect change of slides
    change_thres = np.median(imDiffMS_clean) + np.std(imDiffMS_clean)
    change_idx = np.flatnonzero(imDiffMS_clean > change_thres)

    imageList_change = imageList_clean[change_idx]

    return imageList_change


def build_slide_pdf(imageList,base_folder, filename):

    doc = SimpleDocTemplate(base_folder+'/'+filename)
    doc.pagesize = landscape(A4)

    story = []
    width = 10 * inch
    height = width * 1080 / 1920
    for i in imageList:
        im = Image(f"{base_folder}/{i}.png", width, height)
        story.append(im)
        story.append(PageBreak())

    doc.build(story)


def open_file(filepath):
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(filepath)
    else:                                   # linux variants
        subprocess.call(('xdg-open', filepath))

layout = [
    [sg.Image("0.png", key="screenshot")],
    [
        sg.Input("./data/chap28", key="folderPath", size=(50, 0.5)),
        sg.FolderBrowse(initial_folder=".", key="browseFolder", target="folderPath"),
        sg.Button("Analyze", key="analyze"),
    ],
    [
        sg.Input(5, key="delayTime"),
        sg.Button("Record", key="recordBtn"),
        sg.Text("0", key="imgIdx"),
    ],
    [sg.Text('Analyzis progress',key='progressText'),sg.ProgressBar(100, key="progressbar", size=(5, 1))],
]

window = sg.Window(
    "pySlideCap", use_native_style=True, layout=layout, element_padding=(10, 10)
)

record = False

imgIdx = 0
startTime = 0
imageBuffer = BytesIO()
timeout = None

while True:
    event, values = window.read(timeout=timeout)

    if event in (None, "Exit"):
        break

    if event == "recordBtn":
        record = not record

        if record == True:
            window["recordBtn"].update("Stop")
            window["delayTime"].update(disabled=True)
            window["browseFolder"].update(disabled=True)
            startTime = time.time()
            timeout = 100
        else:
            record = False
            window["recordBtn"].update("Record")
            window["delayTime"].update(disabled=False)
            window["browseFolder"].update(disabled=False)
            timeout = None

    if event == "analyze":
        window['progressText'].update('Loading images')
        images = load_images(values["folderPath"], window["progressbar"])

        folderPath = values['folderPath']

        window['progressText'].update('Analyzing images')
        image_list = analyze_slide_change(images)
        filename = Path(folderPath).name + '.pdf'

        window['progressText'].update('Building PDF')
        build_slide_pdf(image_list, folderPath,filename)

        window['progressText'].update('Finished')

        open_file(folderPath+'/'+filename)

        


    if record:
        # Do a screen shot when the delay time has reached
        if time.time() - startTime > int(values["delayTime"]):
            window["imgIdx"].update(imgIdx)
            startTime = time.time()

            # save screenshot
            im = ImageGrab.grab(backend="mac_screencapture", childprocess=False)
            folderPath = values["folderPath"]
            im.save(f"{folderPath}/{imgIdx}.png")

            # resize for display
            im = np.array(im)
            image = transform.resize(im, (im.shape[0] // 2, im.shape[1] // 2))
            image = (image * 255).astype(np.uint8)
            sio.imsave("temp.png", image)

            window["screenshot"].update("temp.png")

            imgIdx += 1

        # im.save(filename)

