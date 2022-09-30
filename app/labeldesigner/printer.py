from brother_ql.backends import backend_factory, guess_backend
from brother_ql import BrotherQLRaster, create_label
from .label import LabelOrientation, LabelType, LabelContent


class PrinterQueue:

    _printQueue = []
    _cutQueue = []

    def __init__(
            self,
            model,
            device_specifier,
            label_size):
        self.model = model
        self.device_specifier = device_specifier
        self.label_size = label_size

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    @property
    def device_specifier(self):
        return self._device_specifier

    @device_specifier.setter
    def device_specifier(self, value):
        self._device_specifier = value
        selected_backend = guess_backend(self._device_specifier)
        self._backend_class = backend_factory(
            selected_backend)['backend_class']

    @property
    def label_size(self):
        return self._label_size

    @label_size.setter
    def label_size(self, value):
        self._label_size = value

    def add_label_to_queue(self, label, count, cut_mode='cut'):
        for cnt in range(0, count):
            if cut_mode == 'cut':
                cut = True
            elif cut_mode == 'cut_once' and cnt == count:
                cut = True
            else:
                cut = False

            self._printQueue.append(
                {'label': label,
                 'cut': cut
                 })

    def process_queue(self):
        qlr = BrotherQLRaster(self._model)

        for queue_entry in self._printQueue:
            if queue_entry['label'].label_type == LabelType.ENDLESS_LABEL:
                if queue_entry['label'].label_orientation == LabelOrientation.STANDARD:
                    rotate = 0
                else:
                    rotate = 90
            else:
                rotate = 'auto'

            img = queue_entry['label'].generate()

            if queue_entry['label'].label_content == LabelContent.IMAGE_GRAYSCALE: 
                dither = True
            else:
                dither = False

            create_label(
                qlr,
                img,
                self.label_size,
                red='red' in self.label_size,
                dither=dither,
                cut=queue_entry['cut'],
                rotate=rotate)

        self._printQueue.clear()

        be = self._backend_class(self._device_specifier)
        be.write(qlr.data)
        be.dispose()
        del be
