import optuna

from ab.nn.util.Exception import *
from ab.nn.util.Train import optuna_objective
from ab.nn.util.Util import *
from ab.nn.util.db.Calc import patterns_to_configs
from ab.nn.util.db.Read import remaining_trials


def main(config: str | tuple = default_config, n_epochs: int = default_epochs,
         n_optuna_trials: int | str = default_trials,
         min_batch_binary_power: int = default_min_batch_power, max_batch_binary_power: int = default_max_batch_power,
         min_learning_rate: float = default_min_lr, max_learning_rate: float = default_max_lr,
         min_momentum: float = default_min_momentum, max_momentum: float = default_max_momentum,
         transform: str | tuple = None, nn_fail_attempts: int = default_nn_fail_attempts, random_config_order:bool = default_random_config_order):
    """
    Main function for training models using Optuna optimization.
    :param config: Configuration specifying the model training pipelines. The default value for all configurations.
    :param n_epochs: Number of training epochs.
    :param n_optuna_trials: The total number of Optuna trials the model should have. If negative, its absolute value represents the number of additional trials.
    :param min_batch_binary_power: Minimum power of two for batch size. E.g., with a value of 0, batch size equals 2**0 = 1.
    :param max_batch_binary_power: Maximum power of two for batch size. E.g., with a value of 12, batch size equals 2**12 = 4096.
    :param min_learning_rate: Minimum value of learning rate.
    :param max_learning_rate: Maximum value of learning rate.
    :param min_momentum: Minimum value of momentum.
    :param max_momentum: Maximum value of momentum.
    :param transform: The transformation algorithm name. If None (default), all available algorithms are used by Optuna.
    :param nn_fail_attempts: Number of attempts if the neural network model throws exceptions.
    :param random_config_order: If random shuffling of the config list is required.
    """

    validate_prm(min_batch_binary_power, max_batch_binary_power, min_learning_rate, max_learning_rate, min_momentum, max_momentum)

    # Determine configurations based on the provided config
    sub_configs = patterns_to_configs(config, random_config_order)
    if transform:
        transform = transform if isinstance(transform, (tuple, list)) else (transform,)
    print(f"Training configurations ({n_epochs} epochs):")
    for idx, sub_config_str in enumerate(sub_configs, start=1):
        print(f"{idx}. {sub_config_str}")
    for sub_config_str in sub_configs:
            task, dataset_name, metric, model_name = sub_config = conf_to_names(sub_config_str)
            trials_file = model_stat_dir(sub_config) / f'{n_epochs}.json'
            n_optuna_trials_left, n_passed_trials = remaining_trials(trials_file, model_name, n_optuna_trials)
            n_expected_trials = n_optuna_trials_left + n_passed_trials
            if n_optuna_trials_left == 0:
                print(f"The model {model_name} has already passed all trials for task: {task}, dataset: {dataset_name},"
                      f" metric: {metric}, epochs: {n_epochs}")
            else:
                print(f"\nStarting training for the model: {model_name}, task: {task}, dataset: {dataset_name},"
                      f" metric: {metric}, epochs: {n_epochs}")
                fail_iterations = nn_fail_attempts
                continue_study = True
                max_batch_binary_power_local = max_batch_binary_power
                while (continue_study and max_batch_binary_power_local >= min_batch_binary_power and fail_iterations > -1
                       and remaining_trials(trials_file, model_name, n_expected_trials)[0] > 0):
                    continue_study = False
                    try:
                        # Launch Optuna for the current NN model
                        study = optuna.create_study(study_name=model_name, direction='maximize')

                        # Configure Optuna for the current model
                        def objective(trial):
                            nonlocal continue_study, fail_iterations, max_batch_binary_power_local
                            try:
                                accuracy = optuna_objective(trial, sub_config, min_learning_rate, max_learning_rate, min_momentum, max_momentum,
                                                        min_batch_binary_power, max_batch_binary_power_local, transform, fail_iterations, n_epochs)
                                fail_iterations = nn_fail_attempts
                                return accuracy
                            except Exception as e:
                                print(f"Optuna: exception in objective function: {e}")
                                continue_study = True
                                if isinstance(e, CudaOutOfMemory):
                                    raise e
                                if isinstance(e, ModelException):
                                    fail_iterations -= 1
                                return 0.0

                        study.optimize(objective, n_trials=n_optuna_trials_left)
                    except CudaOutOfMemory as e:
                        max_batch_binary_power_local = e.batch_size_power() - 1
                        print(f"Max batch is decreased to {max_batch(max_batch_binary_power_local)} due to a CUDA Out of Memory Exception for model '{model_name}'")
                    finally:
                        del study
                        release_memory()


if __name__ == "__main__":
    a = args()
    main(
        a.config, a.epochs, a.trials, a.min_batch_binary_power, a.max_batch_binary_power,
        a.min_learning_rate, a.max_learning_rate, a.min_momentum, a.max_momentum, a.transform,
        a.nn_fail_attempts, a.random_config_order
    )
