#!/usr/bin/python3
import argparse
import re
import os
import tempfile
import shutil
try:
    from commands import getstatusoutput
except ImportError:
    from subprocess import getstatusoutput

JPG_OPT = '-sampling-factor 4:2:0 -strip -quality 85 -interlace JPEG -colorspace sRGB'
PNG_OPT = '-strip'
LARGE_FILE_THRESHOLD = 100000

class ImageOptApp(object):
    image_re = re.compile('\.jpg$|\.png$|\.jpeg$')
    tempdir = None

    # TODO: Add an option to flag large files (>100kb)
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Batch optimise images')
        parser.add_argument('-i', dest='input',
                            help='Input to process.  Can be a list in a file, an input directory to scan or an individual file',
                            required=True)
        parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False)
        parser.add_argument('--parse-urls', dest='parse_urls', action='store_true', default=False)
        parser.add_argument('--flag-large', dest='flag_large', action='store_true', default=False)
        return parser.parse_args()

    def run(self):
        self.args = self.parse_args()

        file_list = self.get_file_list(self.args.input)

        self.tempdir = tempfile.mkdtemp()
        print('Using temporary directory .. %s' % (self.tempdir))
        try:
            for fn in file_list:
                self.optimise(self.prep_fn(fn), self.args.dry_run)
        finally:
            # print('Cleaning up %s' % (self.tempdir))
            shutil.rmtree(self.tempdir)

        if self.args.flag_large:
            print('LARGE FILES:')
            for fn in file_list:
                fn = self.prep_fn(fn)
                size = os.path.getsize(fn)
                if size > LARGE_FILE_THRESHOLD:
                    print('%s,%s' % (fn, size))

    def prep_fn(self, fn):
        if self.args.parse_urls:
            return re.sub('%20', ' ', fn)
        return fn

    def get_file_list(self, path):
        if os.path.isdir(path):
            return [os.path.join(path, fn) for fn in os.listdir(path) if os.path.isfile(os.path.join(path, fn))]
        elif os.path.isfile(path):
            if self.image_re.search(path.lower()):
                return [path]
            else:
                with open(path, 'r') as f:
                    return [line.strip() for line in f if self.image_re.search(line.strip().lower())]

        raise Exception('Unknown input type')

    def optimise(self, fn, dry_run=False):
        out_fn = os.path.join(self.tempdir, os.path.basename(fn))

        if re.search('\.png$', fn):
            cmd = 'convert "%s" %s "%s"' % (fn, PNG_OPT, out_fn)
        else:
            cmd = 'convert "%s" %s "%s"' % (fn, JPG_OPT, out_fn)

        status, output = getstatusoutput(cmd)
        if status != 0:
            raise Exception('ERROR: Failed to optimise %s - %s' % (fn, output))

        fn_size = os.path.getsize(fn)
        out_fn_size = os.path.getsize(out_fn)
        if fn_size > out_fn_size:
            print(' .... reduced %s (%s) -> %s (%s) -- %.2f%%' % (fn, fn_size, out_fn, out_fn_size, 100.0 - ((out_fn_size / fn_size) * 100.0)))

            if not dry_run:
                shutil.copyfile(out_fn, fn)
        else:
            print(' .... failed to reduce %s, no significant gains could be made' % (fn))


if __name__ == "__main__":
    app = ImageOptApp()
    app.run()
