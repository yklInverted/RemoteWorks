# PDF-Excel Converter
### K Li

这是一个PDF到Excel的端到端转换器，当前为测试版本，请按下方说明安装好dependency并配好环境变量，然后即可使用。
如有任何修改意见请提出issue或联系作者：s220048@e.ntu.edu.sg


## Requirements

- Install [Google Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
  (additional info how to install the engine on Linux, Mac OSX and Windows).
  You must be able to invoke the tesseract command as *tesseract*. If this
  isn't the case, for example because tesseract isn't in your PATH, you will
  have to change the "tesseract_cmd" variable ``pytesseract.pytesseract.tesseract_cmd``.

  *Note:* 在下载语言包时注意勾选需要的语言包，如简中，德语，数学公式等（Tesseract默认只有英语）

- Install Poppler
  Windows users will have to build or download poppler for Windows. I recommend [@oschwartz10612 version](https://github.com/oschwartz10612/poppler-windows/releases/) which is the most up-to-date. You will then have to add the `bin/` folder to [PATH](https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/) or use specify your poppler path when run the converter. The default path of Poppler is "D:\\Program Files\\poppler-22.11.0\\Library\\bin"

- Create Conda Environment
    ```
    conda create -n pdf2excel python=3.10
    conda activate pdf2excel
    ```

- Install required python packages via `pip`

    ```
    pip install -r requirement.txt
    ```


## Usage

- First, since we have provided a PDF file for testing, you can test the converter by running the following command:
    ```
    python main.py --pdfdir test.pdf --page 1
    ```
    There are surely still a lot of space for improvement. To convert a single PDF page to excel takes about 1.5 min, the time highly depends on the complexity of the PDF form.
    
- You can check available arguments using:
    ```
    python main.py -h
    ```