
import sys
import os
import glob
import shlex
from docutils.parsers.rst import Directive, directives 
from docutils import nodes, statemachine
import subprocess

# http://code.nabla.net/doc/docutils/api/docutils/docutils.nodes.html

class ExecDirective(Directive):
    """Execute the specified python code and insert the output into the document"""
    has_content = True

    option_spec = {
        'filename': directives.path,
        'args': directives.unchanged,
    }

    def run(self):
        executable = self.options.get('executable') or sys.executable
        fname = self.options.get('filename')
        args = shlex.split(self.options.get('args') or '')

        hide_src = self.options.get('hide_src')
        hide_output = self.options.get('hide_output')
        hide_error = self.options.get('hide_error')

        is_temp = not fname
        fname = fname or os.path.abspath('_tmp.py')
        try:
            if is_temp:
                with open(fname, 'w') as f:
                    f.write('\n'.join(self.content))

            r = subprocess.run([executable, fname] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = []
            if not hide_src:
                output.append(nodes.literal_block(text=open(fname).read()))
            if not hide_output:
                out = r.stdout.decode()
                if out:
                    output.extend([nodes.inline(text='Output:'), nodes.literal_block(text=out)])
            if not hide_error:
                if r.returncode:
                    output.extend([
                        nodes.inline(text='Error:'),
                        nodes.error(None, nodes.literal_block(text=r.stderr.decode()))
                    ])
            return output
        finally:
            if is_temp and os.path.isfile(fname):
                os.remove(fname)


class FileDirective(Directive):
    """Execute the specified python code and insert the output into the document"""
    has_content = True

    option_spec = {
        'filename': directives.path,
    }

    def run(self):
        outs = []
        for f in sorted(glob.glob(self.options.get('filename')))[:self.options.get('limit') or None]:
            outs.extend([nodes.literal(text=f), nodes.literal_block(text=open(f).read())])
        return outs


def setup(app):
    app.add_directive('exec-code', ExecDirective)
    app.add_directive('show-files', FileDirective)
