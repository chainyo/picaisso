# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

import asyncio
import functools
from collections import OrderedDict
from typing import Union

import numpy as np
import tomesd
import torch
from diffusers.pipelines import DiffusionPipeline
from loguru import logger
from torch import autocast


# Torch optimizations for inference
torch.backends.cudnn.benchmark = True
torch.backends.cuda.matmul.allow_tf32 = True

DTYPE_MAPPING = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}
TASK_MAPPING = OrderedDict(
    [
        ("image_to_image", "StableDiffusionImg2ImgPipeline"),
        ("inpaint", "StableDiffusionInpaintPipeline"),
        ("super_resolution", "StableUpscalePipeline"),
        ("text_to_image", "StableDiffusionPipeline"),
    ]
)

TASK_INPUT_MAPPING = OrderedDict(
    [
        ("image_to_image", ("image", "prompt")),
        ("inpaint", ("image")),
        ("super_resolution", ("image")),
        ("text_to_image", ("prompt")),
    ]
)


class AutoService:
    """Automatic mapping of tasks to services."""

    def __init__(
        self,
        model_name: str,
        task: str,
        dtype: str,
        n_steps: int,
        max_batch_size: int,
        max_wait: int,
    ) -> None:
        """
        Initialize the service with the given parameters and the task.

        Args:
            model_name (str): The model name to use.
            task (str): The task to perform. Must be one of the keys of TASK_MAPPING.
            dtype (str): The dtype to use. Must be one of "fp32", "fp16" or "bf16".
            n_steps (int): The number of steps to use.
            max_batch_size (int): The maximum batch size to use.
            max_wait (int): The maximum time to wait before processing the batch.

        Raises:
            ValueError: If the task is not supported.
        """
        if task not in TASK_MAPPING.keys():
            raise ValueError(f"Task {task} is not supported. Must be one of {list(TASK_MAPPING.keys())}.")
        else:
            self.task = task
            self.input_names = TASK_INPUT_MAPPING[task]

        self.model = model_name
        self.dtype = DTYPE_MAPPING[dtype]
        self.n_steps = n_steps
        self.max_batch_size = max_batch_size
        self.max_wait = max_wait

        # Multi requests support
        self.queue = []
        self.queue_lock = None
        self.needs_processing = None
        self.needs_processing_timer = None

        assert torch.cuda.is_available(), "CUDA is not available"
        self.pipeline = self.import_pipeline()
        self.pipeline.to("cuda:0")
        tomesd.apply_patch(self.pipeline, ratio=0.5)

    def import_pipeline(self) -> DiffusionPipeline:
        """Import the pipeline from the task.

        The task is used to determine the pipeline name,
        e.g. task = "text_to_image" -> pipeline_name = "StableDiffusionPipeline"

        Args:
            task (str): The task to perform. Must be one of the keys of TASK_MAPPING.
            model (str): The model name to use.
            dtype (torch.dtype): The torch dtype to use.

        Returns:
            DiffusionPipeline: The pipeline to use from the diffusers library.

        Raises:
            ValueError: If the task is not supported.
        """
        diffusers_module = __import__("diffusers")

        pipeline = getattr(diffusers_module, TASK_MAPPING[self.task]).from_pretrained(
            self.model, torch_dtype=self.dtype
        )

        return pipeline

    def schedule_processing_if_needed(self):
        if len(self.queue) >= self.max_batch_size:
            self.needs_processing.set()
        elif self.queue:
            self.needs_processing_timer = asyncio.get_event_loop().call_at(
                self.queue[0]["time"] + self.max_wait, self.needs_processing.set
            )

    async def process_input(self, **kwargs) -> Union[str, np.ndarray]:
        """Process the input and wait for the result before returning.

        Args:
            **kwargs: The inputs to the task. Must match the task input names.

        Returns:
            str: The result of the task.
        """
        our_task = {
            "done_event": asyncio.Event(),
            "time": asyncio.get_event_loop().time(),
        }

        for input_name in self.input_names:
            our_task[input_name] = kwargs[input_name]

        async with self.queue_lock:
            self.queue.append(our_task)
            self.schedule_processing_if_needed()

        await our_task["done_event"].wait()

        return our_task["result"]

    async def runner(self):
        """Process the queue."""
        self.queue_lock = asyncio.Lock()
        self.needs_processing = asyncio.Event()
        while True:
            await self.needs_processing.wait()
            self.needs_processing.clear()
            if self.needs_processing_timer is not None:
                self.needs_processing_timer.cancel()
                self.needs_processing_timer = None

            async with self.queue_lock:
                if self.queue:
                    longest_wait = asyncio.get_event_loop().time() - self.queue[0]["time"]
                    logger.debug(f"Processing batch of {len(self.queue)} requests, longest wait: {longest_wait}")
                else:
                    longest_wait = None
                input_batch = self.queue[: self.max_batch_size]
                del self.queue[: self.max_batch_size]
                self.schedule_processing_if_needed()

            try:
                batch = {input_name: [inp[input_name] for inp in input_batch] for input_name in self.input_names}
                results = await asyncio.get_event_loop().run_in_executor(
                    None, functools.partial(self.inference, batch)
                )

                for task, result in zip(input_batch, results.images):
                    task["result"] = result
                    task["done_event"].set()
                del prompt_batch

            except Exception as e:
                logger.error(e)

    def inference(self, n_samples: int = 1, **kwargs) -> np.ndarray:
        """
        Inference on the given inputs.

        Args:
            n_samples (int): The number of samples to generate.
            **kwargs: The inputs to the task. Must match the task input names. Can be a batch.

        Returns:
            np.ndarray: The result of the batched inference.
        """
        with autocast("cuda"):
            return self.pipeline(
                **kwargs,
                num_images_per_prompt=n_samples,
                num_inference_steps=self.n_steps,
                output_type="numpy",
            )
