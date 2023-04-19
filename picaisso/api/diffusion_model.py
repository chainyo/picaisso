# Copyright (c) 2023, Thomas Chaigneau. All rights reserved.

import asyncio
import functools
import numpy as np
from loguru import logger

from diffusers import StableDiffusionPipeline

import torch
from torch import autocast
torch.backends.cudnn.benchmark = True
torch.backends.cuda.matmul.allow_tf32 = True

from config import settings

class DiffusionService():
    def __init__(
        self,
        model: str = "prompthero/openjourney",
        dtype: torch.dtype = torch.float16,
        n_steps: int = 50,
    ):
        self.model = model
        self.dtype = dtype
        self.n_steps = n_steps
        self.max_batch_size = settings.max_batch_size
        self.max_wait = settings.max_wait
        
        # Multi requests support
        self.queue = []
        self.queue_lock = None
        self.needs_processing = None
        self.needs_processing_timer = None
        
        assert torch.cuda.is_available(), "CUDA is not available"
        self.pipeline = StableDiffusionPipeline.from_pretrained(self.model, torch_dtype=self.dtype)
        self.pipeline.to("cuda:0")
    
    
    def schedule_processing_if_needed(self):
        if len(self.queue) >= self.max_batch_size:
            self.needs_processing.set()
        elif self.queue:
            self.needs_processing_timer = asyncio.get_event_loop().call_at(
                self.queue[0]["time"] + self.max_wait, self.needs_processing.set
            )
            
    
    async def process_input(self, prompt: str) -> str:
        """Process the input and return the result."""
        our_task = {
            "done_event": asyncio.Event(loop=asyncio.get_event_loop()),
            "prompt": prompt,
            "time": asyncio.get_event_loop().time(),
        }
        async with self.queue_lock:
            self.queue.append(our_task)
            self.schedule_processing_if_needed()
            
        await our_task["done_event"].wait()
        return our_task["result"]
    
    
    async def runner(self):
        """Process the queue."""
        self.queue_lock = asyncio.Lock(loop=asyncio.get_event_loop())
        self.needs_processing = asyncio.Event(loop=asyncio.get_event_loop())
        while True:
            await self.needs_processing.wait()
            self.needs_processing.clear()
            if self.needs_processing_timer is not None:
                self.needs_processing_timer.cancel()
                self.needs_processing_timer = None
                
            async with self.queue_lock:
                if self.queue:
                    longest_wait = asyncio.get_event_loop().time() - self.queue[0]["time"]
                else:
                    longest_wait = None
                prompt_batch = self.queue[:self.max_batch_size]
                del self.queue[:self.max_batch_size]
                self.schedule_processing_if_needed()
                
            try:
                batch = [prompt["prompt"] for prompt in prompt_batch]
                results = await asyncio.get_event_loop().run_in_executor(
                    None, functools.partial(self.inference, batch)
                )
                for task, result in zip(prompt_batch, results.images):
                    task["result"] = result
                    task["done_event"].set()
                del prompt_batch
            except Exception as e:
                logger.error(e)


    def inference(self, prompt: str, n_samples: int = 1) -> np.ndarray:
        with autocast("cuda"):
            return self.pipeline(
                prompt, num_images_per_prompt=n_samples, num_inference_steps=self.n_steps, output_type="numpy"
            )