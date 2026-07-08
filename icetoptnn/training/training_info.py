"""
    Trained model structure
"""

from pathlib import Path;

import yaml;

class TrainedModelInfo(yaml.YAMLObject):
    """
        Information about a model and how it was trained
    """

    yaml_tag='!tnn/model_info';


    seed_split: int;
    """Seed used to split the dataset"""


    split_training: float;
    """Portion of events used for training"""
    
    split_validation: float;
    """Portion of events used for validation"""

    split_testing: float;
    """Portion of events used for testing"""


    datasets: list[Path];
    """Datasets used to train the model"""


    vset_features: list[str];
    """Features used in training"""

    vset_truth: list[str];
    """Truth used in training"""

