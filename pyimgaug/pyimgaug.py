from __future__ import print_function, division
from abc import ABCMeta, abstractmethod
import random
import numpy as np
import copy

try:
    xrange
except NameError:  # python3
    xrange = range

def is_np_array(val):
    return isinstance(val, (np.ndarray, np.generic))

def current_random_state():
    return np.random

def new_random_state(seed=None):
    if seed is None:
        # sample manually a seed instead of just RandomState(), because the latter one
        # is way slower.
        return np.random.RandomState(np.random.randint(0, 10**6, 1)[0])
    else:
        return np.random.RandomState(seed)

def dummy_random_state():
    return np.random.RandomState(1)

def copy_random_state(random_state, force_copy=False):
    if random_state == np.random and not force_copy:
        return random_state
    else:
        rs_copy = dummy_random_state()
        rs_copy.set_state(random_state.get_state())
        return rs_copy

def from_json(json_str):
    #TODO
    pass

class AugJob(object):
    def __init__(self, images, routes=None, preprocessor=None, postprocessor=None, deactivator=None, random_state=None, track_history=False, history=None):
        self.images = images
        self.routes = routes if routes is not None else []
        self.preprocessor = preprocessor
        self.postprocessor = postprocessor
        self.deactivator = deactivator
        self.random_state = random_state
        self.track_history = track_history
        self.history = history if history is not None else []

    @property
    def nb_images(self):
        return self.images.shape[0]

    @property
    def height(self):
        return self.images.shape[1]

    @property
    def width(self):
        return self.images.shape[2]

    @property
    def nb_channels(self):
        return self.images.shape[3]

    def add_to_history(self, augmenter, changes, before, after):
        if self.track_history:
            self.history.append((augmenter, changes, np.copy(before), np.copy(after)))

    def copy(self, images=None):
        job = copy.copy(self)
        if images is not None:
            job.images = images
        return job

    def deepcopy(self, images=None):
        job = copy.deepcopy(self)
        if images is not None:
            job.images = images
        return job

class BackgroundAugmenter(object):
    def __init__(self, image_source, augmenter, maxlen, nb_workers=1):
        self.augmenter = augmenter
        self.maxlen = maxlen
        self.result_queue = multiprocessing.Queue(maxlen)
        self.batch_workers = []
        for i in range(nb_workers):
            worker = multiprocessing.Process(target=self._augment, args=(image_source, augmenter, self.result_queue))
            worker.daemon = True
            worker.start()
            self.batch_workers.append(worker)

    def join(self):
        for worker in self.batch_workers:
            worker.join()

    def get_batch(self):
        return self.result_queue.get()

    def _augment(self, image_source, augmenter, result_queue):
        batch = next(image_source)
        self.result_queue.put(augmenter.transform(batch))