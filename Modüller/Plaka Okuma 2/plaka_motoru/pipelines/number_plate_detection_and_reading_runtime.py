from .number_plate_detection_and_reading import NumberPlateDetectionAndReading
from plaka_motoru.pipelines.base import RuntimePipeline


class NumberPlateDetectionAndReadingRuntime(NumberPlateDetectionAndReading, RuntimePipeline):
    """
    Number Plate Detection and reading runtime
    """

    def __init__(self, *args, **kwargs):
        NumberPlateDetectionAndReading.__init__(self, *args, **kwargs)
        RuntimePipeline.__init__(self, self.pipelines)
