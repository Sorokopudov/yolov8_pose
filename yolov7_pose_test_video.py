import torch
from torchvision import transforms
from PIL import Image, ImageDraw
from utils.datasets import letterbox
from utils.general import non_max_suppression_kpt
from utils.plots import output_to_keypoint, plot_skeleton_kpts

import matplotlib.pyplot as plt
import cv2
import numpy as np

# https://stackabuse.com/pose-estimation-and-keypoint-detection-with-yolov7-in-python/
# https://pytorch.org/docs/stable/generated/torch.no_grad.html
# https://learnopencv.com/yolov7-pose-vs-mediapipe-in-human-pose-estimation/

def load_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.load('yolov7-w6-pose.pt', map_location=device)['model']
    # Put in inference mode
    model.float().eval()

    if torch.cuda.is_available():
        # half() turns predictions into float16 tensors
        # which significantly lowers inference time
        model.type(torch.FloatTensor).to(device)
    return model

def run_inference(image):
    # image = cv2.imread(url) # shape: (480, 640, 3)
    # Resize and pad image
    image = letterbox(image, 960, stride=64, auto=True)[0] # shape: (768, 960, 3)
    # Apply transforms
    image = transforms.ToTensor()(image) # torch.Size([3, 768, 960])
    # Turn image into batch
    image = image.unsqueeze(0) # torch.Size([1, 3, 768, 960])
    with torch.no_grad(): # - при использовании gpu важно делать инференс именно через with torch.no_grad(), иначе будет забиваться память gpu
        output, _ = model(image) # torch.Size([1, 45900, 57])  -
    return output, image

def visualize_output(output, image):
    output = non_max_suppression_kpt(output,
                                     0.25, # Confidence Threshold
                                     0.65, # IoU Threshold
                                     nc=model.yaml['nc'], # Number of Classes
                                     nkpt=model.yaml['nkpt'], # Number of Keypoints
                                     kpt_label=True)
    with torch.no_grad():
        output = output_to_keypoint(output)
    nimg = image[0].permute(1, 2, 0) * 255
    nimg = nimg.cpu().numpy().astype(np.uint8)
    nimg = cv2.cvtColor(nimg, cv2.COLOR_RGB2BGR)
    for idx in range(output.shape[0]):
        plot_skeleton_kpts(nimg, output[idx, 7:].T, 3)
    # plt.figure(figsize=(12, 12))
    # plt.axis('off')
    # plt.imshow(nimg)
    plt.show()
    return nimg

# Используемые цвета:
COLOR_RED = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_BLACK = (0, 0, 0)
COLOR_SILVER = (192, 192, 192)

video_path = r'D:\Vf\Human_pose_detection\yolov7_pose\video_for_test\graffiti.mp4'  # видео, которое будем обрабатывать
new_video_path = r'D:\Vf\Human_pose_detection\yolov7_pose\video_test\vid_1.avi'

cap = cv2.VideoCapture(video_path)

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
frame_size = (frame_width,frame_height)

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
new_video = cv2.VideoWriter(new_video_path, fourcc=fourcc, fps=30, apiPreference=0, frameSize=frame_size)

frame_N = 1


model = load_model()

while True:
    ret, frame = cap.read()
    print('frame_size', frame_size)
    if not ret:
        break
    # try:
    print('frame_N:', frame_N)
    output, image = run_inference(frame)
    visualize_frame = visualize_output(output, image)

    # except Exception as e:
    #     pass
    visualize_frame = cv2.resize(visualize_frame, frame_size)
    visualize_frame = cv2.cvtColor(visualize_frame, cv2.COLOR_BGR2RGB)
    new_video.write(visualize_frame)
    print('visualize_frame', visualize_frame.shape)
    frame_N = frame_N + 1
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break