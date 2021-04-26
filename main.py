import argparse
import os
import sys

from pathlib import Path

from gooey import Gooey


class StarMasher():

    def __init__(self):
        self.parser = self.parse_arguments()
        self.set_arguments(self.parser)

    def parse_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-i', '--input', nargs='+', required=True, help='Input star file')
        parser.add_argument('-o', '--output', required=True, help='Output star file with modifications')
        parser.args = parser.parse_args()
        return parser

    def set_arguments(self, parser): 
        #required arguments -- input
        a = parser.args #me == lazy
        if isinstance(a.input, str):
            try:
                assert Path(a.input).exists()
                self.input_star = Path(a.input)
            except (AssertionError, TypeError) as e:
                sys.exit(f'The path {a.input} does not exist or is not a valid path')
        else:
            self.input_star = [Path(f) for f in a.input]
            for f in self.input_star:
                try:
                    assert f.exists()
                except AssertionError:
                    sys.exit(f'The file {f} does not exist')
            try:
                assert len(self.input_star) == 2
            except AssertionError:
                sys.exit(f'Please give a maximum of two iput star files')
        #required arguments -- output
        try:
            self.output_star = Path(a.output)
            assert Path(a.output).parent.exists()
        except (AssertionError) as e:
            sys.exit(f'Cannot create the star file {a.output}. Does the folder exist?')
        except TypeError as e:
            sys.exit(f'{a.output} does not seem to be a valid name for a file')

@Gooey
def main():
    import sys
    sys.argv = 'main.py --input star1.star star2.star -o out.star'.split()
    work_folder = Path(r'F:\Users\Cthulhu\Documents\workspace\Starfile')
    os.chdir(work_folder)
    masher = StarMasher()

if __name__ == '__main__':
    main()