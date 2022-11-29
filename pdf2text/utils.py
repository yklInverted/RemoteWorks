import os
import cv2
import numpy as np

from pdf2image import convert_from_path
import pytesseract

def pdf2imgs(pdf_path, poppler_path = "D:\\Program Files\\poppler-22.11.0\\Library\\bin"):
    '''将指定的pdf文件转换为图像,每一页对应一个图像
    '''
    imgs = convert_from_path(pdf_path, poppler_path = poppler_path)
    return [np.array(img) for img in imgs]


def img2text(image, language = 'chi_sim+deu', config = '--psm 6'):
    return pytesseract.image_to_string(image, lang = language, config = config)


class TableSplitter():

    def __init__(self, scale = 25, params_margin_x = 20, params_margin_y = 20, params_dot_margin = 3, params_line_x = 20, params_line_y = 20) -> None:
        
        self._scale = scale #表格中横线或竖线最短像素长度
        self._params_margin_x = params_margin_x # 竖线最小间距
        self._params_margin_y = params_margin_y # 横线最小间距
        self._params_dot_margin = params_dot_margin # 和平均线的偏移量（对缝隙起作用，可去除点，也可变为独立一个点） 太大：被当成另一条直线上，太小：不把它当成一个独立的点
        self._params_line_x = params_line_x # x上点个数的差值调节（线不均匀，有的粗有的细，甚至有的不连续）
        self._params_line_y = params_line_y # y上点个数的差值调节（线不均匀，有的粗有的细，甚至有的不连续）


    def recognize_line_x(self, line_xs, line_ys, num, num1, num2):
        y_line_list = []

        for k in [-3, -2, -1, 0, 1, 2, 3]:
            for i in range(len(line_xs)):
                if line_xs[i] == num + k:
                    if line_ys[i] >= num1 and line_ys[i] <= num2 and line_ys[i] not in y_line_list:
                        y_line_list.append(line_ys[i])
        len_list = len(y_line_list)

        return len_list


    def recognize_line_y(self, line_xs, line_ys, num, num1, num2):
        x_line_list = []
        for k in [-3, -2, -1, 0, 1, 2, 3]:
            for i in range(len(line_xs)):
                if line_ys[i] == num + k:
                    if line_xs[i] >= num1 and line_xs[i] <= num2 and line_xs[i] not in x_line_list:
                        x_line_list.append(line_xs[i])
        len_list = len(x_line_list)

        return len_list


    def split_image(self, image):
        # 二值化(自适应阈值二值化)
        """
        dst = cv2.adaptiveThreshold(src, maxval, thresh_type, type, BlockSize, C)
        src： 输入图，只能输入单通道图像，通常来说为灰度图
        dst： 输出图
        maxval： 当像素值超过了阈值（或者小于阈值，根据type来决定），所赋予的值
        thresh_type： 阈值的计算方法，包含以下2种类型：cv2.ADAPTIVE_THRESH_MEAN_C(通过平均方法取平均值)； cv2.ADAPTIVE_THRESH_GAUSSIAN_C（通过高斯）.
        type：二值化操作的类型，与固定阈值函数相同，包含以下5种类型： cv2.THRESH_BINARY； cv2.THRESH_BINARY_INV； cv2.THRESH_TRUNC； cv2.THRESH_TOZERO；cv2.THRESH_TOZERO_INV.
        BlockSize： 图片中分块的大小
        C ：阈值计算方法中的常数项
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(~gray, 255,
                                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -10)
        cv2.imwrite('cell.jpg', binary)

        rows, cols = binary.shape
        print('rows',  rows)
        print('cols',  cols)
        

        """
        腐蚀是一种消除边界点，使边界向内部收缩的过程   可以用来消除小且无意义的物体.
        膨胀是将与物体接触的所有背景点合并到该物体中，使边界向外部扩张的过程   可以用来填补物体中的空洞.
        
        用 cols // scale x 1 的 kernel，扫描图像的每一个像素；
        用 kernel 与其覆盖的二值图像做 “与” 操作；
        如果都为1，结果图像的该像素为1；否则为0.
        """
        # 原理：这个参数决定了 横线或者竖线的长度
        scale = self._scale  # 调节是否能精确识别点（粗、模糊 +   细、清晰  -）
        dil_coef = 1.3 # 扩张补偿系数

        # 用横条识别横线
        ero_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (scale, 1))
        dil_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(scale *dil_coef), 1))
        eroded = cv2.erode(binary, ero_kernel, iterations=1) 
        dilatedcol = cv2.dilate(eroded, dil_kernel, iterations=1)
        cv2.imwrite('dilated1.jpg', dilatedcol)

        # 用竖条识别竖线
        ero_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, scale))
        dil_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(scale *dil_coef)))
        eroded = cv2.erode(binary, ero_kernel, iterations=1)
        dilatedrow = cv2.dilate(eroded, dil_kernel, iterations=1)
        cv2.imwrite('dilated2.jpg', dilatedrow)

        # 标识交点
        bitwiseAnd = cv2.bitwise_and(dilatedcol, dilatedrow)
        cv2.imwrite('bitwise.jpg', bitwiseAnd)

        # 标识表格
        merge = cv2.add(dilatedcol, dilatedrow)
        cv2.imwrite('add.jpg', merge)

        # 识别表格中所有的线
        line_ys, line_xs = np.where(merge > 0)

        # 识别黑白图中的白色点
        ys, xs = np.where(bitwiseAnd > 0)  # 交点附近的坐标

        mylisty = []
        mylistx = []

        # 通过排序，获取跳变的x和y的值，说明是交点，否则交点会有好多像素值，我只取最后一点
        i = 0
        myxs = np.sort(xs)
        # print('myxs', myxs)
        for i in range(len(myxs) - 1):
            if (myxs[i + 1] - myxs[i] > self._params_margin_x):
                mylistx.append(myxs[i])
            i = i + 1
        mylistx.append(myxs[i]) # 包括最后一点，每个点都取的是最大的一个
        print('纵向：', mylistx)
        print('纵向线数：', len(mylistx))

        i = 0
        myys = np.sort(ys)
        for i in range(len(myys) - 1):
            if (myys[i + 1] - myys[i] > self._params_margin_y):
                mylisty.append(myys[i])
            i = i + 1
        mylisty.append(myys[i])
        print('横向', mylisty)
        print('横向线数：', len(mylisty))


        #对于第i个交点像素，找到对应的横线和竖线
        data_dict = {}
        data_list = []
        for i in range(len(myys)):
            for m in mylisty:
                for n in mylistx:
                    if abs(m - ys[i]) < self._params_dot_margin and abs(n - xs[i]) < self._params_dot_margin and (m, n) not in data_list:
                        data_list.append((m, n))

        print('data_list', data_list)
        print(len(data_list))

        for m in range(len(mylisty)):
            line_list = []
            for i in data_list:
                if i[0] == mylisty[m]:
                    line_list.append(i)
            data_dict[m] = sorted(line_list, key=lambda x: x[1])
        print('data_dict', data_dict)


        img_dict = {}
        for i in range(len(data_dict) - 1):
            for index, value in enumerate(data_dict[i]):
                m = i
                if index == len(data_dict[i]) - 1:
                    break

                for nn in range(1, len(data_dict[i])):
                    m = i
                    mark_num = 0
                    n = index + nn
                    if n == len(data_dict[i]):
                        break

                    while m <= len(data_dict)-2:                      # recognize_line(line_xs, line_ys, 161, 57, 88)
                        if value[1] in [i[1] for i in data_dict[m + 1]] and data_dict[i][n][1] in [i[1] for i in data_dict[m + 1]] and abs(self.recognize_line_x(line_xs, line_ys, value[1], value[0], data_dict[m + 1][0][0])- (data_dict[m + 1][0][0] - value[0])) <= self._params_line_y and abs(self.recognize_line_x(line_xs, line_ys, data_dict[i][n][1], value[0], data_dict[m + 1][0][0])- (data_dict[m + 1][0][0] - value[0])) <= self._params_line_y and abs(self.recognize_line_y(line_xs, line_ys, value[0], value[1], data_dict[i][n][1]) - (data_dict[i][n][1] - value[1])) <= self._params_line_x and abs(self.recognize_line_y(line_xs, line_ys, data_dict[m + 1][0][0], value[1], data_dict[i][n][1]) - (data_dict[i][n][1] - value[1])) <= self._params_line_x:
                            mark_num = 1
                            ROI = image[value[0]:data_dict[m + 1][0][0], value[1]:data_dict[i][n][1]]

                            order_num1 = mylisty.index(value[0])
                            order_num2 = mylisty.index(data_dict[m + 1][0][0]) - 1
                            order_num3 = mylistx.index(value[1])
                            order_num4 = mylistx.index(data_dict[i][n][1]) - 1

                            img_dict[(order_num1 + 1, order_num2 + 1, order_num3 + 1, order_num4 + 1)] = ROI
                            cv2.imwrite(f'./parse/{len(img_dict.keys())}.png', ROI)
                            break
                        else:
                            m += 1

                    if mark_num == 1:
                        break
        return img_dict