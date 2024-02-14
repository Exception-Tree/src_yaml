import argparse

from report import SimpleReportCreatorCallback
from srcyaml import SimpleReportCreatorYaml


class CMD(SimpleReportCreatorCallback):
    def progress(self, caption: str, position: int):
        raise NotImplementedError

    def warning(self, text: str) -> bool:
        raise NotImplementedError

    def error(self, text: str) -> bool:
        """
        Get error message from SRC
        :param text:
        :return: True if you need stop process
        """
        raise NotImplementedError

    def message(self, text: str):
        """
        Get message from SRC
        :param text:
        :return: None
        """
        raise NotImplementedError

    def exception(self, ex: Exception) -> bool:
        """
        Get exception from SRC
        :param ex:
        :return: True if you need stop process
        """
        raise NotImplementedError


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', type=str, required=True, help="load")
    args = parser.parse_args()

    callback = CMD()
    loader = SimpleReportCreatorYaml(callback)
    loader.load(args.filename)
