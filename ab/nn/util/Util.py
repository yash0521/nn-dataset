import argparse
import math
from os.path import exists, join
from pathlib import Path

import ab.nn.util.Const as Const
from ab.nn.util.Const import *


def nn_mod(*nms):
    return ".".join(to_nn + nms)

def get_attr (mod, f):
    return getattr(__import__(nn_mod(mod), fromlist=[f]), f)


def conf_to_names(c: str) -> list[str]:
    return c.split('-')


def is_full_config(s: str):
    l = conf_to_names(s)
    return 4 == len(l) and exists(join(Const.dataset_dir_global, l[-1] + '.py'))


def define_global_paths():
    """
    Defines project paths from current directory.
    """
    stat_dir = 'stat'

    import ab.nn.__init__ as init_file
    pref = Path(init_file.__file__).parent.absolute()
    Const.stat_dir_global = join(pref, stat_dir)
    Const.dataset_dir_global = join(pref, 'dataset')

    Const.data_dir_global = 'data'
    Const.db_dir_global = join('db', 'ab.nn.db')
    if exists(stat_dir):
        project_root = ['..'] * len(to_nn)
        Const.data_dir_global = join(*project_root, Const.data_dir_global)
        Const.db_dir_global = join(*project_root, Const.db_dir_global)

def max_batch (binary_power):
    return 2 ** binary_power


class CudaOutOfMemory(Exception):
    def __init__(self, batch):
        self.batch_power = int(math.log2(batch))

    def batch_size_power(self):
        return self.batch_power

def args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, default=default_config,
                        help="Configuration specifying the model training pipelines. The default value for all configurations.")
    parser.add_argument('-e', '--epochs', type=int, default=default_epochs,
                        help="Numbers of training epochs")
    parser.add_argument('-t', '--trials', type=int, default=default_trials,
                        help="Number of Optuna trials")
    parser.add_argument('--min_batch_binary_power', type=int, default=default_min_batch_power,
                        help="Minimum power of two for batch size. E.g., with a value of 0, batch size equals 2**0 = 1.")
    parser.add_argument('-b', '--max_batch_binary_power', type=int, default=default_max_batch_power,
                        help="Maximum power of two for batch size. E.g., with a value of 12, batch size equals 2**12 = 2048.")
    parser.add_argument('--min_learning_rate', type=float, default=default_min_lr,
                        help="Minimum value of learning rate.")
    parser.add_argument('-l', '--max_learning_rate', type=float, default=default_max_lr,
                        help="Maximum value of learning rate.")
    parser.add_argument('--min_momentum', type=float, default=default_min_momentum,
                        help="Minimum value of momentum.")
    parser.add_argument('-m', '--max_momentum', type=float, default=default_max_momentum,
                        help="Maximum value of momentum.")
    parser.add_argument('-f', '--transform', type=str, default=default_transform,
                        help="The transformation algorithm name. If None (default), all available algorithms are used by Optuna.")
    return parser.parse_args()


