import cv2  
import sys

def draw(image, box):
    """Draw the boxes on the image.

    # Argument:
        image: original image.
        boxes: ndarray, boxes of objects.
        classes: ndarray, classes of objects.
        scores: ndarray, scores of objects.
        all_classes: all classes name.
    """
    print(box)
    top = int(box[0])
    left = int(box[1])
    right = int(box[2])
    bottom = int(box[3])
    cv2.rectangle(image, (top, left), (right, bottom), (255, 0, 0), 2)
    cv2.putText(image, 'leak',
                    (top, left - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 0, 255), 2)

if len(sys.argv) > 1:  
    imgname = sys.argv[1]  
else:  
    imgname = '1.png'

# 读取图片  
resized_img = cv2.imread(imgname)  
boxes=[]
# 创建窗口并设置鼠标回调函数  
def click_event(event, x, y, flags, param):  
    if event == cv2.EVENT_LBUTTONDOWN:  
        # 计算原始图片中的坐标  
        original_x = x
        original_y = y 
        print(f"Original coordinates: ({original_x}, {original_y})")  
  
        # 在原始图片上画出点击的点（这里仅为了演示，实际上窗口显示的是resized_img）  
        #cv2.circle(resized_img, (original_x, original_y), 3, (0, 255, 0), -1)
        boxes.append(original_x)
        boxes.append(original_y)
 
  
# 设置窗口大小和鼠标回调函数  
cv2.namedWindow('image', cv2.WINDOW_NORMAL)  
cv2.setMouseCallback('image', click_event)  
  
# 显示缩小后的图片  
cv2.imshow('image', resized_img)  
  
# 按 'q' 键退出  
while True:  
    if cv2.waitKey(20) & 0xFF == ord('q'):  
        draw(resized_img,boxes)
        cv2.imwrite('./1.jpeg',resized_img)  
        break
  
# 销毁所有窗口  
cv2.destroyAllWindows()
