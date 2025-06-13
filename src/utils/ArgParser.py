# src/utils/ArgParser.py

import argparse


class ArgumentParser:
    @staticmethod
    def parse_args(prog:str=None, description: str=None, epilog:str=None):
        """
        Define Arg parser

        Args:
        - prog: Program Name
        - description: What it does
        - epilog:  Text art the bottom of the help
        """

        parser = argparse.ArgumentParser(prog = prog,
                                         description = description,
                                         epilog = epilog)


        parser.add_argument(
            "-sp", "--skip-proxy",
            action = "store_true",
            help="Skip the proxy connection test, not recommended.",
        )

        args = parser.parse_args()
        return args