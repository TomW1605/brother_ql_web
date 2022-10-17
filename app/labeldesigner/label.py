from enum import Enum, auto
from math import floor

from qrcode import QRCode, constants
from PIL import Image, ImageDraw, ImageFont
import textwrap

class LabelContent(Enum):
    TEXT_ONLY = auto()
    QRCODE_ONLY = auto()
    TEXT_QRCODE = auto()
    IMAGE_BW = auto()
    IMAGE_GRAYSCALE = auto()


class LabelOrientation(Enum):
    STANDARD = auto()
    ROTATED = auto()


class LabelType(Enum):
    ENDLESS_LABEL = auto()
    DIE_CUT_LABEL = auto()
    ROUND_DIE_CUT_LABEL = auto()


class TextAlign(Enum):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'


class SimpleLabel:
    qr_correction_mapping = {
        'L': constants.ERROR_CORRECT_L,
        'M': constants.ERROR_CORRECT_M,
        'Q': constants.ERROR_CORRECT_Q,
        'H': constants.ERROR_CORRECT_H
    }

    def __init__(
            self,
            width=0,
            height=0,
            label_content=LabelContent.TEXT_ONLY,
            label_orientation=LabelOrientation.STANDARD,
            label_type=LabelType.ENDLESS_LABEL,
            label_margin=(0, 0, 0, 0),  # Left, Right, Top, Bottom
            fore_color=(0, 0, 0),  # Red, Green, Blue
            text='',
            text_align=TextAlign.CENTER,
            qr_size=10,
            qr_correction='L',
            image_mode='grayscale',
            image=None,
            font_path='',
            font_size=70,
            line_spacing=100,
            shrink_or_wrap='wrap'):
        self._width = width
        self._height = height
        self.label_content = label_content
        self.label_orientation = label_orientation
        self.label_type = label_type
        self._label_margin = label_margin
        self._fore_color = fore_color
        self.text = text
        self._text_align = text_align
        self._qr_size = qr_size
        self.qr_correction = qr_correction
        self._image = image
        self._font_path = font_path
        self._font_size = font_size
        self._line_spacing = line_spacing
        self._shrink_or_wrap = shrink_or_wrap

    @property
    def label_content(self):
        return self._label_content

    @label_content.setter
    def label_content(self, value):
        self._label_content = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def qr_correction(self):
        for key, val in self.qr_correction_mapping:
            if val == self._qr_correction:
                return key

    @qr_correction.setter
    def qr_correction(self, value):
        self._qr_correction = self.qr_correction_mapping.get(
            value, constants.ERROR_CORRECT_L)

    @property
    def label_orientation(self):
        return self._label_orientation

    @label_orientation.setter
    def label_orientation(self, value):
        self._label_orientation = value

    @property
    def label_type(self):
        return self._label_type

    @label_type.setter
    def label_type(self, value):
        self._label_type = value

    def generate(self):
        if self._label_content in (LabelContent.QRCODE_ONLY, LabelContent.TEXT_QRCODE):
            img = self._generate_qr()
        elif self._label_content in (LabelContent.IMAGE_BW, LabelContent.IMAGE_GRAYSCALE):
            img = self._image
        else:
            img = None

        if img is not None:
            img_width, img_height = img.size
        else:
            img_width, img_height = (0, 0)

        if self._label_content in (LabelContent.TEXT_ONLY, LabelContent.TEXT_QRCODE):
            if self._label_orientation == LabelOrientation.STANDARD:
                if self._shrink_or_wrap == 'wrap':
                    self.text = self._wrap_text()
                elif self._shrink_or_wrap == 'shrink':
                    self._font_size = self._scale_text()
            textsize = self._get_text_size()
        else:
            textsize = (0, 0, 0, 0)

        width, height = self._width, self._height
        margin_left, margin_right, margin_top, margin_bottom = self._label_margin

        if self._label_orientation == LabelOrientation.STANDARD:
            if self._label_type in (LabelType.ENDLESS_LABEL,):
                height = img_height + textsize[3] - textsize[1] + margin_top + margin_bottom
        elif self._label_orientation == LabelOrientation.ROTATED:
            if self._label_type in (LabelType.ENDLESS_LABEL,):
                width = img_width + textsize[2] + margin_left + margin_right

        if self._label_orientation == LabelOrientation.STANDARD:
            if self._label_type in (LabelType.DIE_CUT_LABEL, LabelType.ROUND_DIE_CUT_LABEL):
                vertical_offset_text = (height - img_height - textsize[3])//2
                vertical_offset_text += (margin_top - margin_bottom)//2
            else:
                vertical_offset_text = margin_top

            vertical_offset_text += img_height
            horizontal_offset_text = max((width - textsize[2])//2, 0)
            horizontal_offset_image = (width - img_width)//2
            vertical_offset_image = margin_top

        elif self._label_orientation == LabelOrientation.ROTATED:
            vertical_offset_text = (height - textsize[3])//2
            vertical_offset_text += (margin_top - margin_bottom)//2
            if self._label_type in (LabelType.DIE_CUT_LABEL, LabelType.ROUND_DIE_CUT_LABEL):
                horizontal_offset_text = max((width - img_width - textsize[2])//2, 0)
            else:
                horizontal_offset_text = margin_left
            horizontal_offset_text += img_width
            horizontal_offset_image = margin_left
            vertical_offset_image = (height - img_height)//2

        text_offset = horizontal_offset_text, vertical_offset_text - textsize[1]
        image_offset = horizontal_offset_image, vertical_offset_image

        imgResult = Image.new('RGB', (int(width), int(height)), 'white')

        if img is not None:
            imgResult.paste(img, image_offset)

        if self._label_content in (LabelContent.TEXT_ONLY, LabelContent.TEXT_QRCODE):
            draw = ImageDraw.Draw(imgResult)
            draw.multiline_text(
                text_offset,
                self._prepare_text(self._text),
                self._fore_color,
                font=self._get_font(),
                align=self._text_align,
                spacing=int(self._font_size*((self._line_spacing - 100) / 100)))

        return imgResult

    def _generate_qr(self):
        qr = QRCode(
            version=1,
            error_correction=self._qr_correction,
            box_size=self._qr_size,
            border=0,
        )
        qr.add_data(self._text.encode("utf-8-sig"))
        qr.make(fit=True)
        qr_img = qr.make_image(
            fill_color='red' if (255, 0, 0) == self._fore_color else 'black',
            back_color="white")
        return qr_img

    def _get_text_size(self):
        font = self._get_font()
        img = Image.new('L', (20, 20), 'white')
        draw = ImageDraw.Draw(img)
        return draw.multiline_textbbox(
            (0, 0),
            self._prepare_text(self._text),
            font=font,
            align=self._text_align,
            spacing=int(self._font_size*((self._line_spacing - 100) / 100)))

    @staticmethod
    def _prepare_text(text):
        # workaround for a bug in multiline_textsize()
        # when there are empty lines in the text:
        lines = []
        for line in text.split('\n'):
            if line == '':
                line = ' '
            lines.append(line)
        return '\n'.join(lines)

    def _wrap_text(self):
        lines = []
        for line in self._prepare_text(self.text).split('\n'):
            line_width = self._get_font().getsize(line)[0]
            max_char = floor(self._width/(line_width/len(line)))-2
            line = textwrap.fill(line, width=max_char)
            lines.append(line)
        return '\n'.join(lines)

    def _scale_text(self):
        font_size = self._font_size

        if self._label_type in (LabelType.DIE_CUT_LABEL, LabelType.ROUND_DIE_CUT_LABEL):
            font = ImageFont.truetype(self._font_path, font_size)
            img = Image.new('L', (20, 20), 'white')
            draw = ImageDraw.Draw(img)
            text_height = draw.multiline_textsize(
                self._prepare_text(self._text),
                font=font,
                spacing=int(self._font_size*((self._line_spacing-100)/100)))[1]

            while text_height > self._height:
                font_size -= 1
                font = ImageFont.truetype(self._font_path, font_size)
                text_height = draw.multiline_textsize(
                    self._prepare_text(self._text),
                    font=font,
                    spacing=int(self._font_size*((self._line_spacing-100)/100)))[1]

        for line in self.text.strip().split('\n'):
            font = ImageFont.truetype(self._font_path, font_size)
            line_width = font.getsize(line)[0]
            while line_width > self._width:
                font_size -= 1
                font = ImageFont.truetype(self._font_path, font_size)
                line_width = font.getsize(line)[0]

        return font_size

    def _get_font(self):
        return ImageFont.truetype(self._font_path, self._font_size)
