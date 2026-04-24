"""pipeline construct module

Examples:
    >>> from plaka_motoru import pipeline
    >>> from plaka_motoru.tools import unzip
    >>> number_plate_detection_and_reading = pipeline("number_plate_detection_and_reading", image_loader="opencv")
    >>> results = number_plate_detection_and_reading(['./data/examples/oneline_images/example1.jpeg', './data/examples/oneline_images/example2.jpeg'])
    >>> (images, images_bboxs, images_points, images_zones, region_ids,region_names, count_lines, confidences, texts) = unzip(results)
    >>> print(texts)
    (['AC4921CB'], ['RP70012', 'JJF509'])

The module contains the following functions:

- `check_task(task)` - Returns task options if task supported? else raise KeyError.
- `pipeline(task, image_loader, pipeline_kwargs, **kwargs)` - Returns Pipeline task object.
"""
from typing import Any, Dict, Optional, Union

from plaka_motoru.pipelines.base \
    import Pipeline
from plaka_motoru.image_loaders \
    import BaseImageLoader
from plaka_motoru.pipelines.number_plate_localization \
    import NumberPlateLocalization
from plaka_motoru.pipelines.number_plate_filling \
    import NumberPlateFilling
from plaka_motoru.pipelines.number_plate_classification \
    import NumberPlateClassification
from plaka_motoru.pipelines.number_plate_text_reading \
    import NumberPlateTextReading
from plaka_motoru.pipelines.number_plate_detection_and_reading \
    import NumberPlateDetectionAndReading
from plaka_motoru.pipelines.number_plate_detection_and_reading_runtime \
    import NumberPlateDetectionAndReadingRuntime


SUPPORTED_TASKS = {
    "number_plate_localization": {
        "impl": NumberPlateLocalization,
    },
    "number_plate_filling": {
        "impl": NumberPlateFilling
    },
    "number_plate_classification": {
        "impl": NumberPlateClassification
    },
    "number_plate_text_reading": {
        "impl": NumberPlateTextReading
    },
    "number_plate_detection_and_reading": {
        "impl": NumberPlateDetectionAndReading
    },
    "number_plate_detection_and_reading_runtime": {
        "impl": NumberPlateDetectionAndReadingRuntime
    },
}


def check_task(task: str) -> Dict:
    """
    check task in SUPPORTED_TASKS
    Args:
        task (): task name.

    Returns:
        :Dict: Task options
    """
    if task in SUPPORTED_TASKS:
        targeted_task = SUPPORTED_TASKS[task]
        return targeted_task

    raise KeyError(f"Unknown task {task}, available tasks are {SUPPORTED_TASKS.keys()}")


def pipeline(
    task: str = None,
    image_loader: Optional[Union[str, BaseImageLoader]] = None,
    pipeline_kwargs: Dict[str, Any] = None,
    **kwargs,
) -> Pipeline:
    """
    Args:
        task (): pipelines name.
        image_loader (): image loader name
        pipeline_kwargs (): pipeline kwargs
        kwargs (): kwargs

    Returns:
        :class:`~Pipeline`: A suitable pipeline for the task.

    Avaliable tasks:
        - [multiline_number_plate_detection_and_reading_runtime](pipelines/multiline_number_plate_detection_and_reading_runtime.md)
        - [number_plate_short_detection_and_reading](pipelines/number_plate_short_detection_and_reading.md)
        - [number_plate_localization](pipelines/number_plate_localization.md)
        - [number_plate_bbox_filling](pipelines/number_plate_bbox_filling.md)
        - [number_plate_key_points_detection](pipelines/number_plate_key_points_detection.md)
        - [number_plate_key_points_filling](pipelines/number_plate_key_points_filling.md)
        - [number_plate_classification](pipelines/number_plate_classification.md)
        - [number_plate_text_reading](pipelines/number_plate_text_reading.md)
        - [number_plate_detection_and_reading_v2](pipelines/number_plate_detection_and_reading_v2.md)
        - [number_plate_detection_and_reading_runtime_v2](pipelines/number_plate_detection_and_reading_runtime_v2.md)
        - [number_plate_detection_and_reading](pipelines/number_plate_detection_and_reading.md)
        - [number_plate_detection_and_reading_runtime](pipelines/number_plate_detection_and_reading_runtime.md)

    Examples:
        >>> from plaka_motoru import pipeline
        >>> from plaka_motoru.tools import unzip
        >>> number_plate_detection_and_reading = pipeline("number_plate_detection_and_reading", image_loader="opencv")
        >>> results = number_plate_detection_and_reading(['./data/examples/oneline_images/example1.jpeg', './data/examples/oneline_images/example2.jpeg'])
        >>> (images, images_bboxs, images_points, images_zones, region_ids,region_names, count_lines, confidences, texts) = unzip(results)
        >>> print(texts)
        (['AC4921CB'], ['RP70012', 'JJF509'])
    """
    if pipeline_kwargs is None:
        pipeline_kwargs = {}

    if task is None:
        raise RuntimeError(
            "Impossible to instantiate a pipeline without either a task"
            "being specified."
            "Please provide a task class"
        )

    # Retrieve the task
    targeted_task = check_task(task)
    pipeline_class = targeted_task["impl"]

    return pipeline_class(task, image_loader, **pipeline_kwargs, **kwargs)
