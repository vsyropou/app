import importlib

import mlflow


def run():
    # TODO: make this a proper pipeline runner given a yaml file.

    import argparse

    parser = argparse.ArgumentParser()

    module_name = parser.add_argument("module")
    func = parser.add_argument("func")

    data_path = parser.add_argument("data")
    params_path = parser.add_argument("params")

    tracking_uri = parser.add_argument("tracking_uri")
    experiment_name = parser.add_argument("experiment_name")

    args = parser.parse_args()

    module = importlib.import_module(module_name)

    model = getattr(module, "Model")()

    func = getattr(model, args["func"])

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run() as run:
        run_id = run.info.run_id

        data = mlflow.download_artifact(run_id=run_id, artifact_path=data_path)
        params = mlflow.download_artifact(run_id=run_id, artifact_path=params_path)

        func(data=data, params=params)


if __name__ == "__main__":
    run()
